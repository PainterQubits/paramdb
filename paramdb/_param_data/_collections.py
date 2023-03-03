"""Parameter data collection classes for lists and dictionaries."""

from typing import TypeVar, Generic, SupportsIndex, Any, overload
from collections.abc import Iterator, Iterable, Mapping, MutableSequence, MutableMapping
from datetime import datetime
from typing_extensions import Self
from paramdb._param_data import ParamData


T = TypeVar("T")


class ParamList(ParamData, MutableSequence[T], Generic[T]):
    """Mutable sequence that is also parameter data."""

    _list: list[T]

    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        if iterable is None:
            self._list = []
        else:
            self._list = list(iterable)
            for item in self._list:
                self._add_child(item)

    def __len__(self) -> int:
        return len(self._list)

    @overload
    def __getitem__(self, index: SupportsIndex) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[T]:
        ...

    def __getitem__(self, index: Any) -> Any:
        return self._list[index]

    @overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None:
        ...

    def __setitem__(self, index: Any, value: T | Iterable[T]) -> None:
        self._list[index] = value
        if isinstance(value, Iterable):
            for item in value:
                self._add_child(item)
        else:
            self._add_child(value)

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        self._remove_child(self._list[index])
        del self._list[index]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._list})"

    def insert(self, index: SupportsIndex, value: T) -> None:
        self._list.insert(index, value)
        self._add_child(value)

    @property
    def last_updated(self) -> datetime | None:
        return self._get_last_updated(self._list)

    def to_dict(self) -> dict[str, Any]:
        return {"items": self._list}

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Self:
        return cls(json_dict["items"])


class ParamDict(ParamData, MutableMapping[str, T], Generic[T]):
    """Mutable mapping that is also parameter data."""

    _dict: dict[str, T]

    def __init__(self, mapping: Mapping[str, T] | None = None):
        if mapping is None:
            self._dict = {}
        else:
            self._dict = dict(mapping)
            for item in self._dict.values():
                self._add_child(item)

    def __len__(self) -> int:
        return len(self._dict)

    def __getitem__(self, key: str) -> T:
        return self._dict[key]

    def __setitem__(self, key: str, value: T) -> None:
        self._dict[key] = value
        self._add_child(value)

    def __delitem__(self, key: str) -> None:
        self._remove_child(key)
        del self._dict[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._dict

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._dict})"

    @property
    def last_updated(self) -> datetime | None:
        return self._get_last_updated(self._dict)

    def to_dict(self) -> dict[str, Any]:
        return self._dict

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Self:
        return cls(json_dict)
