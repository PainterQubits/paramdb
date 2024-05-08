# ParamDB

<!-- start badges -->

[![PyPI Latest Release](https://img.shields.io/pypi/v/paramdb)](https://pypi.org/project/paramdb/)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/paramdb)](https://pypi.org/project/paramdb/)
[![License](https://img.shields.io/pypi/l/paramdb)](https://github.com/PainterQubits/paramdb/blob/main/LICENSE)
[![CI](https://github.com/PainterQubits/paramdb/actions/workflows/ci.yml/badge.svg)](https://github.com/PainterQubits/paramdb/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/github/PainterQubits/paramdb/branch/main/graph/badge.svg?token=PQEJWLBTBK)](https://codecov.io/github/PainterQubits/paramdb)
[![Documentation Status](https://readthedocs.org/projects/paramdb/badge/?version=stable)](https://paramdb.readthedocs.io/en/stable/?badge=stable)

<!-- end badges -->

<!-- start intro -->

Python package for storing and retrieving experiment parameters.

<!-- end intro -->

## Installation

<!-- start installation -->

Install the latest version of ParamDB using pip:

```
pip install -U paramdb
```

ParamDB has several extras:

- `pandas` for [`pandas.DataFrame`] support via [`paramdb.ParamDataFrame`]
- `astropy` for [`astropy.units.Quantity`] support
- `pydantic` for type-validation support via [Pydantic]

To install all extras, use the `all` extra:

```
pip install -U "paramdb[all]"
```

[`pandas.DataFrame`]: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html
[`paramdb.ParamDataFrame`]: https://paramdb.readthedocs.io/en/stable/api-reference.html#paramdb.ParamDataFrame
[`astropy.units.quantity`]: https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity
[Pydantic]: https://docs.pydantic.dev/latest/

<!-- end installation -->

## Usage

ParamDB has two main components:

- [**Parameter Data**]: Base classes that are used to defined the structure and
  functionality of parameter data.

- [**Database**]: A database object that commits and loads parameter data to a persistent
  file.

See the [api reference] for more information.

[**parameter data**]: https://paramdb.readthedocs.io/en/stable/parameter-data.html
[**database**]: https://paramdb.readthedocs.io/en/stable/database.html
[api reference]: https://paramdb.readthedocs.io/en/stable/api-reference.html
