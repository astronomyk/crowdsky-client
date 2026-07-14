# Background: what CrowdSky is

CrowdSky is a cloud stacking service for [ZWO Seestar S50](https://www.seestar.com/) telescope
users, run at the University of Vienna. Users upload raw FITS frames; the service groups them into
short time blocks, stacks each block into a deep image, plate-solves it, extracts sources, and
stores the results permanently. The pooled result is a growing, time-resolved archive of the sky
imaged by many small telescopes — which is what this client lets you query.

## Architecture in one paragraph

A PHP web frontend (`crowdsky.univie.ac.at`, backed by MariaDB) handles uploads, accounts, and the
API. A Python worker on a compute node polls for stacking jobs, does the alignment/debayer/stack
and plate-solving, and writes stacked FITS + thumbnails + star tables to WebDAV cloud storage. The
client talks only to the frontend's HTTP API; it never touches the database or storage directly.

## The data you get back

Each stacked image is a **`stacked_frame`**. `frames_by_healpix` and `frames_for_target` return one
dict per frame; the fields you will use most:

deflist
: **`id`** — unique integer handle. Pass it to `download_frame`, `star_data`.
: **`object_name`** — target name from the FITS `OBJECT` header, when present.
: **`ra_deg` / `dec_deg`** — frame pointing centre (degrees).
: **`filter_name`** — the optical filter: `LP` (a dual-band H-α/O-III light-pollution filter) or
  `IRCUT` (no narrowband filter). Useful to separate emission-line from broadband stacks.
: **`total_exptime`** — cumulative exposure of the stack, seconds. A rough quality/depth proxy.
: **`eq_mode`** — `0`/`1`, whether the mount tracked in equatorial mode.
: **`sqm`** — sky-quality-meter estimate (mag/arcsec²) where available; higher is darker.
: **`n_frames_input` / `n_frames_aligned`** — sub-frames fed in vs successfully aligned.
: **`n_stars_detected`** — SEP source count on the stack.
: **`date_obs_start` / `date_obs_end`** — UTC window the sub-frames span.
: **`chunk_key`** — the tiling key (below).

## Chunk keys and HEALPix tiling

Every frame is tagged with a **chunk key** of the form:

```
YYYYMMDD.CC_HPnnnnnn
```

- `YYYYMMDD` — UTC observation date.
- `CC` — 15-minute block index within the day, `floor(seconds_since_midnight / 900)`, range 0–95.
- `HPnnnnnn` — the **HEALPix RING pixel at NSIDE = 128** covering the pointing (196 608 pixels over
  the sky; each ≈ 27.5′ across).

A single NSIDE-128 tile is *smaller* than the Seestar's ~1.3° field of view, so a target can be
imaged by frames whose pointing centre falls in a neighbouring tile. That is why
{meth}`~crowdsky_client.Client.frames_for_target` cone-searches the covering pixels (default radius
0.75°) and unions the per-tile results rather than querying a single pixel.

The same tiling underpins the public **sky-coverage** feed
({meth}`~crowdsky_client.Client.sky_coverage`): one row per (tile, filter) with cumulative exposure,
observation counts, and first/last-observed timestamps — a fast way to see where and how deeply the
sky has been imaged before you pull individual frames.

## Star tables

Each stack has a star table (from `star_data`) produced during processing: SEP-detected sources with
pixel positions and fluxes, cross-matched against **Gaia**. Detections that matched a Gaia source
carry the catalogue association (and, where computed, a synthetic magnitude); unmatched detections
are typically cosmic rays, hot pixels, extended-object substructure, or genuine transients. The
{doc}`worked example <use_case>` uses exactly this matched/unmatched split.

```{note}
Star tables are *detected sources*, not forced photometry. To measure a transient at a known
position you still need the pixels — download the frame and photometer it yourself.
```

## How the client fits the bigger picture

CrowdSky is the **data + identity plane** of a three-part design: this client and the per-user API
keys behind it (plane 1), the scientist's analysis module that depends only on this SDK (plane 2,
built on the CrowdSci side), and the CrowdSci orchestration service that runs merged modules on a
schedule (plane 3). Because a module codes against this client and nothing else, it runs the same on
a laptop and on the production node.
