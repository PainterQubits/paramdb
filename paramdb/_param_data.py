"""Base classes for parameter data, including structures and parameters."""

from __future__ import annotations

from typing import Any
from collections.abc import Iterable, Mapping
from abc import ABCMeta, abstractmethod
from weakref import WeakValueDictionary
from datetime import datetime
from dataclasses import dataclass, field, fields

# Stores weak references to existing parameter classes
_param_classes: WeakValueDictionary[str, _ParamClass] = WeakValueDictionary()


def get_param_class(class_name: str) -> _ParamClass | None:
    """Get a parameter class given its name, or ``None`` if the class does not exist."""
    return _param_classes[class_name] if class_name in _param_classes else None


class _ParamClass(ABCMeta):
    """
    Metaclass for all parameter classes. Inherits from ABCMeta to allow for abstract
    methods.
    """

    def __new__(
        mcs: type[_ParamClass],
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> _ParamClass:
        """
        Construct a new parameter class and add it to the dictionary of parameter
        classes.
        """
        param_class = super().__new__(mcs, name, bases, namespace, **kwargs)
        _param_classes[name] = param_class
        return param_class

    def from_dict(cls, json_dict: dict[str, Any]) -> Any:
        """
        Construct a parameter data object from the given dictionary, usually created by
        `json.loads`.
        """
        return cls(**json_dict)


@dataclass
class ParamData(metaclass=_ParamClass):
    """
    Abstract base class for all parameter data. The base classes :py:class:`Struct` and
    :py:class:`Param` are subclasses of this class.

    Custom parameter data classes are intended to be dataclasses. If they are not
    dataclasses, then custom :py:meth:`to_dict` and ``__init__`` methods should be
    defined so that the parameter data object can be properly converted to and from
    JSON. See :py:meth:`to_dict` for more information.
    """

    @property
    @abstractmethod
    def last_updated(self) -> datetime | None:
        """
        When this parameter data was last updated, or None if no last updated time
        exists.
        """

    def to_dict(self) -> dict[str, Any]:
        """
        Convert this parameter data object into a dictionary to be passed to
        ``json.dumps``. This dictionary will later be passed to the subclass's
        ``__init__`` function to reconstruct the object. By default, the dictionary maps
        from Python dataclass fields to values.

        Note that objects within the dictionary do not need to be JSON serializable,
        since they will be recursively processed by ``json.dumps``.
        """
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def __getitem__(self, name: str) -> Any:
        """Enable getting attributes via indexing."""
        return getattr(self, name)

    def __setitem__(self, name: str, value: Any) -> Any:
        """Enable setting attributes via indexing."""
        return setattr(self, name, value)


class Struct(ParamData):
    """
    Base class for parameter structures. Custom structures should be subclasses of this
    class and are intended to be dataclasses. For example::

        from dataclasses import dataclass
        from paramdb import Struct

        @dataclass
        class CustomStruct(Struct):
            custom_param: CustomParam  # CustomParam class is defined somewhere else

    A structure can contain any data, but it is intended to store parameters and lists
    and dictionaries of parameters.
    """

    @property
    def last_updated(self) -> datetime | None:
        """
        When any parameter within this structure (including those nested within lists,
        dictionaries, and other structures) was last updated, or ``None`` if this
        structure contains no parameters.
        """
        return self._get_last_updated(getattr(self, f.name) for f in fields(self))

    def _get_last_updated(self, obj: Any) -> datetime | None:
        """
        Get the last updated time from a :py:class:`ParamData` object, or recursively
        search through any iterable type to find the latest last updated time.
        """
        if isinstance(obj, ParamData):
            return obj.last_updated
        if isinstance(obj, Iterable) and not isinstance(obj, str):
            # Strings are excluded because they will never contain ParamData and contain
            # strings, leading to infinite recursion.
            values = obj.values() if isinstance(obj, Mapping) else obj
            return max(
                filter(None, (self._get_last_updated(v) for v in values)),
                default=None,
            )
        return None


@dataclass(kw_only=True)
class Param(ParamData):
    """
    Base class for parameters. Custom parameters should be subclasses of this class and
    are intended to be dataclasses. For example::

        from dataclasses import dataclass
        from paramdb import Param

        @dataclass
        class CustomParam(Param):
            value: float
    """

    _last_updated: datetime = field(default_factory=datetime.now)

    _initialized = False

    def __post_init__(self) -> None:
        """Register that the object is done initializing."""
        # Use the superclass setattr method to avoid updating _last_updated.
        super().__setattr__("_initialized", True)

    @property
    def last_updated(self) -> datetime:
        """When this parameter was last updated."""
        return self._last_updated

    def __setattr__(self, name: str, value: Any) -> None:
        """Set the given attribute and update the last updated time."""
        super().__setattr__(name, value)
        if self._initialized:
            super().__setattr__("_last_updated", datetime.now())
