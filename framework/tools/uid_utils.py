from __future__ import annotations

import secrets
import time
from typing import Iterable


CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
UID_PATTERN_TEXT = r"^[0-9A-HJKMNP-TV-Z]{10}-[0-9A-HJKMNP-TV-Z]{4}$"


def encode_base32(value: int, length: int) -> str:
    chars: list[str] = []
    for _ in range(length):
        chars.append(CROCKFORD_BASE32[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def generate_uid(existing: Iterable[str] | None = None) -> str:
    existing_uids = set(existing or [])
    timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    prefix = encode_base32(timestamp_ms, 10)
    while True:
        random_part = "".join(secrets.choice(CROCKFORD_BASE32) for _ in range(4))
        uid = f"{prefix}-{random_part}"
        if uid not in existing_uids:
            return uid
