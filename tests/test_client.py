"""Offline tests for the CrowdSky client: params, Bearer auth, dedup, env fallback.

No network: an injected fake session captures every request. The cone-search test
uses the real ``astropy_healpix`` (only the HTTP layer is faked).
"""

import pytest

from crowdsky_client import Client, CrowdSkyClient, CrowdSkyError


class _Resp:
    def __init__(self, payload=None, content=b"", text="", status_code=200):
        self._payload = payload
        self.content = content
        self.text = text
        self.status_code = status_code

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, responses):
        # responses: callable(path, params) -> _Resp
        self._responses = responses
        self.calls = []

    def get(self, url, params=None, timeout=None, stream=False, headers=None, auth=None):
        path = url.rsplit("/", 1)[-1]
        self.calls.append({"path": path, "params": params or {}, "headers": headers or {}, "auth": auth})
        return self._responses(path, params or {})


def test_client_is_crowdskyclient_alias():
    assert Client is CrowdSkyClient


def test_frames_by_healpix_sends_params_and_bearer():
    def responder(path, params):
        assert path == "frames_by_healpix.php"
        return _Resp(payload=[{"id": 1}, {"id": 2}])

    sess = _FakeSession(responder)
    client = Client(api_key="secret", base_url="https://crowdsky.example", session=sess)
    rows = client.frames_by_healpix(
        49152, start="2026-07-01T00:00:00Z", filter_name="IRCUT", min_exptime=120
    )
    assert [r["id"] for r in rows] == [1, 2]
    call = sess.calls[0]
    assert call["headers"]["Authorization"] == "Bearer secret"
    # None params dropped; filter_name mapped to `filter`; healpix present.
    assert call["params"] == {
        "healpix": 49152,
        "start": "2026-07-01T00:00:00Z",
        "filter": "IRCUT",
        "min_exptime": 120,
    }


def test_frames_by_healpix_requires_key(monkeypatch):
    monkeypatch.delenv("CROWDSKY_API_KEY", raising=False)
    sess = _FakeSession(lambda p, q: _Resp(payload=[]))
    client = Client(base_url="https://crowdsky.example", session=sess)  # no api_key
    with pytest.raises(CrowdSkyError):
        client.frames_by_healpix(49152)


def test_api_key_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("CROWDSKY_API_KEY", "env-secret")
    sess = _FakeSession(lambda p, q: _Resp(payload=[]))
    client = Client(base_url="https://crowdsky.example", session=sess)
    client.frames_by_healpix(49152)
    assert sess.calls[0]["headers"]["Authorization"] == "Bearer env-secret"


def test_base_url_defaults_to_production(monkeypatch):
    monkeypatch.delenv("CROWDSKY_API_URL", raising=False)
    client = Client(api_key="secret", session=_FakeSession(lambda p, q: _Resp()))
    assert client.base_url == "https://crowdsky.univie.ac.at"


def test_frames_for_target_queries_multiple_tiles_and_dedups():
    seen_pixels = []

    def responder(path, params):
        assert path == "frames_by_healpix.php"
        pix = params["healpix"]
        seen_pixels.append(pix)
        # Every tile reports the same frame id 100 plus a tile-unique id, to exercise dedup.
        return _Resp(payload=[
            {"id": 100, "date_obs_start": "2026-07-10T22:00:00Z"},
            {"id": pix, "date_obs_start": "2026-07-11T22:00:00Z"},
        ])

    sess = _FakeSession(responder)
    client = Client(api_key="secret", base_url="https://crowdsky.example", session=sess)
    rows = client.frames_for_target(159.6998, 53.5095, radius_deg=0.75, filter_name="IRCUT")

    # A 0.75deg cone at NSIDE=128 spans several RING tiles (never just one).
    assert len(seen_pixels) > 1
    # Shared id 100 appears once despite being returned by every tile.
    ids = [r["id"] for r in rows]
    assert ids.count(100) == 1
    # Sorted by date_obs_start.
    assert rows[0]["id"] == 100


def test_download_frame_streams_bytes_with_bearer():
    def responder(path, params):
        assert path == "download_frame.php"
        assert params == {"id": 15}
        return _Resp(content=b"SIMPLE  =                    T")

    sess = _FakeSession(responder)
    client = Client(api_key="secret", base_url="https://crowdsky.example", session=sess)
    data = client.download_frame(15)
    assert data.startswith(b"SIMPLE")
    assert sess.calls[0]["headers"]["Authorization"] == "Bearer secret"


def test_download_frame_to_writes_file(tmp_path):
    sess = _FakeSession(lambda p, q: _Resp(content=b"SIMPLE  = T"))
    client = Client(api_key="secret", base_url="https://crowdsky.example", session=sess)
    out = client.download_frame_to(15, tmp_path / "sub" / "frame.fits")
    assert out.read_bytes().startswith(b"SIMPLE")


def test_star_data_hits_frame_stars_endpoint_with_bearer():
    def responder(path, params):
        assert path == "frame_stars.php"
        assert params == {"id": 42}
        return _Resp(payload={"stars": [{"x": 1.0, "y": 2.0}]})

    sess = _FakeSession(responder)
    client = Client(api_key="secret", base_url="https://crowdsky.example", session=sess)
    stars = client.star_data(42)
    assert stars["stars"][0]["x"] == 1.0
    assert sess.calls[0]["headers"]["Authorization"] == "Bearer secret"


def test_sky_coverage_parses_ecsv_no_auth():
    ecsv = (
        "# %ECSV 1.0\n"
        "# ---\n"
        "# datatype:\n"
        "# - {name: healpix_ring, datatype: int64}\n"
        "# - {name: n_stacks, datatype: int64}\n"
        "# schema: astropy-2.0\n"
        "healpix_ring n_stacks\n"
        "49152 3\n"
    )

    def responder(path, params):
        assert path == "sky_coverage.php"
        return _Resp(text=ecsv)

    sess = _FakeSession(responder)
    client = Client(base_url="https://crowdsky.example", session=sess)  # no key needed
    table = client.sky_coverage()
    assert list(table["healpix_ring"]) == [49152]
    # Public endpoint: no Authorization header sent.
    assert "Authorization" not in sess.calls[0]["headers"]


def test_http_error_raises():
    sess = _FakeSession(lambda p, q: _Resp(status_code=401))
    client = Client(api_key="secret", base_url="https://crowdsky.example", session=sess)
    with pytest.raises(CrowdSkyError):
        client.frames_by_healpix(49152)
