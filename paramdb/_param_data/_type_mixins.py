"""Type mixins for parameter data."""

from __future__ import annotations
from typing import TypeVar, Generic, cast
from paramdb._param_data._param_data import ParamData

PT = TypeVar("PT", bound=ParamData)


class ParentType(ParamData, Generic[PT]):
    """
    Mixin for :py:class:`ParamData` that sets the type hint for
    :py:attr:`ParamData.parent` to type parameter ``PT``. For example::

        class CustomParam(ParentType[ParentParam], Param):
            ...

    Note that if the parent actually has a different type, the type hint will be
    incorrect.
    """

    @property
    def parent(self) -> PT:
        return cast(PT, super().parent)


class RootType(ParamData, Generic[PT]):
    """
    Mixin for :py:class:`ParamData` that sets the type hint for
    :py:attr:`ParamData.root` to type parameter ``PT``. For example::

        class CustomParam(RootType[RootParam], Param):
            ...

    Note that if the root actually has a different type, the type hint will be
    incorrect.
    """

    @property
    def root(self) -> PT:
        return cast(PT, super().root)
