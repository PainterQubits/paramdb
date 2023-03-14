# Parameter Data

```{py:currentmodule} paramdb

```

<!-- Jupyter Sphinx setup -->

```{jupyter-execute}
:hide-code:

from __future__ import annotations
```

A ParamDB database stores parameter data. The abstract base class {py:class}`ParamData`
defines some core functionality for this data, including the
{py:class}`~ParamData.last_updated`, {py:class}`~ParamData.parent`, and
{py:class}`~ParamData.root` properties. Internally, any subclasses of
{py:class}`ParamData` automatically registered with ParamDB so that they can be loaded
to and from JSON, which is how they are stored in the database.

All of the classes described on this page are subclasses of {py:class}`ParamData`.

```{important}
Any data that is going to be stored in a ParamDB database must be a JSON serializable
type (`str`, `int`, `float`, `bool`, `None`, `dict`, or `list`), a [`datetime`], an
[`astropy.units.Quantity`], or an instance of a {py:class}`ParamData` subclass. Otherwise,
a `TypeError` will be raised when they are committed to the database.
```

## Parameters

A parameter is defined from the base class {py:class}`Param`. This custom class is
automatically converted into a [`dataclass`], meaning that class variables with type
annotations become object properties and the corresponding [`__init__`] function is
generated. An example of a defining a custom parameter is shown below.

```{jupyter-execute}
from paramdb import Param

class CustomParam(Param):
    value: float

param = CustomParam(value=1.23)
```

These properties can then be accessed and updated.

```{jupyter-execute}
param.value += 0.004
param.value
```

The dataclass aspects of the subclass can be customized by passing keyword arguments when
defining the custom class (the same arguments that would be passed to the [`@dataclass`]
decorator), and by using the dataclass [`field`] function. The class arguments have the
same default values as in [`@dataclass`], except `kw_only` is True by default for
ParamDB dataclasses to facilitate dataclass inheritance with default values. An example of
dataclass customization is shown below.

```{jupyter-execute}
from dataclasses import field

class CustomizedDataclassParam(Param, kw_only=False, repr=False):
    values: list[int] = field(default_factory=list)

customized_dataclass_param = CustomizedDataclassParam([1, 2, 3])
customized_dataclass_param.values
```

Methods can also be added, including dynamic read-only properties using the
[`@property`](https://docs.python.org/3/library/functions.html#property) decorator. For
example:

```{jupyter-execute}
class ParamWithProperty(Param):
    value: int

    @property
    def value_cubed(self) -> int:
        return self.value ** 3

param_with_property = ParamWithProperty(value=16)
param_with_property.value_cubed
```

````{important}
Since [`__init__`] is generated for dataclasses, other initialization must be done using
the [`__post_init__`] function. Furthermore, since [`__post_init__`] is used internally by
{py:class}`ParamData`, {py:class}`Param`, and {py:class}`Struct` to perform
initialization, always call the superclass's [`__post_init__`] at the end. For example:

```{jupyter-execute}
class ParamCustomInit(Param):
    def __post_init__(self) -> None:
        print("Initializing...")  # Replace with custom initialization code
        super().__post_init__()

param_custom_init = ParamCustomInit()
```
````

```{tip}
Since the base class of all parameter classes, {py:class}`ParamData`, is an abstract class
that inherits from [`abc.ABC`], you can use abstract decorators in parameter and structure
classes without inheriting from [`abc.ABC`] again.
```

Parameters track when any of their properties was last updated in the read-only
{py:attr}`~Param.last_updated` property. For example:

```{jupyter-execute}
param.last_updated
```

```{jupyter-execute}
import time

time.sleep(1)
param.value += 1
param.last_updated
```

## Structures

A structure is defined from the base class {py:class}`Struct` and is intended
to be defined as a dataclass. The key difference from {py:class}`Param` is that
structures do not store their own last updated time; instead, the
{py:attr}`ParamData.last_updated` property returns the most recent last updated time
of any {py:class}`ParamData` they contain. For example:

```{jupyter-execute}
from paramdb import Struct, ParamDict

class CustomStruct(Struct):
    value: float
    param: CustomParam

struct = CustomStruct(value=1.23, param=CustomParam(value=4.56))
struct.last_updated
```

```{jupyter-execute}
time.sleep(1)
struct.param.value += 1
struct.last_updated
```

You can access the parent of any parameter data using the {py:attr}`ParamData.parent`
property. For example:

```{jupyter-execute}
struct.param.parent == struct
```

Similarly, the root can be accessed via {py:attr}`ParamData.root`:

```{jupyter-execute}
struct.param.root == struct
```

See [Type Mixins](#type-mixins) for information on how to get the parent and root
properties to work better with static type checkers.

## Collections

Ordinary lists and dictionaries can be used within parameter data; however, any
parameter data objects they contain will not have a parent object. This is because
internally, the parent is set by the {py:class}`ParamData` object that most recently
added the given parameter data as a child. Therefore, it is not recommended to use
ordinary lists and dictionaries to store parameter data. Instead, {py:class}`ParamList`
and {py:class}`ParamDict` can be used.

{py:class}`ParamList` implements the abstract base class `MutableSequence` from
[`collections.abc`], so it behaves similarly to a list. It is also a subclass of
{py:class}`ParamData`, so the parent and root properties will work properly. For
example,

```{jupyter-execute}
from paramdb import ParamList

param_list = ParamList([CustomParam(value=1), CustomParam(value=2), CustomParam(value=3)])
param_list[1].parent == param_list
```

Similarly, {py:class}`ParamDict` implements `MutableMapping` from [`collections.abc`],
so it behaves similarly to a dictionary. Additionally, its items can be accessed via
dot notation in addition to index brackets (unless they begin with an underscore). For
example,

```{jupyter-execute}
from paramdb import ParamDict

param_dict = ParamDict(
    p1=CustomParam(value=1.23),
    p2=CustomParam(value=4.56),
    p3=CustomParam(value=7.89),
)
param_dict.p2.root == param_dict
```

Parameter collections can also be subclassed to provide custom functionality. For example:

```{jupyter-execute}
class CustomDict(ParamDict[CustomParam]):
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

class ParentStruct(Struct):
    param: Child

class ChildParam(Param, ParentType[ParentStruct]):
    value: float

struct = ParentStruct(param=ChildParam(value=1.23))
```

This does nothing to the functionality, but static type checkers will now know that
`struct.param.parent` in the example above is a `ParentStruct` object.

[`datetime`]: https://docs.python.org/3/library/datetime.html#datetime-objects
[`astropy.units.quantity`]: https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity
[`dataclass`]: https://docs.python.org/3/library/dataclasses.html
[`@dataclass`]: https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass
[`field`]: https://docs.python.org/3/library/dataclasses.html#dataclasses.field
[`__init__`]: https://docs.python.org/3/reference/datamodel.html#object.__init__
[`@property`]: https://docs.python.org/3/library/functions.html#property
[`__post_init__`]: https://docs.python.org/3/library/dataclasses.html#post-init-processing
[`abc.abc`]: https://docs.python.org/3/library/abc.html#abc.ABC
[`collections.abc`]: https://docs.python.org/3/library/collections.abc.html
