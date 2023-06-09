# ParamDB

[![CI](https://github.com/PainterQubits/paramdb/actions/workflows/ci.yml/badge.svg)](https://github.com/PainterQubits/paramdb/actions/workflows/ci.yml)

<!-- start intro -->

Python library for storing and retrieving experiment parameters.

<!-- end intro -->

## Installation

<!-- start installation -->

Install the latest version of ParamDB using pip:

```
pip install -U paramdb
```

To install along with [Astropy] for support for storing scalar [`astropy.units.Quantity`]
objects in the database, ParamDB can be installed with the `astropy` extra:

```
pip install -U paramdb[astropy]
```

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
