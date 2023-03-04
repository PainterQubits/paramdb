"""Base classes for parameter dataclasses."""

from __future__ import annotations
from typing import Any
from abc import abstractmethod
from datetime import datetime
from dataclasses import dataclass, field, fields
from typing_extensions import Self
from paramdb._param_data import ParamData


@dataclass
class _ParamDataclass(ParamData):
    """Base class for parameter dataclasses."""

    def __getitem__(self, name: str) -> Any:
        # Enable getting attributes via indexing
        return getattr(self, name)

    def __setitem__(self, name: str, value: Any) -> None:
        # Enable setting attributes via indexing
        setattr(self, name, value)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self._add_child(value)

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

    _initialized = False
    _last_updated: datetime = field(repr=False, default_factory=datetime.now)

    def __post_init__(self) -> None:
        # Register that this object is done initializing
        # Use superclass __setattr__ to avoid updating _last_updated if this is a Param
        super().__setattr__("_initialized", True)

    def __setattr__(self, name: str, value: Any) -> None:
        # Set the given attribute and update the last updated time
        super().__setattr__(name, value)
        if self._initialized:
            super().__setattr__("_last_updated", datetime.now())

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
            value: float
            custom_param: CustomParam
    """

    def __post_init__(self) -> None:
        """Add fields as children."""
        for f in fields(self):
            self._add_child(getattr(self, f.name))

    @property
    def last_updated(self) -> datetime | None:
        return self._get_last_updated(getattr(self, f.name) for f in fields(self))
