# crowdsky-client

A lightweight Python client for the [CrowdSky](https://crowdsky.univie.ac.at) data API —
discover and download crowd-sourced Seestar S50 stacked frames. Built as the shared contract
between CrowdSky, the scientists writing [CrowdSci](https://crowdsci.univie.ac.at) analysis
modules, and the CrowdSci runner on Zeus, so a pipeline behaves identically on a laptop and in
production.

Deliberately light: it depends only on `requests`, `astropy`, and `astropy-healpix` — **not** the
stacking engine (opencv/astroalign/sep).

📖 **Full documentation:** [crowdsky-client.readthedocs.io](https://crowdsky-client.readthedocs.io) —
including a downloadable [47 Tucanae example notebook](https://crowdsky-client.readthedocs.io/en/latest/use_case.html).

## Install

```bash
pip install crowdsky-client
```

## Authenticate

Mint a personal API key at **`https://crowdsky.univie.ac.at/account.php`** (log in → Account →
Create key). The secret is shown once — store it safely. Pass it directly or via the
`CROWDSKY_API_KEY` environment variable.

```python
from crowdsky_client import Client

c = Client(api_key="csk_…")                     # or: export CROWDSKY_API_KEY=csk_…; Client()
```

## Use

```python
# All frames imaging a target (cone-search over NSIDE=128 RING tiles, deduped by id):
frames = c.frames_for_target(159.6998, 53.5095, radius_deg=0.75, filter_name="IRCUT")

# Frames in a single HEALPix tile with server-side filters:
frames = c.frames_by_healpix(49152, start="2026-07-01T00:00:00Z", min_exptime=120)

# Download a stacked FITS by its unique id (bytes, or straight to disk):
fits_bytes = c.download_frame(frames[0]["id"])
c.download_frame_to(frames[0]["id"], "frame.fits")

# A frame's SEP + Gaia star table:
stars = c.star_data(frames[0]["id"])

# Public sky-coverage feed (no key needed) as an astropy Table:
coverage = c.sky_coverage()
```

Every data request sends `Authorization: Bearer <api_key>`; a revoked/expired/invalid key returns
HTTP 401, surfaced as `CrowdSkyError`.

## Develop / test

```bash
pip install -e ".[dev]"
pytest
```

Tests run fully offline via an injected fake session — no network, no key required.
