"""Parameter data collection classes for lists and dictionaries."""

from typing import TypeVar, Generic, Iterable, SupportsIndex, Any, overload
from paramdb._param_data import ParamData

T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")


class ParamList(ParamData, list[T], Generic[T]):
    @overload
    def __setitem__(self, key: SupportsIndex, value: T) -> None:
        ...

    @overload
    def __setitem__(self, key: slice, value: Iterable[T]) -> None:
        ...

    def __setitem__(self, key: Any, value: T | Iterable[T]) -> None:
        list.__setitem__(self, key, value)


class ParamDict(ParamData, dict[KT, VT], Generic[KT, VT]):
    pass
