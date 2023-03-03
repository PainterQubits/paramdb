"""Type mixins for parameter data."""

from __future__ import annotations
from typing import TypeVar, Generic, cast
from paramdb._param_data import ParamData


PT = TypeVar("PT", bound=ParamData)


# pylint: disable-next=abstract-method
class ParentType(ParamData, Generic[PT]):
    """
    Mixin for :py:class:`ParamData` that casts :py:attr:`parent` to type parameter
    ``PT``. Note that if the parent actually has a different type, the type hint will be
    incorrect.
    """

    @property
    def parent(self) -> PT:
        return cast(PT, super().parent)


# pylint: disable-next=abstract-method
class RootType(ParamData, Generic[PT]):
    """
    Mixin for :py:class:`ParamData` that casts :py:attr:`root` to type parameter ``PT``.
    Note that if the root actually has a different type, the type hint will be
    incorrect.
    """

    @property
    def root(self) -> PT:
        return cast(PT, super().root)
