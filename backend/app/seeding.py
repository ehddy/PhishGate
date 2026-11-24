"""Derive reproducible, purpose-specific values from one experiment seed."""

from __future__ import annotations

import hashlib
import hmac
import os


MASTER_SEED_ENV = "PHISHGATE_SEED"


def master_seed() -> str:
    """Return the one operator-supplied experiment seed."""
    seed = os.environ.get(MASTER_SEED_ENV, "").strip()
    if not seed:
        raise RuntimeError(f"{MASTER_SEED_ENV} must be set to a non-empty private value.")
    return seed


def derive_seed(seed: str, purpose: str) -> str:
    """Return a domain-separated deterministic seed for ``purpose``."""
    if not seed:
        raise ValueError("A non-empty experiment seed is required.")
    if not purpose:
        raise ValueError("A non-empty seed purpose is required.")
    return hmac.new(seed.encode("utf-8"), purpose.encode("utf-8"), hashlib.sha256).hexdigest()


def purpose_seed(purpose: str) -> str:
    """Derive one purpose-specific seed from ``PHISHGATE_SEED``."""
    return derive_seed(master_seed(), purpose)
