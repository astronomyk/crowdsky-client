# Worked example: 47 Tucanae

This walkthrough queries CrowdSky for stacked frames covering the globular cluster **47 Tucanae**
(NGC 104, RA ≈ 6.0224°, Dec ≈ −72.0814°), downloads one frame and its star table, displays the
green channel of the stack, and overplots circles around the **Gaia-matched** and **unmatched** SEP
detections.

```{admonition} Download the notebook
:class: tip
This page is generated from a Jupyter notebook you can run yourself:
{download}`crowdsky_47tuc_example.ipynb <examples/crowdsky_47tuc_example.ipynb>`.
It needs `crowdsky-client`, `matplotlib`, and a `CROWDSKY_API_KEY` in your environment.
```

The rendered notebook follows. It is shown without executed output (it requires a live key and
network); run it locally to reproduce the figure.

```{toctree}
:maxdepth: 1

examples/crowdsky_47tuc_example
```

## What it demonstrates

- {meth}`~crowdsky_client.Client.frames_for_target` — a coordinate cone-search that unions the
  covering HEALPix tiles and dedups by frame `id`.
- {meth}`~crowdsky_client.Client.download_frame` — fetch a stacked FITS as bytes and open it with
  `astropy.io.fits` from memory.
- {meth}`~crowdsky_client.Client.star_data` — fetch the frame's SEP + Gaia star table as JSON.
- Splitting detections into Gaia-matched vs unmatched and overplotting them on the green layer.

The notebook's column-detection helpers are intentionally defensive — CrowdSky's star-table schema
may evolve, so the example prints the available keys and adapts, which also makes it a handy probe
of the live data.
