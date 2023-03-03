"""Parameter data collection classes for lists and dictionaries."""

from typing import TypeVar, Generic, SupportsIndex, Any, overload
from collections.abc import (
    Iterator,
    Collection,
    Iterable,
    Mapping,
    MutableSequence,
    MutableMapping,
)
from datetime import datetime
from typing_extensions import Self
from paramdb._param_data import ParamData


T = TypeVar("T")


# pylint: disable-next=abstract-method
class _ParamCollection(ParamData):
    """Base class for parameter data collections."""

    _contents: Collection[Any]

    def __len__(self) -> int:
        return len(self._contents)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._contents})"

    @property
    def last_updated(self) -> datetime | None:
        return self._get_last_updated(self._contents)


class ParamList(_ParamCollection, MutableSequence[T], Generic[T]):
    """Mutable sequence that is also parameter data."""

    _contents: list[T]

    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        self._contents = [] if iterable is None else list(iterable)
        if iterable is not None:
            for item in self._contents:
                self._add_child(item)

    @overload
    def __getitem__(self, index: SupportsIndex) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[T]:
        ...

    def __getitem__(self, index: Any) -> Any:
        return self._contents[index]

    @overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None:
        ...

    def __setitem__(self, index: Any, value: T | Iterable[T]) -> None:
        self._contents[index] = value
        if isinstance(value, Iterable):
            for item in value:
                self._add_child(item)
        else:
            self._add_child(value)

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        self._remove_child(self._contents[index])
        del self._contents[index]

    def insert(self, index: SupportsIndex, value: T) -> None:
        self._contents.insert(index, value)
        self._add_child(value)

    def to_dict(self) -> dict[str, list[T]]:
        return {"items": self._contents}

    @classmethod
    def from_dict(cls, json_dict: dict[str, list[T]]) -> Self:
        return cls(json_dict["items"])


class ParamDict(_ParamCollection, MutableMapping[str, T], Generic[T]):
    """Mutable mapping that is also parameter data."""

    _contents: dict[str, T]

    def __init__(self, mapping: Mapping[str, T] | None = None):
        # Use superclass __setattr__ to set actual attribute, not dictionary item
        super().__setattr__("_contents", {} if mapping is None else dict(mapping))
        if mapping is not None:
            for item in self._contents.values():
                self._add_child(item)

    def __getitem__(self, key: str) -> T:
        return self._contents[key]

    def __setitem__(self, key: str, value: T) -> None:
        self._contents[key] = value
        self._add_child(value)

    def __delitem__(self, key: str) -> None:
        self._remove_child(key)
        del self._contents[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._contents

    def __getattr__(self, key: str) -> T:
        # Enable accessing items via dot notation
        return self[key]

    def __setattr__(self, key: str, value: T) -> None:
        # Enable setting items via dot notation
        self[key] = value

    def to_dict(self) -> dict[str, T]:
        return self._contents

    @classmethod
    def from_dict(cls, json_dict: dict[str, T]) -> Self:
        return cls(json_dict)
