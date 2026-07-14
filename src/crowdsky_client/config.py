"""Environment configuration for the CrowdSky client.

Real values come from environment variables (or a ``.env`` if ``python-dotenv``
happens to be installed — it is NOT a hard dependency of this package).
"""

from __future__ import annotations

import os

# Production CrowdSky instance; overridable via CROWDSKY_API_URL or the base_url arg.
DEFAULT_BASE_URL = "https://crowdsky.univie.ac.at"

API_KEY_ENV = "CROWDSKY_API_KEY"
BASE_URL_ENV = "CROWDSKY_API_URL"

# Optionally load a .env sitting in the working dir, if python-dotenv is present.
try:  # pragma: no cover - convenience only
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


def get(name: str, default: str | None = None, *, required: bool = False) -> str | None:
    val = os.environ.get(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Required environment variable '{name}' is not set.")
    return val
