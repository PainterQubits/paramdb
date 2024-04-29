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
from paramdb import ParamDataclass, ParamDB

class Root(ParamDataclass):
    param: CustomParam

class CustomParam(ParamDataclass):
    value: float

param_db = ParamDB[Root]("path/to/param.db")
```

```{important}
The {py:class}`ParamDB` object should be created once per project and imported by other
files that access the database.
```

```{note}
Dataclass fields created with `init=False` will not be stored in or restored from the
database. See [`dataclasses.field`] for more information.
```

## Commit and Load

Data can be committed using {py:meth}`ParamDB.commit` and loaded using
{py:meth}`ParamDB.load`, which either loads the most recent commit, or takes a specific
commit ID. Note that commit IDs start from 1. For example:

```{jupyter-execute}
root = Root(param=CustomParam(value=1.23))
param_db.commit(f"Initial commit", root)
for _ in range(10):
    root.param.value += 1
    param_db.commit(f"Increment param value to {root.param.value}", root)
```

We can then load the most recent commit:

```{jupyter-execute}
param_db.load()
```

Or a specific previous commit:

```{jupyter-execute}
param_db.load(5)
```

## Commit History

We can get a list of commits (as {py:class}`CommitEntry` objects) using the
{py:meth}`ParamDB.commit_history` method.

```{jupyter-execute}
param_db.commit_history()
```

A specific range can also be requested by passing in start and/or end indices to
{py:meth}`ParamDB.commit_history`, which function like Python list slicing, where the
start index is inclusive and the end is exclusive. For example:

```{jupyter-execute}
param_db.commit_history(3, 6)
```

Note that the indices passed in are list indices, and do not necessarily correspond
to commit IDs, whereas {py:meth}`ParamDB.load` takes in a specific commit ID.

Negative indices also are allowed and function like Python list slicing. For example, to
get the last three commits, we can pass in `-3` for the start and leave the end as
`None`.

```{jupyter-execute}
param_db.commit_history(start=-3)
```

<!-- Jupyter Sphinx cleanup -->

```{jupyter-execute}
:hide-code:

param_db.dispose()  # Fixes PermissionError on Windows
```

[`dataclasses.field`]: https://docs.python.org/3/library/dataclasses.html#dataclasses.field
