"""Sphinx configuration for the crowdsky-client documentation."""

import os
import sys

# For local builds (RTD pip-installs the package instead). Lets autodoc import
# crowdsky_client from the source tree without an editable install.
sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------

project = "crowdsky-client"
author = "Kieran Leschinski (University of Vienna)"
copyright = "2026, Kieran Leschinski / University of Vienna"

try:
    from importlib.metadata import version as _v

    release = _v("crowdsky-client")
except Exception:
    release = "0.1.0"
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_nb",                # Markdown + .ipynb rendering (no pandoc needed)
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
]

myst_enable_extensions = ["colon_fence", "deflist"]

# Never execute the example notebook at build time — it needs network + a key.
nb_execution_mode = "off"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# -- autodoc -----------------------------------------------------------------

autoclass_content = "both"          # merge class + __init__ docstrings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_mock_imports = ["requests", "astropy", "astropy_healpix"]

napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "astropy": ("https://docs.astropy.org/en/stable", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "requests": ("https://requests.readthedocs.io/en/stable", None),
}

# -- HTML output -------------------------------------------------------------

html_theme = "furo"
html_title = f"crowdsky-client {release}"
html_static_path = ["_static"]
