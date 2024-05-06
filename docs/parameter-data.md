# Parameter Data

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
```

A ParamDB database stores parameter data. The abstract base class {py:class}`ParamData`
defines some core functionality for this data, including the
{py:class}`~ParamData.last_updated`, {py:class}`~ParamData.parent`, and
{py:class}`~ParamData.root` properties. Internally, any subclasses of
{py:class}`ParamData` are automatically registered with ParamDB so that they can be
loaded to and from JSON, which is how they are stored in the database.

All of the "Param" classes described on this page are subclasses of {py:class}`ParamData`.

```{important}
Any data that is going to be stored in a ParamDB database must be a JSON serializable
type (`str`, `int`, `float`, `bool`, `None`, `dict`, or `list`), a [`datetime`], an
[`astropy.units.Quantity`], or an instance of a {py:class}`ParamData` subclass. Otherwise,
a `TypeError` will be raised when they are committed to the database.
```

## Primitives

Primitives are the building blocks of parameter data. While builtin primitive types can
be used in a ParamDB (`int`, `float`, `str`, `bool`, and `None`), they will not store a
{py:class}`~ParamData.last_updated` time and will not have {py:class}`~ParamData.parent`
or {py:class}`~ParamData.root` properties. When these features are desired, we can wrap
primitive values in the following types:

- {py:class}`ParamInt` for integers
- {py:class}`ParamFloat` for float
- {py:class}`ParamBool` for booleans
- {py:class}`ParamStr` for strings
- {py:class}`ParamNone` for `None`

For example:

```{jupyter-execute}
from paramdb import ParamInt

param_int = ParamInt(123)
param_int
```

```{jupyter-execute}
print(param_int.last_updated)
```

````{tip}
Methods from the builtin primitive types work on parameter primitives, with the caveat
that they return the builtin type. For example:

```{jupyter-execute}
param_int + 123
```

```{jupyter-execute}
type(param_int + 123)
```
````

## Data Classes

A parameter data class is defined from the base class {py:class}`ParamDataclass`. This
custom class is automatically converted into a [data class], meaning that class variables
with type annotations become object properties and the corresponding [`__init__`]
function is generated. An example of a defining a custom parameter Data Class is shown
below.

```{jupyter-execute}
from paramdb import ParamFloat, ParamDataclass

class CustomParam(ParamDataclass):
    value: ParamFloat

custom_param = CustomParam(value=ParamFloat(1.23))
```

These properties can then be accessed and updated.

```{jupyter-execute}
custom_param.value = ParamFloat(1.234)
custom_param.value
```

The data class aspects of the subclass can be customized by passing keyword arguments when
defining the custom class (the same arguments that would be passed to the [`@dataclass`]
decorator), and by using the dataclass [`field`] function. The class arguments have the
same default values as in [`@dataclass`]. An example of data class customization is shown
below.

```{note}
The `kw_only` setting below only works in Python 3.10, but is useful for defining
non-default arguments after those with default values (like in the example), especially
when building up dataclasses through inheritance.
```

```{jupyter-execute}
from dataclasses import field

class KeywordOnlyParam(ParamDataclass, kw_only=True):
    count: int
    values: list[int] = field(default_factory=list)

keyword_only_param = KeywordOnlyParam(count=123)
keyword_only_param
```

```{warning}
For mutable default values, `default_factory` should generally be used. See the Python
data class documentation on [mutable default values] for more information.
```

Custom methods can also be added, including dynamic properties using the [`@property`]
decorator. For example:

```{jupyter-execute}
class ParamWithProperty(ParamDataclass):
    value: ParamInt

    @property
    def value_cubed(self) -> int:
        return self.value ** 3

param_with_property = ParamWithProperty(value=ParamInt(16))
param_with_property.value_cubed
```

````{important}
Since [`__init__`] is generated for data classes, other initialization must be done using
the [`__post_init__`] function. Furthermore, since [`__post_init__`] is used internally by
{py:class}`ParamDataclass` to perform initialization, always call the superclass's
[`__post_init__`]. For example:

```{jupyter-execute}
class ParamCustomInit(ParamDataclass):
    def __post_init__(self) -> None:
        print("Initializing...")  # Replace with custom initialization code
        super().__post_init__()

param_custom_init = ParamCustomInit()
```
````

Parameter data track when any of their properties were last updated, and this value can be
accessed by the read-only {py:attr}`~ParamData.last_updated` property. For example:

```{jupyter-execute}
print(custom_param.last_updated)
```

```{jupyter-execute}
import time

time.sleep(1)
custom_param.value = ParamFloat(4.56)
print(custom_param.last_updated)
```

Parameter dataclasses can also be nested, in which case the
{py:attr}`ParamData.last_updated` property returns the most recent last updated time stamp
among its own last updated time and the last updated times of any {py:class}`ParamData`
it contains. For example:

```{jupyter-execute}
class NestedParam(ParamDataclass):
    value: float
    child_param: CustomParam

