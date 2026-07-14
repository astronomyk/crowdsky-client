"""A thin HTTP client for pulling raw Seestar data from CrowdSky.

This is the shared contract between CrowdSky, the scientists writing CrowdSci
analysis modules, and the CrowdSci Zeus runner — all three code against these
method names/signatures, so keep them stable (propose changes explicitly rather
than silently diverging).

Auth is a personal API key minted at ``<base_url>/account.php`` (or the shared
CROWDSCI service key), sent as ``Authorization: Bearer <key>`` on every data
request. A personal key reads across the whole pooled archive.

Endpoints wrapped (see CrowdSky ``docs/api-reference.md``):

- ``frames_by_healpix.php`` — frames covering one HEALPix RING NSIDE=128 tile,
  server-side filtered (:meth:`Client.frames_by_healpix`), plus the
  coordinate-driven convenience :meth:`Client.frames_for_target`.
- ``download_frame.php?id=…`` — a stacked FITS by its unique numeric id
  (:meth:`Client.download_frame` / :meth:`Client.download_frame_to`).
- ``frame_stars.php?id=…`` — a frame's SEP + Gaia star table
  (:meth:`Client.star_data`).
- ``sky_coverage.php`` — the public Norder-7 coverage feed as an astropy Table
  (:meth:`Client.sky_coverage`).

Network access is isolated here and the ``session`` is injectable, so modules and
the runner stay unit-testable offline.
"""

from __future__ import annotations

from typing import Any

from . import config

# HEALPix scheme shared with CrowdSky's sky_coverage / chunk_key tiling:
# RING ordering at NSIDE=128 (pixel ~27.5', finer than the Seestar FOV).
HEALPIX_NSIDE = 128
HEALPIX_ORDER = "ring"

__all__ = ["Client", "CrowdSkyClient", "CrowdSkyError", "HEALPIX_NSIDE", "HEALPIX_ORDER"]


class CrowdSkyError(RuntimeError):
    """Raised when a CrowdSky request fails."""


class Client:
    """Client for the CrowdSky data API.

    :param api_key: Personal API key (Bearer). Falls back to ``$CROWDSKY_API_KEY``.
    :param base_url: CrowdSky base URL. Falls back to ``$CROWDSKY_API_URL`` then the
        production default ``https://crowdsky.univie.ac.at``.
    :param session: An injectable ``requests.Session``-like object (for tests).
    :param timeout: Per-request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        session: Any = None,
        timeout: int = 120,
    ) -> None:
        api_key = api_key or config.get(config.API_KEY_ENV)
        base_url = base_url or config.get(config.BASE_URL_ENV) or config.DEFAULT_BASE_URL

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        if session is None:
            import requests  # imported lazily so the module imports without requests

            session = requests.Session()
        self.session = session

    def _get(
        self,
        path: str,
        *,
        bearer: bool = False,
        stream: bool = False,
        **params: Any,
    ):
        # Drop params the caller left as None so we only send what was set.
        params = {k: v for k, v in params.items() if v is not None}
        kwargs: dict[str, Any] = {"params": params, "timeout": self.timeout, "stream": stream}
        if bearer:
            if not self.api_key:
                raise CrowdSkyError(
                    f"CrowdSky GET {path} needs a Bearer key (set CROWDSKY_API_KEY)."
                )
            kwargs["headers"] = {"Authorization": f"Bearer {self.api_key}"}
        resp = self.session.get(f"{self.base_url}/api/{path}", **kwargs)
        if getattr(resp, "status_code", 200) != 200:
            raise CrowdSkyError(f"CrowdSky GET {path} -> HTTP {resp.status_code}")
        return resp

    # --- Discovery -----------------------------------------------------------

    def frames_by_healpix(
        self,
        healpix: int,
        *,
        start: str | None = None,
        end: str | None = None,
        filter_name: str | None = None,
        eq_mode: int | None = None,
        min_sqm: float | None = None,
        min_exptime: float | None = None,
    ) -> list[dict[str, Any]]:
        """Frames covering one RING NSIDE=128 tile, with server-side filters.

        ``filter_name`` maps to the endpoint's ``filter`` query param (avoids
        shadowing the Python builtin). Returns the JSON array (empty when nothing
        matches).
        """
        resp = self._get(
            "frames_by_healpix.php",
            bearer=True,
            healpix=healpix,
            start=start,
            end=end,
            filter=filter_name,
            eq_mode=eq_mode,
            min_sqm=min_sqm,
            min_exptime=min_exptime,
        )
        data = resp.json()
        return data if isinstance(data, list) else []

    def frames_for_target(
        self,
        ra_deg: float,
        dec_deg: float,
        radius_deg: float = 0.75,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """All frames imaging a sky position, deduped by unique ``id``.

        A single NSIDE=128 tile (~27.5') is smaller than the Seestar FOV, so frames
        imaging the target may have their pointing centre in a neighbouring tile. We
        cone-search the covering RING pixels (radius ~ the FOV) and union
        :meth:`frames_by_healpix` over them. ``**filters`` are passed through
        (``start`` / ``end`` / ``filter_name`` / ...). Returns rows sorted by
        ``date_obs_start``.
        """
        import astropy.units as u
        from astropy_healpix import HEALPix

        hp = HEALPix(nside=HEALPIX_NSIDE, order=HEALPIX_ORDER)
        pixels = hp.cone_search_lonlat(ra_deg * u.deg, dec_deg * u.deg, radius_deg * u.deg)

        by_id: dict[Any, dict[str, Any]] = {}
        for pix in pixels:
            for row in self.frames_by_healpix(int(pix), **filters):
                by_id[row.get("id", id(row))] = row
        return sorted(by_id.values(), key=lambda r: str(r.get("date_obs_start", "")))

    # --- Data ----------------------------------------------------------------

    def download_frame(self, frame_id: int | str) -> bytes:
        """Download one stacked FITS file (bytes) by its unique ``stacked_frames.id``."""
        resp = self._get("download_frame.php", bearer=True, stream=True, id=frame_id)
        return resp.content

    def download_frame_to(self, frame_id: int | str, path: Any) -> Any:
        """Stream one stacked FITS file to ``path`` on disk; returns the Path.

        Streams in chunks (like the worker's downloader) so large files never fully
        buffer in memory. Falls back to ``resp.content`` for sessions without
        ``iter_content`` (e.g. test fakes).
        """
        from pathlib import Path

        resp = self._get("download_frame.php", bearer=True, stream=True, id=frame_id)
        p = Path(path)
        if p.parent and not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as fh:
            if hasattr(resp, "iter_content"):
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        fh.write(chunk)
            else:
                fh.write(resp.content)
        return p

    def star_data(self, frame_id: int | str) -> dict[str, Any]:
        """Return a frame's star table (SEP detections + Gaia cross-match) as JSON.

        Note: these are *detected sources*, not forced photometry — a pipeline
        measuring a transient at a known position still needs the pixels
        (:meth:`download_frame`).
        """
        return self._get("frame_stars.php", bearer=True, id=frame_id).json()

    # --- Convenience ---------------------------------------------------------

    def sky_coverage(self):
        """Return the public Norder-7 sky-coverage feed as an ``astropy.table.Table``.

        Public (no key required). One row per (HEALPix RING tile, filter) with
        cumulative exposure and last-observed time.
        """
        from astropy.io import ascii as _ascii

        resp = self._get("sky_coverage.php")
        text = resp.text if hasattr(resp, "text") else resp.content.decode("utf-8")
        return _ascii.read(text, format="ecsv")


# Back-compat alias: the code lifted from CrowdSci referred to CrowdSkyClient.
CrowdSkyClient = Client
