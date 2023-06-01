# ParamDB

<!-- start intro -->

Python library for storing and retrieving experiment parameters.

<!-- end intro -->

[![CI](https://github.com/PainterQubits/paramdb/actions/workflows/ci.yml/badge.svg)](https://github.com/PainterQubits/paramdb/actions/workflows/ci.yml)

## Installation

<!-- start installation -->

Install the latest version of ParamDB using pip:

```
pip install -U paramdb --extra-index-url https://painterqubits.github.io/paramdb/releases
```

To install along with [Astropy] for support for storing [`astropy.units.Quantity`]
objects in the database, ParamDB can be installed with the `astropy` extra:

```
pip install -U paramdb[astropy] --extra-index-url https://painterqubits.github.io/paramdb/releases
```

The `extra-index-url` parameter is needed since ParamDB is not published to PyPI yet. If
you are using a Python package manager, add
`https://painterqubits.github.io/paramdb/releases` as a secondary source. For example, for
[Poetry] the command is

```
poetry source add --secondary paramdb https://painterqubits.github.io/paramdb/releases
```

Then the package can be installed like any other (e.g. `poetry add paramdb`).

[poetry]: https://python-poetry.org
[astropy]: https://docs.astropy.org/en/stable/index.html
[`astropy.units.quantity`]: https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity

<!-- end installation -->

## Usage

ParamDB has two main components:

- [**Parameter Data**]: Base classes that are used to defined the structure and
  functionality of parameter data.

- [**Database**]: A database object that commits and loads parameter data to a persistent
  file.

See the [api reference] for more information.

[**parameter data**]: https://painterqubits.github.io/paramdb/parameter-data.html
[**database**]: https://painterqubits.github.io/paramdb/database.html
[api reference]: https://painterqubits.github.io/paramdb/api-reference
