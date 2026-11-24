"""Derive runtime routing values from the single experiment seed."""

from __future__ import annotations

import hashlib

from app.seeding import derive_seed


PREFIX_LENGTH = 12
DOMAIN_STYLES = ("off", "hash", "pronounceable")
DOMAIN_TLD = "com"
CONSONANTS = "bcdfghjklmnpqrstvwxyz"
VOWELS = "aeiou"


def derive_route_prefix(seed: str) -> str:
    """Return the detector-blind route prefix for one experiment seed."""
    route_seed = derive_seed(seed, "route")
    return hashlib.sha256(route_seed.encode("utf-8")).hexdigest()[:PREFIX_LENGTH]


def derive_local_domain(seed: str, style: str) -> str | None:
    """Return the optional local-only hostname for one supported style."""
    if style not in DOMAIN_STYLES:
        raise ValueError(
            f"Unknown PHISHGATE_DOMAIN_STYLE: {style!r} "
            f"(use one of {', '.join(DOMAIN_STYLES)})"
        )
    if style == "hash":
        label = hashlib.sha256(f"{seed}:domain-hash".encode("utf-8")).hexdigest()[:12]
    elif style == "pronounceable":
        digest = hashlib.sha256(f"{seed}:domain-pronounceable".encode("utf-8")).digest()
        letters = []
        for index in range(9):
            pool = CONSONANTS if index % 2 == 0 else VOWELS
            letters.append(pool[digest[index] % len(pool)])
        label = "".join(letters)
    else:
        return None
    return f"{label}.{DOMAIN_TLD}"
