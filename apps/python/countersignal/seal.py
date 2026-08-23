"""Content-addressed integrity seal for CounterSignal audit packets.

This detects packet mutation after export. It is not an identity signature and
not an external timestamp or tamper-proof anchor: anyone who can rewrite the
packet can also compute a new digest. The product surfaces that limitation
explicitly instead of overstating what a SHA-256 digest proves.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

SEAL_VERSION = "countersignal.content-seal.v1"


def _payload(packet: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in packet.items() if key != "integrity_seal"}


def canonical_bytes(packet: dict[str, Any]) -> bytes:
    return json.dumps(
        _payload(packet), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def digest(packet: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(packet)).hexdigest()


def seal_packet(packet: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(_payload(packet))
    sealed["integrity_seal"] = {
        "schema": SEAL_VERSION,
        "algorithm": "sha256",
        "digest": digest(sealed),
        "scope": "canonical JSON packet excluding integrity_seal",
        "proves": "exported packet content has not changed since this digest was computed",
        "does_not_prove": "author identity, external timestamp, or tamper-proof storage",
    }
    return sealed


def verify_packet(packet: dict[str, Any]) -> bool:
    seal = packet.get("integrity_seal")
    if not isinstance(seal, dict):
        return False
    if seal.get("schema") != SEAL_VERSION or seal.get("algorithm") != "sha256":
        return False
    observed = seal.get("digest")
    return isinstance(observed, str) and observed == digest(packet)
