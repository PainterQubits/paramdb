"""Base classes for parameter dataclasses."""

from __future__ import annotations
from typing import Any
from abc import abstractmethod
from datetime import datetime, timezone
from dataclasses import dataclass, is_dataclass, fields
from typing_extensions import Self, dataclass_transform
from paramdb._keys import LAST_UPDATED_KEY
from paramdb._param_data._param_data import ParamData


@dataclass_transform()
class _ParamDataclass(ParamData):
    """
    Base class for parameter dataclasses.

    Any keyword arguments given when creating a subclass are passed to the dataclass
    constructor.
    """

    def __init_subclass__(cls, /, **kwargs: Any) -> None:
        # Convert subclasses into dataclasses
        super().__init_subclass__()  # kwargs are passed to dataclass constructor
        dataclass(**kwargs)(cls)

    def __getitem__(self, name: str) -> Any:
        # Enable getting attributes via indexing
        return getattr(self, name)

    def __setitem__(self, name: str, value: Any) -> None:
        # Enable setting attributes via indexing
        setattr(self, name, value)

    @property
    @abstractmethod
    def last_updated(self) -> datetime | None: ...

    def to_dict(self) -> dict[str, Any]:
        if is_dataclass(self):
            return {f.name: getattr(self, f.name) for f in fields(self) if f.init}
        return {}

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Self:
        return cls(**json_dict)


class Param(_ParamDataclass):
    """
    Subclass of :py:class:`ParamData`.

    Base class for parameters. Subclasses are automatically converted to dataclasses.
    For example::

        class CustomParam(Param):
            value: float
    """

    def __post_init__(self) -> None:
        self.__last_updated = datetime.now(timezone.utc).astimezone()

    def __setattr__(self, name: str, value: Any) -> None:
        # Set the given attribute and update the last updated time if the object is
        # initialized and the variable name does not have a double underscore in it (to
        # exclude private variables, like __initialized, and dunder variables).
        super().__setattr__(name, value)
        if "__" not in name:
            self.__last_updated = datetime.now(timezone.utc).astimezone()

    @property
    def last_updated(self) -> datetime:
        """When this parameter was last updated."""
        return self.__last_updated

    def to_dict(self) -> dict[str, Any]:
        return {LAST_UPDATED_KEY: self.__last_updated} | super().to_dict()

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Self:
        last_updated = json_dict.pop(LAST_UPDATED_KEY)
        obj = cls(**json_dict)
        obj.__last_updated = last_updated  # pylint: disable=unused-private-member
        return obj


class Struct(_ParamDataclass):
    """
    Subclass of :py:class:`ParamData`.

    Base class for parameter structures. Subclasses are automatically converted to
    dataclasses. For example::

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
