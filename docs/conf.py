# See https://www.sphinx-doc.org/en/master/usage/configuration.html for all options

# Project information
project = "ParamDB"
copyright = "2023, California Institute of Technology"
author = "Alex Hadley"
release = "0.3.0"

# General configuration
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "jupyter_sphinx",
]

# HTML output options
html_theme = "furo"
html_static_path = ["_static"]

# MyST options
myst_heading_anchors = 3

# Autodoc options
# See https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration
autodoc_default_options = {"members": True, "member-order": "bysource"}
autodoc_inherit_docstrings = False
add_module_names = False


# Autodoc custom signature and return annotation processing
def process_signature(app, what, name, obj, options, signature, return_annotation):
    if isinstance(return_annotation, str):
        return_annotation = return_annotation.replace("paramdb._database.", "")
    return signature, return_annotation


# Connect event handling
def setup(app):
    app.connect("autodoc-process-signature", process_signature)
