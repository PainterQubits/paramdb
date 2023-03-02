"""Mixins for parameter data, including parent and root mixins."""

from __future__ import annotations
from typing import TypeVar, Generic, Any, cast
from typing_extensions import Self
from paramdb._param_data import ParamData


PD = TypeVar("PD", bound=ParamData)


class _MixinBase:
    _initialized: bool
    _parent: ParamData | None
    _mixin_name: str

    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        if cls is _MixinBase or cls in _MixinBase.__subclasses__():
            raise TypeError(f"only subclasses of {cls.__name__} can be instantiated")
        if not issubclass(cls, ParamData):
            mixin_class = next(
                superclass
                for superclass in cls.mro()
                if superclass in _MixinBase.__subclasses__()
            )
            raise TypeError(
                f"'{cls.__name__}' uses {mixin_class.__name__} but is not a subclass of"
                f" {ParamData.__name__}, so it cannot be instantiated"
            )
        return super().__new__(cls)


class ParentMixin(_MixinBase, Generic[PD]):
    """
    Mixin that provides access to the parent structure by adding the :py:attr:`parent`
    property. Intended to be used with parameter data classes (e.g. subclasses of
    :py:class:`Struct` and :py:class:`Param`). For example::

        @dataclass
        class CustomParam(ParentMixin[ParentStruct], Param):
            value: float

    The type parameter ``PD`` must be a parameter data type and is used as the type of
    the returned parent. Note that if the parent actually has a different type, the type
    hint will be incorrect.
    """

    @property
    def parent(self) -> PD:
        """
        Parent of this parameter data, cast to the type `ParentMixin` was parameterized
        with. Note that if the parent actually has a different type, the return type
        will be incorrect.

        (If this parameter data is contained by multiple parents, this will return the
        most recently initialized parent.)
        """
        if not self._initialized:
            # This will occur if we try to access this object's parent within the
            # __init__ or __post_init__ functions, in which case the parent will not be
            # initialized yet. We throw an error since `_parent` will be inaccurate.
            raise ValueError(
                f"cannot access parent of '{self.__class__.__name__}' object before it"
                " is done initializing"
            )
        if self._parent is None:
            raise ValueError(f"'{self.__class__.__name__}' object has no parent")
        return cast(PD, self._parent)


class RootMixin(_MixinBase, Generic[PD]):
    """
    Mixin that provides access to the root structure by adding the :py:attr:`root`
    property, where the root structure is the first parent of this object that has no
    parent. Intended to be used with parameter data classes (e.g. subclasses of
    :py:class:`Struct` and :py:class:`Param`). For example::

        @dataclass
        class CustomParam(ParentMixin[RootStruct], Param):
            value: float

    The type parameter ``PD`` must be a parameter data type and is used as the type of
    the returned root. Note that if the root actually has a different type, the type
    hint will be incorrect.
    """

    @property
    def root(self) -> PD:
        """
        Root of this parameter data, cast to the type `RootMixin` was parameterized
        with. Note that if the root actually has a different type, the return type will
        be incorrect.

        (If this parameter data is contained by multiple parents, this will return the
        root of the most recently initialized parent.)
        """
        if not self._initialized:
            # This will occur if we try to access the root within the __init__ or
            # __post_init__ functions, in which case this object's parent will not be
            # initialized yet. We throw an error since `_parent` will be inaccurate.
            raise ValueError(
                f"cannot access root of '{self.__class__.__name__}' object before it is"
                " done initializing"
            )
        potential_root: RootMixin[PD] | ParamData = self
        while potential_root._parent is not None:  # pylint: disable=protected-access
            potential_root = potential_root._parent  # pylint: disable=protected-access
        return cast(PD, potential_root)
