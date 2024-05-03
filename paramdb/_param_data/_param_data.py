"""Base class for all parameter data."""

from __future__ import annotations
from typing import Any
from abc import ABC, abstractmethod
from weakref import WeakValueDictionary
from datetime import datetime, timezone
from typing_extensions import Self

_LAST_UPDATED_KEY = "last_updated"
"""Dictionary key corresponding to a ``ParamData`` object's last updated time."""
_DATA_KEY = "data"
"""Dictionary key corresponding to a ``ParamData`` object's data."""

_param_classes: WeakValueDictionary[str, type[ParamData]] = WeakValueDictionary()
"""Dictionary of weak references to existing ``ParamData`` classes."""


def get_param_class(class_name: str) -> type[ParamData] | None:
    """Get a parameter class given its name, or ``None`` if the class does not exist."""
    return _param_classes[class_name] if class_name in _param_classes else None


class ParamData(ABC):
    """Abstract base class for all parameter data."""

    _parent: ParamData | None = None
    _last_updated: datetime

    def __init_subclass__(cls, /, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Add subclass to dictionary of ParamData classes
        _param_classes[cls.__name__] = cls

    def __init__(self) -> None:
        super().__setattr__("_last_updated", datetime.now(timezone.utc).astimezone())

    def _add_child(self, child: Any) -> None:
        """Add the given object as a child, if it is ``ParamData``."""
        if isinstance(child, ParamData):
            super(ParamData, child).__setattr__("_parent", self)

    def _remove_child(self, child: Any) -> None:
        """Remove the given object as a child, if it is ``ParamData``."""
        if isinstance(child, ParamData):
            super(ParamData, child).__setattr__("_parent", None)

    def _update_last_updated(self) -> None:
        """Update last updated for this object and its chain of parents."""
        # pylint: disable=protected-access,unused-private-member
        new_last_updated = datetime.now(timezone.utc).astimezone()
        current: ParamData | None = self

        # Continue up the chain of parents, stopping if we reach a last updated
        # timestamp that is more recent than the new one
        while current is not None and not (
            current._last_updated and current._last_updated >= new_last_updated
        ):
            super(ParamData, current).__setattr__("_last_updated", new_last_updated)
            current = current._parent

    @abstractmethod
    def _to_json(self) -> Any:
        """
        Convert the data stored in this object into a JSON serializable format, which
        will later be passed to ``self._data_from_json()`` to reconstruct this object.

        The last updated timestamp is handled separately and does not need to be saved
        here.

        Note that objects within a list or dictionary returned by this function do not
        need to be JSON serializable, since they will be processed recursively.
        """

    @classmethod
    @abstractmethod
    def _from_json(cls, json_data: Any) -> Self:
        """
        Construct a parameter data object from the given JSON data, usually created by
        ``json.loads()`` and originally constructed by ``self._data_to_json()``.

        The last updated timestamp is handled separately and does not need to be set
        here.
        """

    def to_dict(self) -> dict[str, Any]:
        """
        Return a dictionary representation of this parameter data object, which can be
        used to reconstruct the object by passing it to :py:meth:`from_dict`.
        """
        return {_LAST_UPDATED_KEY: self._last_updated, _DATA_KEY: self._to_json()}

    @classmethod
    def from_dict(cls, data_dict: dict[str, Any]) -> Self:
        """
        Construct a parameter data object from the given dictionary, usually created by
        ``json.loads()`` and originally constructed by :py:meth:`from_dict`.
        """
        param_data = cls._from_json(data_dict[_DATA_KEY])
        super().__setattr__(param_data, "_last_updated", data_dict[_LAST_UPDATED_KEY])
        return param_data

    @property
    def last_updated(self) -> datetime:
        """When any parameter within this parameter data was last updated."""
        return self._last_updated

    @property
    def parent(self) -> ParamData:
        """
        Parent of this parameter data. The parent is defined to be the
        :py:class:`ParamData` object that most recently had this object added as a
        child.

        Raises a ``ValueError`` if there is currently no parent, which can occur if the
        parent is still being initialized.
        """
        if self._parent is None:
            raise ValueError(
                f"'{type(self).__name__}' object has no parent, or its parent has not"
                " been initialized yet"
            )
        return self._parent

    @property
    def root(self) -> ParamData:
        """
        Root of this parameter data. The root is defined to be the first object with no
        parent when going up the chain of parents.
        """
        # pylint: disable=protected-access
        root = self
        while root._parent is not None:
            root = root._parent
        return root
