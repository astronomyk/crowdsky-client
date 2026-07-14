"""crowdsky-client — a lightweight Python client for the CrowdSky data API.

    from crowdsky_client import Client
    c = Client(api_key="csk_…")            # or set CROWDSKY_API_KEY
    frames = c.frames_for_target(159.6998, 53.5095)
    fits_bytes = c.download_frame(frames[0]["id"])
"""

from __future__ import annotations

from .client import Client, CrowdSkyClient, CrowdSkyError, HEALPIX_NSIDE, HEALPIX_ORDER

__version__ = "0.1.0"

__all__ = [
    "Client",
    "CrowdSkyClient",
    "CrowdSkyError",
    "HEALPIX_NSIDE",
    "HEALPIX_ORDER",
    "__version__",
]
