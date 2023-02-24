# ParamDB

<!-- start intro -->

Python library for storing and retrieving experiment parameters.

<!-- end intro -->

## Installation

<!-- start installation -->

Install the latest version of ParamDB using pip:

```
pip install -U paramdb --extra-index-url https://painterqubits.github.io/paramdb/releases
```

The `extra-index-url` parameter is needed since ParamDB is not published to PyPI yet.

<!-- end installation -->

## Usage

ParamDB has two main components:

- **Parameted Data**: Base classes that are used to defined the structure of parameter
  data, which consists of parameters
  ([`Param`](https://painterqubits.github.io/paramdb/api-reference#paramdb.Param)) and
  groups of parameters, called structures
  ([`Struct`](https://painterqubits.github.io/paramdb/api-reference#paramdb.Struct)).

- **Database**: A database object
  ([`ParamDB`](https://painterqubits.github.io/paramdb/api-reference#paramdb.ParamDB))
  that commits and loads parameter data to a persistent file.

See the [usage page](https://painterqubits.github.io/paramdb/usage) on the documentation
website for examples and more information. Also see the
[api reference](https://painterqubits.github.io/paramdb/api-reference).
