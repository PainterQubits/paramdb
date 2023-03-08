"""Base classes for parameter dataclasses."""

from __future__ import annotations
from typing import Any
from abc import abstractmethod
from datetime import datetime
from dataclasses import dataclass, fields
from typing_extensions import Self
from paramdb._param_data._param_data import ParamData


@dataclass
class _ParamDataclass(ParamData):
    """Base class for parameter dataclasses."""

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
        return {f.name: getattr(self, f.name) for f in fields(self) if f.init}

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Self:
        return cls(**json_dict)


@dataclass
class Param(_ParamDataclass):
    """
    Base class for parameters. Custom parameters should be subclasses of this class and
    are intended to be dataclasses. For example::

        @dataclass
        class CustomParam(Param):
            value: float
    """

    def __post_init__(self) -> None:
        self.__last_updated = datetime.now()

    def __setattr__(self, name: str, value: Any) -> None:
        # Set the given attribute and update the last updated time if the object is
        # initialized and the variable name does not have a double underscore in it (to
        # exclude private variables, like __initialized, and dunder variables).
        super().__setattr__(name, value)
        if "__" not in name:
            self.__last_updated = datetime.now()

    @property
    def last_updated(self) -> datetime:
        """When this parameter was last updated."""
        return self.__last_updated

    def to_dict(self) -> dict[str, Any]:
        return {"__last_updated": self.__last_updated} | super().to_dict()

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Self:
        last_updated = json_dict.pop("__last_updated")
        obj = cls(**json_dict)
        obj.__last_updated = last_updated  # pylint: disable=unused-private-member
        return obj


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
        # Add fields as children.
        for f in fields(self):
            self._add_child(getattr(self, f.name))

    def __setattr__(self, name: str, value: Any) -> None:
        old_value = getattr(self, name) if hasattr(self, name) else None
        super().__setattr__(name, value)
        self._remove_child(old_value)
        self._add_child(value)

    @property
    def last_updated(self) -> datetime | None:
        return self._get_last_updated(getattr(self, f.name) for f in fields(self))
