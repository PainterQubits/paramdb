# Usage

```{py:currentmodule} paramdb

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
[`@dataclasses.dataclass`](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass)
decorator, meaning that class variables with type annotations are automatically become
object properties, and the corresponding `__init__` function is generated. An example of
a defining a custom parameter is shown below.

```python
from paramdb import Param
from dataclasses import dataclass

@dataclass
class CustomParam(Param):
    value: float

custom_param = CustomParam(value=1.23)
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

### Structures

A structure is defined from the base class {py:class}`Struct` and is intended
to be defined as a dataclass. A structure can contain any data, but it is intended to
store parameters and lists and dictionaries of parameters. For example:

```python
from paramdb import Struct

@dataclass
class CustomStruct(Param):
    param: CustomParam
    param_dict: dict[str, CustomParam]

custom_struct = CustomStruct(
    param = CustomParam(value=1.23)
    param_dict = {
        "p1": CustomParam(value=4.56),
        "p2": CustomParam(value=7.89),
    }
)
```

Structures also have a {py:attr}`Struct.last_updated` property that computes the most
recent last updated time from any of its child parameters (including those within
structures, lists, and dictionaries).

## Database

The database is represented by a {py:class}`ParamDB` object. A path is passed, and a new
database file is created if it does not already exist. We can parameterize the class with
the root data type in order for its methods (e.g. {py:meth}`ParamDB.commit`) work properly
with type checking. For example:

```python
from paramdb import ParamDB

param_db = ParamDB[CustomStruct]("path/to/param.db")
```

```{note}
The {py:class}`ParamDB` object should be created once per project and imported by other
files that access the database.
```

Data can then be committed and loaded as follows:

```python
param_db.commit("Initial commit", custom_struct)

custom_struct_loaded = param_db.load()
```

```{warning}
Simulataneous database operations have not been tested yet. Simultaneous read operations
(e.g. calls to {py:meth}`ParamDB.load`) are likely ok, but simultaneous write operations
(e.g. calls to {py:meth}`ParamDB.commit`) may raise an error.
```

We can get a list of commits using the {py:meth}`ParamDB.commit_history` method.
