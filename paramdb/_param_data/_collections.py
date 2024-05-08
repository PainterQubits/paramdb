"""Parameter data collection classes."""

from __future__ import annotations
from typing import TypeVar, Generic, SupportsIndex, Any, overload
from collections.abc import (
    Iterator,
    Collection,
    Iterable,
    Mapping,
    MutableSequence,
    MutableMapping,
    KeysView,
    ValuesView,
    ItemsView,
)
from abc import abstractmethod
from typing_extensions import Self
from paramdb._param_data._param_data import ParamData

T = TypeVar("T")
_CollectionT = TypeVar("_CollectionT", bound=Collection[Any])


# pylint: disable-next=abstract-method
class _ParamCollection(ParamData, Generic[_CollectionT]):
    """Base class for parameter collections."""

    _contents: _CollectionT

    def __len__(self) -> int:
        return len(self._contents)

    def __eq__(self, other: Any) -> bool:
        # Equal if they have are of the same class and their contents are equal
        return (
            isinstance(other, _ParamCollection)
            and type(other) is type(self)
            and self._contents == other._contents
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._contents})"

    def _to_json(self) -> _CollectionT:
        return self._contents

    @classmethod
    @abstractmethod
    def _from_json(cls, json_data: _CollectionT) -> Self: ...


class ParamList(_ParamCollection[list[T]], MutableSequence[T], Generic[T]):
    """
    Subclass of :py:class:`ParamData` and ``MutableSequence``.

    Mutable sequence that is also parameter data. It can be initialized from any
    iterable (like builtin ``list``).
    """

    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        super().__init__()
        self._contents = [] if iterable is None else list(iterable)
        if iterable is not None:
            for item in self._contents:
                self._add_child(item)

    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> list[T]: ...

    def __getitem__(self, index: Any) -> Any:
        return self._contents[index]

    @overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...

    def __setitem__(self, index: SupportsIndex | slice, value: Any) -> None:
        old_value: Any = self._contents[index]
        self._contents[index] = value
        self._update_last_updated()
        if isinstance(index, slice):
            for item in old_value:
                self._remove_child(item)
            for item in value:
                self._add_child(item)
        else:
            self._remove_child(old_value)
            self._add_child(value)

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        old_value = self._contents[index]
        del self._contents[index]
        self._update_last_updated()
        self._remove_child(old_value)

    def insert(self, index: SupportsIndex, value: T) -> None:
        self._contents.insert(index, value)
        self._update_last_updated()
        self._add_child(value)

    @classmethod
    def _from_json(cls, json_data: list[T]) -> Self:
        return cls(json_data)


class ParamDict(_ParamCollection[dict[str, T]], MutableMapping[str, T], Generic[T]):
    """
    Subclass of :py:class:`ParamData` and ``MutableMapping``.

    Mutable mapping that is also parameter data. It can be initialized from any mapping
    or using keyword arguments (like builtin ``dict``).

    Keys that do not begin with an underscore can be set via dot notation. Keys, values,
    and items are returned as dict_keys, dict_values, and dict_items objects.
    """

    def __init__(self, mapping: Mapping[str, T] | None = None, /, **kwargs: T):
        super().__init__()
        self._contents = ({} if mapping is None else dict(mapping)) | kwargs
        for item in self._contents.values():
            self._add_child(item)

    def __dir__(self) -> Iterable[str]:
        # Return keys that are not attribute names (i.e. do not pass self._is_attribute)
        # in __dir__() so they are suggested by interactive prompts like IPython.
        return [
            *super().__dir__(),
            *filter(lambda key: not self._is_attribute(key), self._contents.keys()),
        ]

    def __getitem__(self, key: str) -> T:
        return self._contents[key]

    def __setitem__(self, key: str, value: T) -> None:
        old_value = self._contents[key] if key in self._contents else None
        self._contents[key] = value
        self._update_last_updated()
        self._remove_child(old_value)
        self._add_child(value)

    def __delitem__(self, key: str) -> None:
        old_value = self._contents[key] if key in self._contents else None
        del self._contents[key]
        self._update_last_updated()
        self._remove_child(old_value)

    def __iter__(self) -> Iterator[str]:
        yield from self._contents

    def __getattr__(self, name: str) -> T:
        # Enable accessing items via dot notation
        if self._is_attribute(name):
            # It is important to raise an attribute error rather than a key error for
            # names considered to be attributes. For example, this allows deepcopy to
            # work properly.
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        return self[name]

    def __setattr__(self, name: str, value: T) -> None:
        # Enable setting items via dot notation
        if self._is_attribute(name):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __delattr__(self, name: str) -> None:
        # Enable deleting items via dot notation
        if self._is_attribute(name):
            super().__delattr__(name)
        else:
            del self[name]

    def _is_attribute(self, name: str) -> bool:
        """
        Names beginning with underscores are considered to be attributes when accessed
        via dot notation. This is both to allow internal Python variables to be set
        (i.e. dunder variables), and to allow for true attributes to be used if needed.
        """
        return len(name) > 0 and name[0] == "_"

    def keys(self) -> KeysView[str]:
        # Use dict_keys so keys print nicely
        return self._contents.keys()

    def values(self) -> ValuesView[T]:
        # Use dict_values so values print nicely
        return self._contents.values()

    def items(self) -> ItemsView[str, T]:
        # Use dict_items so items print nicely
        return self._contents.items()

    @classmethod
    def _from_json(cls, json_data: dict[str, T]) -> Self:
        return cls(json_data)
