# crowdsky-client

A lightweight Python client for the [CrowdSky](https://crowdsky.univie.ac.at) data API —
discover and download crowd-sourced Seestar S50 stacked frames, their star tables, and sky
coverage, from a laptop or from a compute node.

It is the shared contract between CrowdSky, the scientists writing
[CrowdSci](https://crowdsci.univie.ac.at) analysis modules, and the CrowdSci runner on Zeus,
so a pipeline behaves identically in development and in production. The package depends only on
`requests`, `astropy`, and `astropy-healpix` — **not** the stacking engine — so it installs
cleanly anywhere.

```{code-block} python
from crowdsky_client import Client

c = Client(api_key="csk_…")                       # or set CROWDSKY_API_KEY
frames = c.frames_for_target(6.0224, -72.0814)    # 47 Tuc
fits_bytes = c.download_frame(frames[0]["id"])
```

```{admonition} Get an API key
:class: tip
Log in at [crowdsky.univie.ac.at](https://crowdsky.univie.ac.at) → **Account** → *Create key*.
The secret (`csk_…`) is shown once — see {doc}`getting_started`.
```

## Contents

```{toctree}
:maxdepth: 2

getting_started
use_case
background
rest_api
api
```

## Indices

- {ref}`genindex`
- {ref}`modindex`
