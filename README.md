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

<!-- start usage -->

ParamDB has two main components:

1. **Parameted Data**: Base classes that are used to defined the structure of parameter
   data, which consists of parameters (`Param`) and groups of parameters, called
   structures (`Struct`).

2. **Database**: A database object (`ParamDB`) that commits and loads parameter data to
   a persistent file.

<!-- end usage -->

See the [usage page](https://painterqubits.github.io/qpuview/usage) on the documentation
website for examples. Also see the
[api reference](https://painterqubits.github.io/qpuview/api-reference).
