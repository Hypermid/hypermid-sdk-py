"""Webhook signature verification.

When Hypermid sends a webhook it includes two headers:

- ``X-Hypermid-Signature`` — ``sha256=<hex>`` HMAC of the raw body.
- ``X-Hypermid-Timestamp`` — Unix seconds when the payload was signed.

The signed payload is ``f"{timestamp}.{raw_body}"`` to prevent replay
attacks. Verify with :func:`verify_webhook_signature`.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Union


_TOLERANCE_SECONDS = 5 * 60  # 5 minutes


def verify_webhook_signature(
    *,
    payload: Union[str, bytes],
    signature: str,
    timestamp: Union[str, int],
    secret: str,
    tolerance_seconds: int = _TOLERANCE_SECONDS,
) -> bool:
    """Return ``True`` iff the signature is valid AND fresh.

    Args:
        payload: Raw request body (string or bytes).
        signature: Value of the ``X-Hypermid-Signature`` header.
        timestamp: Value of the ``X-Hypermid-Timestamp`` header.
        secret: Webhook signing secret returned at registration time.
        tolerance_seconds: Reject signatures older than this many
            seconds (default: 300, i.e. 5 minutes). Set lower for
            stricter replay protection.

    Returns:
        ``True`` if the HMAC matches and the timestamp is within
        tolerance, ``False`` otherwise.
    """
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False

    # Reject stale / future timestamps.
    if abs(time.time() - ts) > tolerance_seconds:
        return False

    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload

    signed = f"{ts}.".encode("utf-8") + payload_bytes
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()

    # Accept both bare hex and "sha256=<hex>" prefix.
    provided = signature.removeprefix("sha256=").strip()

    return hmac.compare_digest(expected, provided)
