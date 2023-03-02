"""Base class for all parameter data."""

from __future__ import annotations
from typing import Any, cast
from abc import ABCMeta, abstractmethod
from weakref import WeakValueDictionary
from datetime import datetime
from typing_extensions import Self


# Stores weak references to existing parameter classes
_param_classes: WeakValueDictionary[str, type[ParamData]] = WeakValueDictionary()


def get_param_class(class_name: str) -> type[ParamData] | None:
    """Get a parameter class given its name, or ``None`` if the class does not exist."""
    return _param_classes[class_name] if class_name in _param_classes else None


class _ParamClass(ABCMeta):
    """
    Metaclass for all parameter data classes. Inherits from ABCMeta to allow for
    abstract methods.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> _ParamClass:
        """
        Construct a new parameter data class and add it to the dictionary of parameter
        classes.
        """
        param_class = cast(
            "type[ParamData]", super().__new__(mcs, name, bases, namespace, **kwargs)
        )
        _param_classes[name] = param_class
        return param_class


class ParamData(metaclass=_ParamClass):
    """Abstract base class for all parameter data."""

    # Most recently initialized structure that contains this parameter data
    _parent: ParamData | None = None

    def _set_parent(self, new_parent: ParamData) -> None:
        # Use superclass __setattr__ to avoid updating _last_updated
        super().__setattr__("_parent", new_parent)

    @property
    @abstractmethod
    def last_updated(self) -> datetime | None:
        """
        When this parameter data was last updated, or None if no last updated time
        exists.
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Convert this parameter data object into a dictionary to be passed to
        ``json.dumps``. This dictionary will later be passed to :py:meth:`from_dict`
        to reconstruct the object.

        Note that objects within the dictionary do not need to be JSON serializable,
        since they will be recursively processed by ``json.dumps``.
        """

    @classmethod
    @abstractmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Self:
        """
        Construct a parameter data object from the given dictionary, usually created by
        `json.loads` and originally constructed by :py:meth:`from_dict`.
        """
