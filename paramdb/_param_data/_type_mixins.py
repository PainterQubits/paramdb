"""Type mixins for parameter data."""

from __future__ import annotations
from typing import TypeVar, Generic, Any, cast
from paramdb._param_data._param_data import ParamData

ParentT = TypeVar("ParentT", bound=ParamData[Any])
RootT = TypeVar("RootT", bound=ParamData[Any])


class ParentType(ParamData[Any], Generic[ParentT]):
    """
    Mixin for :py:class:`ParamData` that sets the type hint for
    :py:attr:`ParamData.parent` to type parameter ``ParentT``. For example::

        class CustomParam(ParentType[ParentParam], Param):
            ...

    Note that if the parent actually has a different type, the type hint will be
    incorrect.
    """

    @property
    def parent(self) -> ParentT:
        return cast(ParentT, super().parent)


class RootType(ParamData[Any], Generic[RootT]):
    """
    Mixin for :py:class:`ParamData` that sets the type hint for
    :py:attr:`ParamData.root` to type parameter ``RootT``. For example::

        class CustomParam(RootType[RootParam], Param):
            ...

    Note that if the root actually has a different type, the type hint will be
    incorrect.
    """

    @property
    def root(self) -> RootT:
        return cast(RootT, super().root)
