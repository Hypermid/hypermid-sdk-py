# hypermid

[![PyPI version](https://img.shields.io/pypi/v/hypermid.svg?color=00C2A8)](https://pypi.org/project/hypermid/)
[![PyPI downloads](https://img.shields.io/pypi/dm/hypermid.svg?color=00C2A8)](https://pypi.org/project/hypermid/)
[![Python versions](https://img.shields.io/pypi/pyversions/hypermid.svg)](https://pypi.org/project/hypermid/)
[![License](https://img.shields.io/pypi/l/hypermid.svg)](./LICENSE)

> **Cross-chain swap, bridge & fiat on-ramp in one SDK.** 90+ chains
> across EVM, Solana, Bitcoin, NEAR, Sui, Tron, TON, XRP and Doge.
> Multi-ecosystem wallet balances. Anonymous tier — no API key
> required to start.

```bash
pip install hypermid
```

```python
from hypermid import Hypermid

hm = Hypermid()                        # no key, no signup
chains = hm.get_chains()
print(len(chains.chains))              # → 89
```

Or async:

```python
import asyncio
from hypermid import AsyncHypermid

async def main():
    async with AsyncHypermid() as hm:
        chains = await hm.get_chains()
        print(len(chains.chains))

asyncio.run(main())
```

## Why Hypermid

- **One SDK, every ecosystem** — EVM + Solana + Bitcoin + NEAR + Sui +
  Tron + TON + XRP + Doge through a single client. No per-chain
  branching in your code.
- **Zero-setup integration** — anonymous tier works out of the box.
  Sign up only when you need partner fee splits or higher rate limits.
- **Routed across the best providers** — LI.FI, NEAR Intents and
  Hypermid SuperSwap (PulseChain native) routed automatically per
  pair, with USDC bridge fallback.
- **Built-in fiat on-ramp** — RampNow integration, same SDK.
- **Multi-chain balances** — `get_balances(address)` returns priced
  holdings + dust classification across every ecosystem the address
  touches.
- **Sync + async** — both APIs ship in the same package
  (`Hypermid`, `AsyncHypermid`). Type-checked with pydantic v2.

## Quick start — a swap end-to-end

```python
from hypermid import Hypermid

hm = Hypermid()

# 1. Quote
quote = hm.get_quote(
    from_chain=1,
    from_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC on Ethereum
    from_amount="1000000",                                     # 1 USDC (6 decimals)
    to_chain=8453,
    to_token="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",    # USDC on Base
    from_address="0xYourWallet",
    to_address="0xYourWallet",
)

# 2. Execute (returns the on-chain tx to sign + submit)
exe = hm.execute(
    from_chain=1,
    from_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    from_amount="1000000",
    to_chain=8453,
    to_token="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    from_address="0xYourWallet",
    to_address="0xYourWallet",
)

# 3. Status (once your wallet submits the tx)
status = hm.get_status(tx_hash="0x...", chain_id=1)
```

## Wallet balances across every ecosystem

```python
hm = Hypermid()
b = hm.get_balances("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
print(f"Total: ${b.total_balance_usd}")          # → Total: $25058.33
print(f"Chains with holdings: {len(b.balances)}") # → 61
```

## Webhook verification

```python
from hypermid import verify_webhook_signature

ok = verify_webhook_signature(
    payload=request.body,
    signature=request.headers["X-Hypermid-Signature"],
    timestamp=request.headers["X-Hypermid-Timestamp"],
    secret=os.environ["HYPERMID_WEBHOOK_SECRET"],
)
if not ok:
    return Response(status=401)
```

## Authentication

The API is open by default — every endpoint works without
authentication, so you can integrate, test, and ship without a signup.

An **API key is only needed if you're a partner** with negotiated terms
(custom fee splits, fee discounts, volume tiers, higher rate limits,
webhook events scoped to your traffic):

```python
from hypermid import Hypermid, HypermidConfig
import os

hm = Hypermid(HypermidConfig(api_key=os.environ["HYPERMID_API_KEY"]))
```

Apply for a partner account at [partner.hypermid.io](https://partner.hypermid.io).

## Documentation

Full reference: <https://docs.hypermid.io>

## License

MIT
