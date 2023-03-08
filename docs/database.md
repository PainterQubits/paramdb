# Database

```{py:currentmodule} paramdb

```

<!-- Jupyter Sphinx setup -->

```{jupyter-execute}
:hide-code:

from __future__ import annotations
import os
from tempfile import TemporaryDirectory
tmp_dir = TemporaryDirectory()
os.chdir(tmp_dir.name)
os.makedirs("path/to")
```

The database is represented by a {py:class}`ParamDB` object. A path is passed, and a new
database file is created if it does not already exist. We can parameterize the class with
the root data type in order for its methods (e.g. {py:meth}`ParamDB.commit`) work properly
with type checking. For example:

```{jupyter-execute}
from dataclasses import dataclass
from paramdb import Struct, Param, ParamDB

@dataclass
class Root(Struct):
    param: CustomParam

@dataclass
class CustomParam(Param):
    value: float

param_db = ParamDB[Root]("path/to/param.db")
```

```{note}
The {py:class}`ParamDB` object should be created once per project and imported by other
files that access the database.
```

Data can be committed using {py:meth}`ParamDB.commit` and loaded using
{py:meth}`ParamDB.load`. Note that commit IDs start from 1. For example:

```{jupyter-execute}
root = Root(param=CustomParam(value=1.23))
param_db.commit("Initial commit", root)
param_db.load() == root
```

```{warning}
Simultaneous database operations have not been tested yet. Simultaneous read operations
(e.g. calls to {py:meth}`ParamDB.load`) are likely ok, but simultaneous write operations
(e.g. calls to {py:meth}`ParamDB.commit`) may raise an exception.
```

We can get a list of commits (as {py:class}`CommitEntry` objects) using the
{py:meth}`ParamDB.commit_history` method.

```{jupyter-execute}
param_db.commit_history()
```

<!-- Jupyter Sphinx cleanup -->

```{jupyter-execute}
:hide-code:

# Gets ride of PermissionError on Windows
param_db._engine.dispose()
```
