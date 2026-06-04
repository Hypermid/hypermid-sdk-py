"""Hypermid Partner API SDK for Python.

Cross-chain swap, bridge & fiat on-ramp across 90+ chains
(EVM, Solana, Bitcoin, NEAR, Sui, Tron, TON, XRP, Doge).

Quick start (no API key required)::

    from hypermid import Hypermid

    hm = Hypermid()
    chains = hm.get_chains()
    print(f"Supported chains: {len(chains.chains)}")

Or async::

    from hypermid import AsyncHypermid

    async def main():
        async with AsyncHypermid() as hm:
            chains = await hm.get_chains()
"""

from .client import Hypermid, AsyncHypermid
from .config import HypermidConfig
from .errors import (
    HypermidError,
    HypermidTimeoutError,
    HypermidNetworkError,
    HypermidPollTimeoutError,
)
from .webhook import verify_webhook_signature
from . import types

__version__ = "1.0.0"

__all__ = [
    "Hypermid",
    "AsyncHypermid",
    "HypermidConfig",
    "HypermidError",
    "HypermidTimeoutError",
    "HypermidNetworkError",
    "HypermidPollTimeoutError",
    "verify_webhook_signature",
    "types",
    "__version__",
]
