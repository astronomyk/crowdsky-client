# REST API endpoints

The client is a thin wrapper over four HTTP endpoints under
`https://crowdsky.univie.ac.at/api/`. You rarely need to call them directly, but they are documented
here so the contract is explicit and debuggable (e.g. with `curl`). The authoritative reference is
CrowdSky's own `docs/api-reference.md`.

## Authentication

The three data endpoints take a **Bearer** token that is *either* a personal API key *or* CrowdSky's
shared service key — both grant read access across all pooled frames:

```
Authorization: Bearer csk_1a2b3c4d…
```

A revoked, expired, or unknown key returns **HTTP 401**. `sky_coverage.php` is public (no key).

## `GET /api/frames_by_healpix.php`

Lists stacked frames (all users) whose tile matches one HEALPix RING pixel. Wrapped by
{meth}`~crowdsky_client.Client.frames_by_healpix`; the cone-search
{meth}`~crowdsky_client.Client.frames_for_target` calls it once per covering pixel and dedups.

| Param | Required | Description |
|-------|----------|-------------|
| `healpix` | yes | RING pixel index at NSIDE=128 (0–196607). |
| `start` / `end` | no | ISO-8601 UTC bounds on `date_obs_start` (inclusive). |
| `filter` | no | Exact `filter_name` (`LP`, `IRCUT`). *(client arg: `filter_name`)* |
| `eq_mode` | no | Exact `0`/`1` match. |
| `min_sqm` | no | Keep frames with `sqm ≥ value`. |
| `min_exptime` | no | Keep frames with `total_exptime ≥ value` (seconds). |

**Response** — `200` JSON array (empty `[]` if nothing matches), ordered by `date_obs_start`; each
object carries the frame fields described in {doc}`background` plus a `download_url`.

```bash
curl -s -H "Authorization: Bearer $CROWDSKY_API_KEY" \
  "https://crowdsky.univie.ac.at/api/frames_by_healpix.php?healpix=49152&min_exptime=120"
```

## `GET /api/download_frame.php`

Downloads stacked FITS by numeric `stacked_frames.id` (all users), proxied from cloud storage.
Wrapped by {meth}`~crowdsky_client.Client.download_frame` and
{meth}`~crowdsky_client.Client.download_frame_to`.

| Param | Required | Description |
|-------|----------|-------------|
| `id` | yes | One id, or several comma-separated. |

- **Single id** → streams the FITS (`Content-Type: application/fits`), body begins `SIMPLE  =`.
- **Multiple ids** → `200` JSON array of `{id, chunk_key, object_name, filename, file_size_bytes,
  download_url}` (metadata only; fetch each file by its own single-id request).

`id` (not `chunk_key`) is the handle because a chunk key is not unique across users.

## `GET /api/frame_stars.php`

Returns one frame's star table (SEP detections + Gaia cross-match) as JSON, proxied from storage.
Wrapped by {meth}`~crowdsky_client.Client.star_data`.

| Param | Required | Description |
|-------|----------|-------------|
| `id` | yes | A single `stacked_frames.id`. |

**Response** — `200` `application/json` star table; `404` if the frame has no star table.

## `GET /api/sky_coverage.php`

Public feed (no auth) of per-tile coverage as an ECSV table: one row per (HEALPix RING tile, filter)
with cumulative exposure, observation counts, and first/last-observed timestamps. Wrapped by
{meth}`~crowdsky_client.Client.sky_coverage`, which parses it into an `astropy.table.Table`.

```bash
curl -s "https://crowdsky.univie.ac.at/api/sky_coverage.php" | head
```
