"""Hypermid sync + async clients.

Two clients with identical surface area:

- :class:`Hypermid` — blocking, uses :class:`httpx.Client`.
- :class:`AsyncHypermid` — coroutine-based, uses :class:`httpx.AsyncClient`.

Both accept the same :class:`HypermidConfig`. The async client supports
the context-manager protocol so connection pools are cleaned up::

    async with AsyncHypermid() as hm:
        chains = await hm.get_chains()
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from .config import HypermidConfig
from .errors import (
    HypermidError,
    HypermidNetworkError,
    HypermidTimeoutError,
)
from .types import (
    BalancesResponse,
    ChainsResponse,
    CreateWebhookResponse,
    DepositStatusResponse,
    ExecuteResponse,
    InboundReceiverResponse,
    OnrampCheckoutResponse,
    OnrampQuoteResponse,
    OnrampStatusResponse,
    QuoteResponse,
    StatusResponse,
    TokensResponse,
)

T = TypeVar("T", bound=BaseModel)

_USER_AGENT = "hypermid-py/1.0.0"


def _build_query(params: Optional[Mapping[str, Any]]) -> str:
    """Render a query string, skipping ``None`` values and joining list
    values with commas (matches the API's CSV-style array params).
    """
    if not params:
        return ""
    parts: List[tuple[str, str]] = []
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            parts.append((k, ",".join(str(x) for x in v)))
        elif isinstance(v, bool):
            parts.append((k, "true" if v else "false"))
        else:
            parts.append((k, str(v)))
    return "?" + urlencode(parts) if parts else ""


def _parse_envelope(
    status: int,
    body_bytes: bytes,
    response_type: Type[T],
) -> T:
    """Parse the standard Hypermid ``{data, error, meta}`` envelope and
    return the typed inner data (or raise :class:`HypermidError`).
    """
    import json

    try:
        body = json.loads(body_bytes)
    except json.JSONDecodeError as exc:
        raise HypermidNetworkError(
            f"Invalid JSON response (HTTP {status})", cause=exc
        ) from exc

    err = body.get("error")
    if err is not None:
        meta = body.get("meta") or {}
        raise HypermidError(
            code=err.get("code", "UNKNOWN"),
            message=err.get("message", "Unknown error"),
            status=status,
            details=err.get("details"),
            request_id=meta.get("requestId"),
        )

    data = body.get("data")
    if data is None:
        raise HypermidNetworkError(
            f"Response missing data field (HTTP {status})"
        )

    return response_type.model_validate(data)


class _BaseClient:
    """Shared header + URL construction for sync and async clients."""

    def __init__(self, config: Optional[HypermidConfig] = None) -> None:
        self._config = config or HypermidConfig()
        self._base_url = self._config.base_url.rstrip("/")

    def _headers(self, extra: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
        h: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        }
        if self._config.api_key:
            h["X-API-Key"] = self._config.api_key
        if extra:
            h.update(extra)
        return h

    def _url(self, path: str, query: Optional[Mapping[str, Any]] = None) -> str:
        return f"{self._base_url}/v1{path}{_build_query(query)}"


# ─── Sync client ─────────────────────────────────────────────────────────


class Hypermid(_BaseClient):
    """Synchronous Hypermid Partner API client.

    Example::

        from hypermid import Hypermid

        hm = Hypermid()                       # anonymous, no signup
        chains = hm.get_chains()
        print(len(chains.chains))             # → 89
    """

    def __init__(self, config: Optional[HypermidConfig] = None) -> None:
        super().__init__(config)
        self._client = httpx.Client(timeout=self._config.timeout)

    def __enter__(self) -> "Hypermid":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # ─── HTTP primitive ─────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        json_body: Optional[Any] = None,
        response_type: Type[T],
    ) -> T:
        url = self._url(path, query)
        try:
            res = self._client.request(
                method,
                url,
                headers=self._headers(),
                json=json_body,
            )
        except httpx.TimeoutException as exc:
            raise HypermidTimeoutError(self._config.timeout) from exc
        except httpx.HTTPError as exc:
            raise HypermidNetworkError(f"Request failed: {exc}", cause=exc) from exc
        return _parse_envelope(res.status_code, res.content, response_type)

    # ─── Chains / Tokens ────────────────────────────────────────────

    def get_chains(self) -> ChainsResponse:
        """Return every chain the routing layer currently supports."""
        return self._request("GET", "/chains", response_type=ChainsResponse)

    def get_tokens(
        self,
        chains: Optional[str] = None,
        keywords: Optional[str] = None,
    ) -> TokensResponse:
        """Return the token registry, optionally filtered by chain / keyword."""
        return self._request(
            "GET",
            "/tokens",
            query={"chains": chains, "keywords": keywords},
            response_type=TokensResponse,
        )

    # ─── Quote / Execute / Status ───────────────────────────────────

    def get_quote(
        self,
        *,
        from_chain: int | str,
        from_token: str,
        from_amount: str,
        to_chain: int | str,
        to_token: str,
        from_address: str,
        to_address: Optional[str] = None,
        slippage: Optional[float | str] = None,
        order: Optional[str] = None,
    ) -> QuoteResponse:
        """Get a dry quote for a swap. No signature required."""
        return self._request(
            "GET",
            "/quote",
            query={
                "fromChain": from_chain,
                "fromToken": from_token,
                "fromAmount": from_amount,
                "toChain": to_chain,
                "toToken": to_token,
                "fromAddress": from_address,
                "toAddress": to_address,
                "slippage": slippage,
                "order": order,
            },
            response_type=QuoteResponse,
        )

    def execute(
        self,
        *,
        from_chain: int | str,
        from_token: str,
        from_amount: str,
        to_chain: int | str,
        to_token: str,
        from_address: str,
        to_address: str,
        deposit_mode: Optional[str] = None,
        slippage: Optional[float | str] = None,
        order: Optional[str] = None,
        refund_address: Optional[str] = None,
    ) -> ExecuteResponse:
        """Get an executable response — a tx to sign (EVM) or a deposit
        address (NEAR Intents / Bitcoin / etc.). User signs and submits
        on-chain.
        """
        return self._request(
            "POST",
            "/execute",
            json_body={
                "fromChain": from_chain,
                "fromToken": from_token,
                "fromAmount": from_amount,
                "toChain": to_chain,
                "toToken": to_token,
                "fromAddress": from_address,
                "toAddress": to_address,
                "depositMode": deposit_mode,
                "slippage": slippage,
                "order": order,
                "refundAddress": refund_address,
            },
            response_type=ExecuteResponse,
        )

    def get_status(
        self,
        *,
        tx_hash: Optional[str] = None,
        chain_id: Optional[int | str] = None,
        bridge: Optional[str] = None,
        from_chain: Optional[int | str] = None,
        to_chain: Optional[int | str] = None,
        provider: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> StatusResponse:
        """Universal status lookup. Pass ``tx_hash`` for LI.FI /
        SuperSwap, or ``provider='near-intents'`` + ``correlation_id``
        for NEAR Intents flows.
        """
        return self._request(
            "GET",
            "/status",
            query={
                "txHash": tx_hash,
                "chainId": chain_id,
                "bridge": bridge,
                "fromChain": from_chain,
                "toChain": to_chain,
                "provider": provider,
                "correlationId": correlation_id,
            },
            response_type=StatusResponse,
        )

    def get_deposit_status(
        self,
        *,
        deposit_address: str,
        deposit_memo: Optional[str] = None,
    ) -> DepositStatusResponse:
        """NEAR Intents deposit status by deposit address."""
        return self._request(
            "GET",
            "/execute/deposit/status",
            query={
                "depositAddress": deposit_address,
                "depositMemo": deposit_memo,
            },
            response_type=DepositStatusResponse,
        )

    # ─── Balances ───────────────────────────────────────────────────

    def get_balances(
        self,
        address: str,
        chain_ids: Optional[List[int]] = None,
    ) -> BalancesResponse:
        """Multi-ecosystem token balances + USD total for an address.

        The backend auto-detects the address ecosystem
        (EVM / Solana / Bitcoin / NEAR / Sui / Tron). Pass ``chain_ids``
        to restrict EVM coverage to specific chains.
        """
        return self._request(
            "GET",
            "/balances",
            query={"address": address, "chainIds": chain_ids},
            response_type=BalancesResponse,
        )

    # ─── Webhooks ───────────────────────────────────────────────────

    def create_webhook(
        self,
        *,
        url: str,
        events: List[str],
    ) -> CreateWebhookResponse:
        """Register a webhook endpoint. Returns the signing secret
        once — store it server-side and use
        :func:`hypermid.verify_webhook_signature` to verify deliveries.
        """
        return self._request(
            "POST",
            "/partner/me/webhooks",
            json_body={"url": url, "events": events},
            response_type=CreateWebhookResponse,
        )

    # ─── Inbound receiver (SuperSwap V2) ────────────────────────────

    def register_inbound_receiver(
        self,
        *,
        tx_hash: str,
        from_address: str,
        to_address: str,
        output_token: str,
        destination_domain: int,
        signature: str,
    ) -> InboundReceiverResponse:
        """Register a SuperSwap V2 inbound deposit so the backend
        executes the PulseChain-side output. The deposit must already
        be on-chain; an EIP-712 signature is required.
        """
        return self._request(
            "POST",
            "/inbound-receiver/register",
            json_body={
                "txHash": tx_hash,
                "fromAddress": from_address,
                "toAddress": to_address,
                "outputToken": output_token,
                "destinationDomain": destination_domain,
                "signature": signature,
            },
            response_type=InboundReceiverResponse,
        )

    # ─── On-ramp ────────────────────────────────────────────────────

    def get_onramp_quote(self, **params: Any) -> OnrampQuoteResponse:
        """Fiat-on-ramp quote (RampNow integration)."""
        return self._request(
            "GET", "/onramp/quote", query=params, response_type=OnrampQuoteResponse
        )

    def get_onramp_checkout(self, **params: Any) -> OnrampCheckoutResponse:
        """Create an on-ramp checkout session and return the URL."""
        return self._request(
            "POST",
            "/onramp/checkout",
            json_body=params,
            response_type=OnrampCheckoutResponse,
        )

    def get_onramp_status(self, order_id: str) -> OnrampStatusResponse:
        """Look up on-ramp order status by order ID."""
        return self._request(
            "GET",
            "/onramp/status",
            query={"orderId": order_id},
            response_type=OnrampStatusResponse,
        )


# ─── Async client ────────────────────────────────────────────────────────


class AsyncHypermid(_BaseClient):
    """Asynchronous Hypermid Partner API client.

    Same surface as :class:`Hypermid` but every method is a coroutine.
    Use as an async context manager so the connection pool is cleaned
    up::

        from hypermid import AsyncHypermid

        async def main():
            async with AsyncHypermid() as hm:
                chains = await hm.get_chains()
    """

    def __init__(self, config: Optional[HypermidConfig] = None) -> None:
        super().__init__(config)
        self._client = httpx.AsyncClient(timeout=self._config.timeout)

    async def __aenter__(self) -> "AsyncHypermid":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        json_body: Optional[Any] = None,
        response_type: Type[T],
    ) -> T:
        url = self._url(path, query)
        try:
            res = await self._client.request(
                method,
                url,
                headers=self._headers(),
                json=json_body,
            )
        except httpx.TimeoutException as exc:
            raise HypermidTimeoutError(self._config.timeout) from exc
        except httpx.HTTPError as exc:
            raise HypermidNetworkError(f"Request failed: {exc}", cause=exc) from exc
        return _parse_envelope(res.status_code, res.content, response_type)

    # ─── Method surface (mirrors the sync client) ───────────────────

    async def get_chains(self) -> ChainsResponse:
        return await self._request("GET", "/chains", response_type=ChainsResponse)

    async def get_tokens(
        self,
        chains: Optional[str] = None,
        keywords: Optional[str] = None,
    ) -> TokensResponse:
        return await self._request(
            "GET",
            "/tokens",
            query={"chains": chains, "keywords": keywords},
            response_type=TokensResponse,
        )

    async def get_quote(
        self,
        *,
        from_chain: int | str,
        from_token: str,
        from_amount: str,
        to_chain: int | str,
        to_token: str,
        from_address: str,
        to_address: Optional[str] = None,
        slippage: Optional[float | str] = None,
        order: Optional[str] = None,
    ) -> QuoteResponse:
        return await self._request(
            "GET",
            "/quote",
            query={
                "fromChain": from_chain,
                "fromToken": from_token,
                "fromAmount": from_amount,
                "toChain": to_chain,
                "toToken": to_token,
                "fromAddress": from_address,
                "toAddress": to_address,
                "slippage": slippage,
                "order": order,
            },
            response_type=QuoteResponse,
        )

    async def execute(
        self,
        *,
        from_chain: int | str,
        from_token: str,
        from_amount: str,
        to_chain: int | str,
        to_token: str,
        from_address: str,
        to_address: str,
        deposit_mode: Optional[str] = None,
        slippage: Optional[float | str] = None,
        order: Optional[str] = None,
        refund_address: Optional[str] = None,
    ) -> ExecuteResponse:
        return await self._request(
            "POST",
            "/execute",
            json_body={
                "fromChain": from_chain,
                "fromToken": from_token,
                "fromAmount": from_amount,
                "toChain": to_chain,
                "toToken": to_token,
                "fromAddress": from_address,
                "toAddress": to_address,
                "depositMode": deposit_mode,
                "slippage": slippage,
                "order": order,
                "refundAddress": refund_address,
            },
            response_type=ExecuteResponse,
        )

    async def get_status(
        self,
        *,
        tx_hash: Optional[str] = None,
        chain_id: Optional[int | str] = None,
        bridge: Optional[str] = None,
        from_chain: Optional[int | str] = None,
        to_chain: Optional[int | str] = None,
        provider: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> StatusResponse:
        return await self._request(
            "GET",
            "/status",
            query={
                "txHash": tx_hash,
                "chainId": chain_id,
                "bridge": bridge,
                "fromChain": from_chain,
                "toChain": to_chain,
                "provider": provider,
                "correlationId": correlation_id,
            },
            response_type=StatusResponse,
        )

    async def get_deposit_status(
        self,
        *,
        deposit_address: str,
        deposit_memo: Optional[str] = None,
    ) -> DepositStatusResponse:
        return await self._request(
            "GET",
            "/execute/deposit/status",
            query={
                "depositAddress": deposit_address,
                "depositMemo": deposit_memo,
            },
            response_type=DepositStatusResponse,
        )

    async def get_balances(
        self,
        address: str,
        chain_ids: Optional[List[int]] = None,
    ) -> BalancesResponse:
        return await self._request(
            "GET",
            "/balances",
            query={"address": address, "chainIds": chain_ids},
            response_type=BalancesResponse,
        )

    async def create_webhook(
        self,
        *,
        url: str,
        events: List[str],
    ) -> CreateWebhookResponse:
        return await self._request(
            "POST",
            "/partner/me/webhooks",
            json_body={"url": url, "events": events},
            response_type=CreateWebhookResponse,
        )

    async def register_inbound_receiver(
        self,
        *,
        tx_hash: str,
        from_address: str,
        to_address: str,
        output_token: str,
        destination_domain: int,
        signature: str,
    ) -> InboundReceiverResponse:
        return await self._request(
            "POST",
            "/inbound-receiver/register",
            json_body={
                "txHash": tx_hash,
                "fromAddress": from_address,
                "toAddress": to_address,
                "outputToken": output_token,
                "destinationDomain": destination_domain,
                "signature": signature,
            },
            response_type=InboundReceiverResponse,
        )

    async def get_onramp_quote(self, **params: Any) -> OnrampQuoteResponse:
        return await self._request(
            "GET", "/onramp/quote", query=params, response_type=OnrampQuoteResponse
        )

    async def get_onramp_checkout(self, **params: Any) -> OnrampCheckoutResponse:
        return await self._request(
            "POST",
            "/onramp/checkout",
            json_body=params,
            response_type=OnrampCheckoutResponse,
        )

    async def get_onramp_status(self, order_id: str) -> OnrampStatusResponse:
        return await self._request(
            "GET",
            "/onramp/status",
            query={"orderId": order_id},
            response_type=OnrampStatusResponse,
        )
