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
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx_copybutton",
]

# HTML output options
html_theme = "furo"

# MyST options
myst_heading_anchors = 3

# Autodoc options
# See https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration
autodoc_default_options = {"members": True, "member-order": "bysource"}


# Autodoc custom signature and return annotation processing
def process_signature(app, what, name, obj, options, signature, return_annotation):
    if isinstance(signature, str):
        signature = signature.replace("~", "")
        signature = signature.replace("paramdb._database.", "")
    if isinstance(return_annotation, str):
        return_annotation = return_annotation.replace("paramdb._database.", "")
    return signature, return_annotation


# Connect event handling
def setup(app):
    app.connect("autodoc-process-signature", process_signature)