"""Parameter data primitive classes."""

from __future__ import annotations
from typing import TypeVar, Generic, Any
from abc import abstractmethod
from typing_extensions import Self
from paramdb._param_data._param_data import ParamData

_T = TypeVar("_T")


class _ParamPrimitive(ParamData, Generic[_T]):
    """Base class for parameter primitives."""

    @property
    @abstractmethod
    def value(self) -> _T:
        """Primitive value stored by this parameter primitive."""

    def _to_json(self) -> _T:
        return self.value

    @classmethod
    def _from_json(cls, json_data: _T) -> Self:
        return cls(json_data)  # type: ignore

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value!r})"


def __init__(self: _ParamPrimitive[Any], *_args: Any) -> None:
    # Allow extra arguments to be passed to __init__() to allow for extra arguments in
    # __new__() from base classes int, float, and str.
    super(_ParamPrimitive, self).__init__()


# We assign __init__() outside of the class so that static type checkers and suggestions
# defer to the signature of __new__() from base classes int, float, and str.
_ParamPrimitive.__init__ = __init__  # type: ignore


class ParamInt(int, _ParamPrimitive[int]):
    """
    Subclass of :py:class:`ParamData` and ``int``.

    Parameter data integer. All ``int`` functions and operations are available; however,
    note that ordinary ``int`` objects will be returned.
    """

    @property
    def value(self) -> int:
        return int(self)

    def __repr__(self) -> str:
        # Override __repr__() from base class int
        return _ParamPrimitive.__repr__(self)


class ParamBool(ParamInt):
    """
    Subclass of :py:class:`ParamInt`.

    Parameter data boolean. All ``int`` and ``bool`` funtions and operations are
    available; however, note that ordinary ``int`` objects (``0`` or ``1``) will be
    returned.
    """

    def __new__(cls, o: object = False) -> Self:
        # Convert any object to a boolean to emulate bool()
        return super().__new__(cls, bool(o))

    @property
    def value(self) -> bool:
        return bool(self)


class ParamFloat(float, _ParamPrimitive[float]):
    """
    Subclass of :py:class:`ParamData` and ``float``.

    Parameter data float. All ``float`` funtions and operations are available; however,
    note that ordinary ``float`` objects will be returned.
    """

    @property
    def value(self) -> float:
        return float(self)

    def __repr__(self) -> str:
        # Override __repr__() from base class float
        return _ParamPrimitive.__repr__(self)


class ParamStr(str, _ParamPrimitive[str]):
    """
    Subclass of :py:class:`ParamData` and ``str``.

    Parameter data string. All ``str`` funtions and operations are available; however,
    note that ordinary ``str`` objects will be returned.
    """

    @property
    def value(self) -> str:
        return str(self)

    def __repr__(self) -> str:
        # Override __repr__() from base class str
        return _ParamPrimitive.__repr__(self)


class ParamNone(_ParamPrimitive[None]):
    """
    Subclass of :py:class:`ParamData`.

    Parameter data ``None``. Just like ``None``, its truth value is false.
    """

    @property
    def value(self) -> None:
        return None

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ParamNone)

    def __repr__(self) -> str:
        # Show empty parentheses
        return f"{type(self).__name__}()"
