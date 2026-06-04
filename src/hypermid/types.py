"""Hypermid Partner API request/response types.

All types are :mod:`pydantic` v2 models that validate at the response
boundary. They allow extra fields (``model_config = ConfigDict(extra="allow")``)
so the SDK doesn't break when the API adds new fields.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# ─── Base config — allow extra fields so a new API field never breaks consumers ─

class _Base(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ─── API envelope ────────────────────────────────────────────────────────

class RateLimitInfo(_Base):
    limit: int
    remaining: int
    reset: int


class ApiMeta(_Base):
    request_id: str = Field(..., alias="requestId")
    timestamp: int
    rate_limit: Optional[RateLimitInfo] = Field(None, alias="rateLimit")


# ─── Chains ──────────────────────────────────────────────────────────────

class NativeToken(_Base):
    symbol: str
    name: str
    decimals: int


class Chain(_Base):
    id: int
    key: str
    name: str
    chain_type: str = Field(..., alias="chainType")
    native_token: NativeToken = Field(..., alias="nativeToken")
    slug: Optional[str] = None
    providers: Optional[List[str]] = None
    provider: Optional[str] = None


class ChainsResponse(_Base):
    chains: List[Chain]


# ─── Tokens ──────────────────────────────────────────────────────────────

class Token(_Base):
    address: str
    symbol: str
    name: str
    decimals: int
    chain_id: int = Field(..., alias="chainId")
    logo_uri: Optional[str] = Field(None, alias="logoURI")
    price_usd: Optional[str] = Field(None, alias="priceUSD")


class TokensResponse(_Base):
    tokens: Dict[str, List[Token]]


# ─── Quote ───────────────────────────────────────────────────────────────

class QuoteResponse(_Base):
    quote: Any
    provider: Literal["lifi", "near-intents", "superswap"]
    fee_bps: int = Field(..., alias="feeBps")
    is_dry_quote: bool = Field(..., alias="isDryQuote")


# ─── Status ──────────────────────────────────────────────────────────────

class StatusResponse(_Base):
    provider: Literal["lifi", "near-intents", "superswap"]
    status: Optional[str] = None


# ─── Execute ─────────────────────────────────────────────────────────────

class TransactionRequest(_Base):
    to: str
    data: str
    value: str
    from_: str = Field(..., alias="from")
    chain_id: int = Field(..., alias="chainId")
    gas_limit: Optional[str] = Field(None, alias="gasLimit")
    gas_price: Optional[str] = Field(None, alias="gasPrice")


class ExecuteResponse(_Base):
    """Polymorphic execute response (LI.FI / NEAR Intents / SuperSwap).

    Use the ``provider`` field to discriminate. Common fields below;
    provider-specific fields are accessible via attribute access (extra
    fields are allowed).
    """

    provider: Literal["lifi", "near-intents", "superswap"]
    deposit_mode: str = Field(..., alias="depositMode")
    fee_bps: int = Field(..., alias="feeBps")


# ─── Deposit (NEAR Intents) ──────────────────────────────────────────────

class DepositStatusResponse(_Base):
    provider: Literal["near-intents"]
    status: str
    deposit_address: str = Field(..., alias="depositAddress")


# ─── Balances ────────────────────────────────────────────────────────────

BalanceTier = Literal["priced", "untracked", "dust"]


class TokenBalance(_Base):
    chain_id: int = Field(..., alias="chainId")
    address: str
    symbol: str
    name: str
    decimals: int
    balance: str
    price_usd: float = Field(0.0, alias="priceUSD")
    balance_usd: float = Field(0.0, alias="balanceUSD")
    logo_uri: str = Field("", alias="logoURI")
    providers: List[str] = Field(default_factory=list)
    tier: Optional[BalanceTier] = None


class BalanceChainMeta(_Base):
    ok: bool
    error: Optional[str] = None
    source: Optional[str] = None
    duration_ms: int = Field(..., alias="durationMs")
    stale: Optional[bool] = None


class BalancesResponse(_Base):
    address: str
    total_balance_usd: str = Field(..., alias="totalBalanceUSD")
    balances: Dict[str, List[TokenBalance]]
    chain_meta: Optional[Dict[str, BalanceChainMeta]] = Field(None, alias="chainMeta")
    cached_at: Optional[str] = Field(None, alias="cachedAt")
    cache_hit: Optional[bool] = Field(None, alias="cacheHit")


# ─── Webhooks ────────────────────────────────────────────────────────────

class CreateWebhookResponse(_Base):
    id: str
    url: str
    secret: str
    events: List[str]
    created_at: str = Field(..., alias="createdAt")


# ─── Inbound receiver (SuperSwap V2) ─────────────────────────────────────

class InboundReceiverResponse(_Base):
    registered: bool
    record_id: str = Field(..., alias="recordId")
    usdc_amount: str = Field(..., alias="usdcAmount")
    status: str


# ─── On-ramp ─────────────────────────────────────────────────────────────

class OnrampQuoteResponse(_Base):
    provider: str
    fiat_amount: str = Field(..., alias="fiatAmount")
    fiat_currency: str = Field(..., alias="fiatCurrency")
    crypto_amount: str = Field(..., alias="cryptoAmount")
    crypto_token: str = Field(..., alias="cryptoToken")
    fee_usd: Optional[float] = Field(None, alias="feeUsd")


class OnrampCheckoutResponse(_Base):
    checkout_url: str = Field(..., alias="checkoutUrl")
    order_id: str = Field(..., alias="orderId")


class OnrampStatusResponse(_Base):
    status: str
    order_id: str = Field(..., alias="orderId")
    tx_hash: Optional[str] = Field(None, alias="txHash")