nested_param = NestedParam(value=1.23, child_param=CustomParam(value=ParamFloat(4.56)))
print(nested_param.last_updated)
```

```{jupyter-execute}
time.sleep(1)
nested_param.child_param.value = ParamFloat(2)
print(nested_param.last_updated)
```

You can access the parent of any parameter data using the {py:attr}`ParamData.parent`
property. For example:

```{jupyter-execute}
nested_param.child_param.parent is nested_param
```

Similarly, the root can be accessed via {py:attr}`ParamData.root`:

```{jupyter-execute}
nested_param.child_param.root is nested_param
```

See [Type Mixins](#type-mixins) for information on how to get the parent and root
properties to work better with static type checkers.

### Type Validation

If [Pydantic] is installed, parameter data classes will automatically be converted to
[Pydantic data classes], enabling runtime type validation. Some [Pydantic configuration]
have modified defaults; see {py:class}`ParamDataclass` for more information.

Pydantic type validation will enforce type hints at runtime by raising an exception. For
example:

```{jupyter-execute}
import pydantic

try:
    CustomParam(value="123")
except pydantic.ValidationError as exception:
    print(exception)
```

Type validation can be disabled for a particular parameter data class (and its subclasses)
using the class keyword argument `type_validation`:

```{jupyter-execute}
class NoTypeValidationParam(CustomParam, type_validation=False):
    pass

NoTypeValidationParam(value="123")
```

## Files

{py:class}`ParamFile` is an abstract base class that stores the path to a file. The data
in the file can then be loaded by accessing {py:attr}`ParamFile.data` and updated using
{py:meth}`ParamFile.update_data`. In order to use {py:class}`ParamFile`, it must be
subclassed and the functions `ParamFile._save_data()` and `ParamFile._load_data()` must be
defined.

### Pandas DataFrames

One class that implements these functions is {py:class}`ParamDataFrame` for saving and
retrieving [Pandas DataFrames]. For example:

```{jupyter-execute}
import pandas as pd
from paramdb import ParamDataFrame

data_frame = pd.DataFrame([[1, 2, 3], [4, 5, 6]], columns=["col1", "col2", "col3"])
param_data_frame = ParamDataFrame("data.csv", data_frame)
param_data_frame.data
```

## Collections

Ordinary lists and dictionaries can be used within parameter data; however, any
parameter data objects they contain will not have a last updated time or a parent object.
Therefore, it is not recommended to use ordinary lists and dictionaries to store parameter
data. Instead, {py:class}`ParamList` and {py:class}`ParamDict` can be used.

### Parameter Lists

{py:class}`ParamList` implements the abstract base class `MutableSequence` from
[`collections.abc`], so it behaves similarly to a list. It is also a subclass of
{py:class}`ParamData`, so the last updated, parent, and root properties will work
properly. For example:

```{jupyter-execute}
from paramdb import ParamList

param_list = ParamList([ParamInt(1), ParamInt(2), ParamInt(3)])
param_list[1].parent is param_list
```

```{jupyter-execute}
print(param_list.last_updated)
```

```{jupyter-execute}
time.sleep(1)
param_list[1] = ParamInt(4)
print(param_list.last_updated)
```

### Parameter Dictionaries

Similarly, {py:class}`ParamDict` implements `MutableMapping` from [`collections.abc`],
so it behaves similarly to a dictionary. Additionally, its items can be accessed via
dot notation in addition to index brackets (unless they begin with an underscore). For
example:

```{jupyter-execute}
from paramdb import ParamDict

param_dict = ParamDict(p1=ParamFloat(1.23), p2=ParamFloat(4.56), p3=ParamFloat(7.89))
param_dict.p2.root == param_dict
```

```{jupyter-execute}
print(param_dict.last_updated)
```

```{jupyter-execute}
time.sleep(1)
param_dict.p2 = ParamFloat(0)
print(param_dict.last_updated)
```

Parameter collections can also be subclassed to provide custom functionality. For example:

```{jupyter-execute}
class CustomDict(ParamDict[ParamFloat]):
    @property
    def total(self) -> float:
        return sum(param.value for param in self.values())

custom_dict = CustomDict(param_dict)
custom_dict.total
```

## Type Mixins

The return type hint for {py:attr}`ParamData.parent` and {py:attr}`ParamData.root` is
{py:class}`ParamData`. Since the parent and root objects can change, it is not possible
to automatically infer a more specific type for the parent or root. However, a type hint
can be given using the {py:class}`ParentType` and {py:class}`RootType` mixins. For
example:

```{jupyter-execute}
from paramdb import ParentType

class ParentParam(ParamDataclass):
    child_param: ChildParam

class ChildParam(ParamDataclass, ParentType[ParentParam]):
    value: float

parent_param = ParentParam(child_param=ChildParam(value=1.23))
```

This does nothing to the functionality, but static type checkers will now know that
`parent_param.child_param.parent` in the example above is a `ParentParam` object.

[`datetime`]: https://docs.python.org/3/library/datetime.html#datetime-objects
[`astropy.units.quantity`]: https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity
[data class]: https://docs.python.org/3/library/dataclasses.html
[`@dataclass`]: https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass
[`field`]: https://docs.python.org/3/library/dataclasses.html#dataclasses.field
[`__init__`]: https://docs.python.org/3/reference/datamodel.html#object.__init__
[mutable default values]: https://docs.python.org/3/library/dataclasses.html#mutable-default-values
[`@property`]: https://docs.python.org/3/library/functions.html#property
[`__post_init__`]: https://docs.python.org/3/library/dataclasses.html#post-init-processing
[Pydantic]: https://docs.pydantic.dev/latest/
[Pydantic data classes]: https://docs.pydantic.dev/latest/concepts/dataclasses/
[Pydantic configuration]: https://docs.pydantic.dev/latest/api/config/
[Pandas DataFrames]: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html
[`collections.abc`]: https://docs.python.org/3/library/collections.abc.html
