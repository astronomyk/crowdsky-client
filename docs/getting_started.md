# Getting started

## Install

```bash
pip install crowdsky-client
```

Pulls only `requests`, `astropy`, and `astropy-healpix`. Requires Python ≥ 3.11.

## Get an API key

Programmatic access uses a **personal API key**, minted from your CrowdSky account:

1. Log in at [https://crowdsky.univie.ac.at](https://crowdsky.univie.ac.at).
2. Open **Account** in the top navigation.
3. Under *Create a new key*, give it a name (e.g. `laptop` or `zeus-runner`), optionally set an
   expiry, and click **Create key**.
4. Copy the secret (`csk_…`) **immediately** — it is stored only as a hash and is never shown
   again. If you lose it, revoke it and mint a new one.

A key reads across the **whole pooled archive** (every contributor's frames), which is the point
of the shared citizen-science dataset. You can hold several named keys and revoke any of them at
any time from the same page.

## Authenticate the client

Pass the key explicitly:

```python
from crowdsky_client import Client

c = Client(api_key="csk_1a2b3c4d…")
```

…or, preferred, set it in the environment and let the client pick it up:

```bash
export CROWDSKY_API_KEY="csk_1a2b3c4d…"
```

```python
from crowdsky_client import Client

c = Client()                          # reads CROWDSKY_API_KEY
```

The base URL defaults to `https://crowdsky.univie.ac.at`; override it with the `base_url` argument
or the `CROWDSKY_API_URL` environment variable (useful against a staging instance).

## First queries

```python
# Every frame imaging a target, deduped across neighbouring sky tiles:
frames = c.frames_for_target(6.0224, -72.0814, radius_deg=0.75)   # 47 Tuc / NGC 104
print(len(frames), "frames")
print(frames[0].keys())

# Frames in one HEALPix tile, with server-side quality filters:
frames = c.frames_by_healpix(49152, filter_name="IRCUT", min_exptime=120)

# Download a stacked FITS by its unique id (bytes, or straight to disk):
data = c.download_frame(frames[0]["id"])
c.download_frame_to(frames[0]["id"], "frame.fits")

# The frame's SEP + Gaia star table, and the public coverage map:
stars = c.star_data(frames[0]["id"])
coverage = c.sky_coverage()          # astropy Table, no key required
```

For a complete worked example — querying 47 Tuc, downloading a frame and its star table, and
overplotting Gaia-matched vs unmatched detections — see {doc}`use_case`.

## Errors

Every request raises {class}`~crowdsky_client.CrowdSkyError` on failure. The common cases:

deflist
: **HTTP 401** — key missing, revoked, expired, or its owner deactivated. Mint a fresh key.
: **`CrowdSkyError: … needs a Bearer key`** — no `api_key` and no `CROWDSKY_API_KEY` in the
  environment.
: **Empty list** — the query succeeded but nothing matched (not an error).

```python
from crowdsky_client import Client, CrowdSkyError

try:
    frames = Client().frames_for_target(6.0224, -72.0814)
except CrowdSkyError as exc:
    print("CrowdSky request failed:", exc)
```

## Offline testing

The HTTP session is injectable, so downstream code stays unit-testable without a network or a key —
pass any object with a `requests`-like `.get()`:

```python
client = Client(api_key="test", base_url="https://example", session=my_fake_session)
```

See `client/tests/test_client.py` in the repository for the pattern.
