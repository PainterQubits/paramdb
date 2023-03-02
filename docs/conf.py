# pylint: skip-file
# type: ignore

# See https://www.sphinx-doc.org/en/master/usage/configuration.html for all options

# Project information
project = "ParamDB"
copyright = "2023, California Institute of Technology"
author = "Alex Hadley"
release = "0.1.0"

# General configuration
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
    "sphinx_copybutton",
    "jupyter_sphinx",
]

# HTML output options
html_theme = "sphinx_rtd_theme"
html_theme_options = {"navigation_depth": 3}

# MyST options
myst_heading_anchors = 3

# Autodoc options
# See https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration
autodoc_default_options = {"members": True, "member-order": "bysource"}
