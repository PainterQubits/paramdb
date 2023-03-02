"""Mixins for parameter data, including parent and root mixins."""

from typing import TypeVar, Generic, cast
from paramdb._param_data import Struct


ST = TypeVar("ST", bound=Struct)


class ParentMixin(Generic[ST]):
    """
    Mixin that provides access to the parent structure by adding the `parent`
    property. Intended to be used with parameter data classes (e.g. subclasses of
    :py:class:`Struct` and :py:class:`Param`). For example::

        @dataclass
        class CustomStruct(ParentMixin[ParentStruct], Param):
            value: float

    The type parameter is used as the type of the returned parent. Note that if the
    parent actually has a different type, the type hint will be incorrect.
    """

    _initialized: bool
    _parent: Struct | None

    @property
    def parent(self) -> ST:
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
        return cast(ST, self._parent)


class RootMixin(Generic[ST]):
    """
    Mixin that provides access to the root structure by adding the `root` property,
    where the root structure is the first parent of this object that has no parent.
    Intended to be used with parameter data classes (e.g. subclasses of
    :py:class:`Struct` and :py:class:`Param`).

    The type parameter is used as the type of the returned root. Note that if the root
    actually has a different type, the type hint will be incorrect.
    """

    _initialized: bool
    _parent: Struct | None

    @property
    def root(self) -> ST:
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
        potential_root: RootMixin[ST] | Struct = self
        while potential_root._parent is not None:  # pylint: disable=protected-access
            potential_root = potential_root._parent  # pylint: disable=protected-access
        return cast(ST, potential_root)
