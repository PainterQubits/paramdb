# Usage

```{py:currentmodule} paramdb

```

<!-- Jupyter Sphinx setup -->

```{jupyter-execute}
:hide-code:

import os
from tempfile import TemporaryDirectory
tmp_dir = TemporaryDirectory()
os.chdir(tmp_dir.name)
os.makedirs("path/to")
```

ParamDB has two main components:

- [Parameter Data](#parameter-data): Base classes that are used to defined the structure
  of parameter data, which consists of parameters ({py:class}`Param`) and groups of
  parameters, called structures ({py:class}`Struct`).

- [Database](#database): A database object ({py:class}`ParamDB`) that commits and loads
  parameter data to a persistent file.

The usage of each of these components is explained in more detail below.

## Parameter Data

### Parameters

A parameter is defined from the base class {py:class}`Param`. This custom class is
intended to be defined using the
[`@dataclass`](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass)
decorator, meaning that class variables with type annotations are automatically become
object properties, and the corresponding `__init__` function is generated. An example of
a defining a custom parameter is shown below.

```{jupyter-execute}
from paramdb import Param
from dataclasses import dataclass

@dataclass
class CustomParam(Param):
    value: float

param = CustomParam(value=1.23)
```

```{tip}
Methods can also be added to {py:class}`Param` and {py:class}`Struct` subclasses,
including read-only properties using the
[`@property`](https://docs.python.org/3/library/functions.html#property) decorator.

Also, since the `__init__` function is generated, other initialization should be done
using the
[`__post_init__`](https://docs.python.org/3/library/dataclasses.html#post-init-processing)
function.
```

Parameters track when any of their properties was last updated in the read-only
{py:attr}`Param.last_updated` property.

```{jupyter-execute}
param.last_updated
```

### Structures

A structure is defined from the base class {py:class}`Struct` and is intended
to be defined as a dataclass. A structure can contain any data, but it is intended to
store parameters and lists and dictionaries of parameters. For example:

```{jupyter-execute}
from paramdb import Struct

@dataclass
class CustomStruct(Struct):
    param: CustomParam
    param_dict: dict[str, CustomParam]

struct = CustomStruct(
    param = param,
    param_dict = {
        "p1": CustomParam(value=4.56),
        "p2": CustomParam(value=7.89),
    }
)
```

Structures also have a {py:attr}`Struct.last_updated` property that computes the most
recent last updated time from any of its child parameters (including those within
structures, lists, and dictionaries).

```{jupyter-execute}
struct.last_updated
```

## Database

The database is represented by a {py:class}`ParamDB` object. A path is passed, and a new
database file is created if it does not already exist. We can parameterize the class with
the root data type in order for its methods (e.g. {py:meth}`ParamDB.commit`) work properly
with type checking. For example:

```{jupyter-execute}
from paramdb import ParamDB

param_db = ParamDB[CustomStruct]("path/to/param.db")
```

```{note}
The {py:class}`ParamDB` object should be created once per project and imported by other
files that access the database.
```

Data can be committed using {py:meth}`ParamDB.commit` and loaded using
{py:meth}`ParamDB.load`. Note that commit IDs start from 1. For example:

```{jupyter-execute}
param_db.commit("Initial commit", struct)

param_db.load() == struct
```

```{warning}
Simultaneous database operations have not been tested yet. Simultaneous read operations
(e.g. calls to {py:meth}`ParamDB.load`) are likely ok, but simultaneous write operations
(e.g. calls to {py:meth}`ParamDB.commit`) may raise an exception.
```

We can get a list of commits using the {py:meth}`ParamDB.commit_history` method.

```{jupyter-execute}
param_db.commit_history()
```

<!-- Jupyter Sphinx cleanup -->

```{jupyter-execute}
:hide-code:

# Gets ride of PermissionError on Windows
param_db._engine.dispose()
```
