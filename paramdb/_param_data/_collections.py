"""Parameter data collection classes."""

from __future__ import annotations
from typing import Union, TypeVar, Generic, SupportsIndex, Any, cast, overload
from collections.abc import (
    Iterator,
    Collection,
    Iterable,
    Mapping,
    MutableSequence,
    MutableMapping,
)
from typing_extensions import Self
from paramdb._param_data._param_data import ParamData, _ParamWrapper

T = TypeVar("T")
_ChildNameT = TypeVar("_ChildNameT", str, int)
_CollectionT = TypeVar("_CollectionT", bound=Collection[Any])


# pylint: disable-next=abstract-method
class _ParamCollection(ParamData[_ChildNameT], Generic[_ChildNameT, _CollectionT]):
    """Base class for parameter collections."""

    _contents: _CollectionT

    def __len__(self) -> int:
        return len(self._contents)

    def __eq__(self, other: Any) -> bool:
        # Equal if they have are of the same class and their contents are equal
        return type(other) is type(self) and self._contents == other._contents

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._contents})"

    def _to_json(self) -> _CollectionT:
        return self._contents

    def _get_wrapped_child(self, child_name: _ChildNameT) -> ParamData[Any]:
        # If a TypeError, IndexError, or KeyError occurs from _contents, raise the
        # superclass ValueError from the _contents exception
        try:
            return cast(
                ParamData[Any], self._contents[child_name]  # type: ignore[index]
            )
        except (TypeError, IndexError, KeyError) as contents_exc:
            try:
                return super()._get_wrapped_child(child_name)  # type: ignore[arg-type]
            except ValueError as super_exc:
                raise super_exc from contents_exc

    @classmethod
    def _from_json(cls, json_data: _CollectionT) -> Self:
        # Set contents directly since __init__() will contain child wrapping logic
        new_param_collection = cls()
        new_param_collection._contents = json_data
        return new_param_collection


class ParamList(
    _ParamCollection[int, list[Union[T, _ParamWrapper[T]]]],
    MutableSequence[T],
    Generic[T],
):
    """
    Subclass of :py:class:`ParamData` and ``MutableSequence``.

    Mutable sequence that is also parameter data. It can be initialized from any
    iterable (like builtin ``list``).
    """

    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        super().__init__()
        initial_contents = iterable or []
        self._contents = [self._wrap_child(item) for item in initial_contents]
        for item in initial_contents:
            self._add_child(item)

    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> Self: ...

    def __getitem__(self, index: SupportsIndex | slice) -> T | Self:
        if isinstance(index, slice):
            return type(self)(
                [
                    self._unwrap_child(wrapped_child)
                    for wrapped_child in self._contents[index]
                ]
            )
        return self._unwrap_child(self._contents[index])

    @overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...

    def __setitem__(self, index: SupportsIndex | slice, value: Any) -> None:
        if isinstance(index, slice):
            old_values = self._contents[index]
            self._contents[index] = [self._wrap_child(item) for item in value]
            for old_item in old_values:
                self._remove_child(old_item)
            for item in value:
                self._add_child(item)
        else:
            old_value = self._contents[index]
            self._contents[index] = self._wrap_child(value)
            self._remove_child(old_value)
            self._add_child(value)

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        old_value = self._contents[index]
        del self._contents[index]
        if isinstance(index, slice) and isinstance(old_value, list):
            for old_item in old_value:
                self._remove_child(old_item)
        else:
            self._remove_child(old_value)

    def insert(self, index: SupportsIndex, value: T) -> None:
        self._contents.insert(index, self._wrap_child(value))
        self._add_child(value)

    @classmethod
    def _from_json(cls, json_data: list[T | _ParamWrapper[T]]) -> Self:

        new_obj = cls()
        new_obj._contents = json_data
        return new_obj


class ParamDict(
    _ParamCollection[str, dict[str, Union[T, _ParamWrapper[T]]]],
    MutableMapping[str, T],
    Generic[T],
):
    """
    Subclass of :py:class:`ParamData` and ``MutableMapping``.

    Mutable mapping that is also parameter data. It can be initialized from any mapping
    or using keyword arguments (like builtin ``dict``).

    Keys that do not begin with an underscore can be set via dot notation. Keys, values,
    and items are returned as dict_keys, dict_values, and dict_items objects.
    """

    def __init__(self, mapping: Mapping[str, T] | None = None, /, **kwargs: T):
        super().__init__()
        initial_contents = {**(mapping or {}), **kwargs}
        self._contents = {
            key: self._wrap_child(value) for key, value in initial_contents.items()
        }
        for value in initial_contents.values():
            self._add_child(value)

    def __dir__(self) -> Iterable[str]:
        # Return keys that are not attribute names (i.e. do not pass self._is_attribute)
        # in __dir__() so they are suggested by interactive prompts like IPython.
        return [
            *super().__dir__(),
            *filter(lambda key: not self._is_attribute(key), self._contents.keys()),
        ]

    def __getitem__(self, key: str) -> T:
        return self._unwrap_child(self._contents[key])

    def __setitem__(self, key: str, value: T) -> None:
        old_value = self._contents[key] if key in self._contents else None
        self._contents[key] = self._wrap_child(value)
        self._remove_child(old_value)
        self._add_child(value)

    def __delitem__(self, key: str) -> None:
        old_value = self._contents[key] if key in self._contents else None
        del self._contents[key]
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
