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
from copy import copy
from typing_extensions import Self
from paramdb._param_data._param_data import ParamData, _ParamWrapper

ItemT = TypeVar("ItemT")
_ChildNameT = TypeVar("_ChildNameT", str, int)
_CollectionT = TypeVar("_CollectionT", bound=Union[list[Any], dict[str, Any]])


# pylint: disable-next=abstract-method
class _ParamCollection(
    ParamData[_ChildNameT], Collection[Any], Generic[_ChildNameT, _CollectionT]
):
    """Base class for parameter collections."""

    _contents: _CollectionT

    def __len__(self) -> int:
        return len(self._contents)

    def __repr__(self) -> str:
        # Show contents as self converted to an ordinary list or dict to hide internal
        # _ParamWrapper objects
        return f"{type(self).__name__}({type(self._contents)(self)})"

    def to_json(self) -> _CollectionT:
        return self._contents

    def _get_wrapped_child(self, child_name: _ChildNameT) -> ParamData[Any]:
        # If a TypeError, IndexError, or KeyError occurs from _contents, raise the
        # superclass ValueError from the _contents exception
        try:
            return cast(
                ParamData[Any],
                self._contents[child_name],  # type: ignore[index,call-overload]
            )
        except (TypeError, IndexError, KeyError) as contents_exc:
            try:
                return super()._get_wrapped_child(child_name)  # type: ignore[arg-type]
            except ValueError as super_exc:
                raise super_exc from contents_exc


class ParamList(
    _ParamCollection[int, list[Union[ItemT, _ParamWrapper[ItemT]]]],
    MutableSequence[ItemT],
    Generic[ItemT],
):
    """
    Subclass of :py:class:`ParamData` and ``MutableSequence``.

    Mutable sequence that is also parameter data. It can be initialized from any
    iterable (like builtin ``list``).
    """

    def __init__(self, iterable: Iterable[ItemT] | None = None) -> None:
        super().__init__()
        initial_contents = iterable or []
        wrapped_initial_contents = [self._wrap_child(item) for item in initial_contents]
        for wrapped_item in wrapped_initial_contents:
            self._add_child(wrapped_item)
        self._contents = wrapped_initial_contents

    def __eq__(self, other: Any) -> bool:
        # Equal if the other object is also a ParamList and has the same contents
        return isinstance(other, ParamList) and self._contents == other._contents

    @overload
    def __getitem__(self, index: SupportsIndex) -> ItemT: ...

    @overload
    def __getitem__(self, index: slice) -> Self: ...

    def __getitem__(self, index: SupportsIndex | slice) -> ItemT | Self:
        if isinstance(index, slice):
            # The slice has the same last updated time and item objects as the original
            self_copy = copy(self)
            self_copy._contents = self._contents[index]
            return self_copy
        return self._unwrap_child(self._contents[index])

    @overload
    def __setitem__(self, index: SupportsIndex, value: ItemT) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[ItemT]) -> None: ...

    def __setitem__(self, index: SupportsIndex | slice, value: Any) -> None:
        if isinstance(index, slice):
            old_wrapped_values = self._contents[index]
            wrapped_values = [self._wrap_child(item) for item in value]
            self._contents[index] = wrapped_values
            for old_wrapped_item in old_wrapped_values:
                self._remove_child(old_wrapped_item)
            for wrapped_item in wrapped_values:
                self._add_child(wrapped_item)
        else:
            old_wrapped_value = self._contents[index]
            wrapped_value = self._wrap_child(value)
            self._contents[index] = wrapped_value
            self._remove_child(old_wrapped_value)
            self._add_child(wrapped_value)

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        old_wrapped_value = self._contents[index]
        del self._contents[index]
        if isinstance(index, slice) and isinstance(old_wrapped_value, list):
            for old_wrapped_item in old_wrapped_value:
                self._remove_child(old_wrapped_item)
        else:
            self._remove_child(old_wrapped_value)

    def insert(self, index: SupportsIndex, value: ItemT) -> None:
        wrapped_value = self._wrap_child(value)
        self._contents.insert(index, wrapped_value)
        self._add_child(wrapped_value)


class ParamDict(
    _ParamCollection[str, dict[str, Union[ItemT, _ParamWrapper[ItemT]]]],
    MutableMapping[str, ItemT],
    Generic[ItemT],
):
    """
    Subclass of :py:class:`ParamData` and ``MutableMapping``.

    Mutable mapping that is also parameter data. It can be initialized from any mapping
    or using keyword arguments (like builtin ``dict``).

    Keys that do not refer to existing attributes or class type hints can be gotten,
    set, and deleted via dot notation.
    """

    def __init__(self, mapping: Mapping[str, ItemT] | None = None, /, **kwargs: ItemT):
        super().__init__()
        initial_contents = {**(mapping or {}), **kwargs}
        wrapped_initial_contents = {
            key: self._wrap_child(value) for key, value in initial_contents.items()
        }
        self._contents = wrapped_initial_contents
        for wrapped_value in wrapped_initial_contents.values():
            self._add_child(wrapped_value)

    def __eq__(self, other: Any) -> bool:
        # Equal if the other object is also a ParamDict and has the same contents
        return isinstance(other, ParamDict) and self._contents == other._contents

    def __dir__(self) -> Iterable[str]:
        # In addition to the default __dir__(), include dictionary keys so they are
        # suggested for dot notation by interactive prompts like IPython.
        super_dir = super().__dir__()
        return [
            *super_dir,
            *filter(lambda key: key not in super_dir, self.keys()),
        ]

    def __getitem__(self, key: str) -> ItemT:
        return self._unwrap_child(self._contents[key])

    def __setitem__(self, key: str, value: ItemT) -> None:
        old_wrapped_value = self._contents[key] if key in self._contents else None
        wrapped_value = self._wrap_child(value)
        self._contents[key] = wrapped_value
        self._remove_child(old_wrapped_value)
        self._add_child(wrapped_value)

    def __delitem__(self, key: str) -> None:
        old_wrapped_value = self._contents[key] if key in self._contents else None
        del self._contents[key]
        self._remove_child(old_wrapped_value)

    def __iter__(self) -> Iterator[str]:
        yield from self._contents

    def __getattr__(self, name: str) -> ItemT:
        # Enable accessing items via dot notation
        if self._is_attribute(name) or name not in self:
            # If the name corresponds to an attribute or is not in the dictionary, we
            # should raise the default AttributeError rather than a KeyError, since this
            # is the expected behavior of __getattr__(). For example, this allows
            # getattr() and hasattr() to work properly.
            self.__getattribute__(name)  # Raises the default AttributeError
        return self[name]

    def __setattr__(self, name: str, value: ItemT) -> None:
        # Enable setting items via dot notation
        if self._is_attribute(name):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __delattr__(self, name: str) -> None:
        # Enable deleting items via dot notation
        if self._is_attribute(name) or name not in self:
            super().__delattr__(name)
        else:
            del self[name]

    def _is_attribute(self, name: str) -> bool:
        """
        If the given name matches an existing attribute, has a corresponding class type
        hint, or is a dunder name (e.g. __init__), treat it as the name of an attribute.
        """
        try:
            self.__getattribute__(name)  # pylint: disable=unnecessary-dunder-call
            existing_attribute = True
        except AttributeError:
            existing_attribute = False
        class_annotations: dict[str, Any] = {}
        for cls in type(self).mro():
            class_annotations |= getattr(cls, "__annotations__", {})
        dunder = name.startswith("__") and name.endswith("__")
        return existing_attribute or name in class_annotations or dunder
