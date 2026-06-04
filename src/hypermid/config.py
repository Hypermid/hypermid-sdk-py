"""Hypermid client configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

DEFAULT_BASE_URL = "https://api.hypermid.io"
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass
class HypermidConfig:
    """Configuration for the Hypermid client.

    All fields are optional. The default config talks to the production
    Hypermid API at the anonymous tier (no signup required).

    Attributes:
        api_key: Partner API key. **Optional** — the API works fully
            without a key. Set this only if you're a partner with
            negotiated fee terms (custom splits, discounts, higher
            rate limits). Sent as ``X-API-Key`` header.
        base_url: Override the API base URL (default:
            ``https://api.hypermid.io``).
        timeout: Per-request timeout in seconds (default: 30.0).
    """

    api_key: Optional[str] = None
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT_SECONDS
