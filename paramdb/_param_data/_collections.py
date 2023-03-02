"""Parameter data collection classes for lists and dictionaries."""

from typing import TypeVar, Generic
from paramdb._param_data import ParamData

T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")


class ParamList(ParamData, list[T], Generic[T]):
    pass


class ParamDict(ParamData, dict[KT, VT], Generic[KT, VT]):
    pass
