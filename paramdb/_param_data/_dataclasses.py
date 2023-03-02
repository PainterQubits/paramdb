"""Base classes for parameter dataclasses, including structures and parameters."""


from __future__ import annotations
from typing import Any
from collections.abc import Iterable, Mapping
from abc import abstractmethod
from datetime import datetime
from dataclasses import dataclass, field, fields
from typing_extensions import Self
from paramdb._param_data import ParamData


@dataclass
class _ParamDataclass(ParamData):
    """Base class for parameter dataclasses."""

    # Whether this dataclass object is done initializing
    _initialized = False

    def __post_init__(self) -> None:
        # Register that this object is done initializing
        # Use superclass __setattr__ to avoid updating _last_updated
        super().__setattr__("_initialized", True)

    def __getitem__(self, name: str) -> Any:
        # Enable getting attributes via indexing
        return getattr(self, name)

    def __setitem__(self, name: str, value: Any) -> None:
        # Enable setting attributes via indexing
        setattr(self, name, value)

    @property
    @abstractmethod
    def last_updated(self) -> datetime | None:
        ...

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Self:
        return cls(**json_dict)


@dataclass(kw_only=True)
class Param(_ParamDataclass):
    """
    Base class for parameters. Custom parameters should be subclasses of this class and
    are intended to be dataclasses. For example::

        @dataclass
        class CustomParam(Param):
            value: float
    """

    _last_updated: datetime = field(default_factory=datetime.now)

    def __setattr__(self, name: str, value: Any) -> None:
        # Set the given attribute and update the last updated time
        if self._initialized:
            super().__setattr__("_last_updated", datetime.now())
        super().__setattr__(name, value)

    @property
    def last_updated(self) -> datetime:
        """When this parameter was last updated."""
        return self._last_updated


@dataclass
class Struct(_ParamDataclass):
    """
    Base class for parameter structures. Custom structures should be subclasses of this
    class and are intended to be dataclasses. For example::

        @dataclass
        class CustomStruct(Struct):
            custom_param: CustomParam

    A structure can contain any data, but it is intended to store parameters and lists
    and dictionaries of parameters.
    """

    def __post_init__(self) -> None:
        """Set `_parent` attributes on parameter data this object contains."""
        for f in fields(self):
            child = getattr(self, f.name)
            if isinstance(child, ParamData):
                child._set_parent(self)  # pylint: disable=protected-access
        super().__post_init__()

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

    @property
    def last_updated(self) -> datetime | None:
        """
        When any parameter within this structure (including those nested within lists,
        dictionaries, and other structures) was last updated, or ``None`` if this
        structure contains no parameters.
        """
        return self._get_last_updated(getattr(self, f.name) for f in fields(self))
