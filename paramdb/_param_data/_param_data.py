"""Base class for all parameter data."""

from __future__ import annotations
from typing import Any
from collections.abc import Iterable, Mapping
from abc import ABC, abstractmethod
from weakref import WeakValueDictionary
from datetime import datetime
from typing_extensions import Self

# Stores weak references to existing parameter classes
_param_classes: WeakValueDictionary[str, type[ParamData]] = WeakValueDictionary()


def get_param_class(class_name: str) -> type[ParamData] | None:
    """Get a parameter class given its name, or ``None`` if the class does not exist."""
    return _param_classes[class_name] if class_name in _param_classes else None


class ParamData(ABC):
    """Abstract base class for all parameter data."""

    # Most recently initialized structure that contains this parameter data
    _parent: ParamData | None = None

    def __init_subclass__(cls) -> None:
        # Add subclass to dictionary of parameter data classes
        _param_classes[cls.__name__] = cls
        super().__init_subclass__()

    def _add_child(self, child: Any) -> None:
        """Add the given object as a child, if it is ``ParamData``."""

        if isinstance(child, ParamData):
            # Use ParamData __setattr__ to avoid updating _last_updated
            ParamData.__setattr__(child, "_parent", self)

    def _remove_child(self, child: Any) -> None:
        """Remove the given object as a child, if it is ``ParamData``."""

        if isinstance(child, ParamData):
            # Use ParamData __setattr__ to avoid updating _last_updated
            ParamData.__setattr__(child, "_parent", None)

    def _get_last_updated(self, obj: Any) -> datetime | None:
        """
        Get the last updated time from a ``ParamData`` object, or recursively search
        through any iterable type to find the latest last updated time.
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
    @abstractmethod
    def last_updated(self) -> datetime | None:
        """
        When any parameter within this parameter data were last updated, or ``None`` if
        this object contains no parameters.
        """

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
        root = self
        while root._parent is not None:  # pylint: disable=protected-access
            root = root._parent  # pylint: disable=protected-access
        return root

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
