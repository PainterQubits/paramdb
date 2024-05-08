"""Parameter data primitive classes."""

from __future__ import annotations
from typing import (
    Union,
    Protocol,
    TypeVar,
    Generic,
    SupportsInt,
    SupportsFloat,
    SupportsIndex,
    Any,
    overload,
)
from abc import abstractmethod
from typing_extensions import Self, Buffer
from paramdb._param_data._param_data import ParamData

_T = TypeVar("_T")


# Based on https://github.com/python/typeshed/blob/main/stdlib/_typeshed/__init__.pyi
class _SupportsTrunc(Protocol):
    def __trunc__(self) -> int: ...


# Based on https://github.com/python/typeshed/blob/main/stdlib/_typeshed/__init__.pyi
ConvertibleToInt = Union[str, Buffer, SupportsInt, SupportsIndex, _SupportsTrunc]
ConvertibleToFloat = Union[str, Buffer, SupportsFloat, SupportsIndex]


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
        return cls(json_data)  # type: ignore # pylint: disable=too-many-function-args

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value!r})"


class ParamInt(int, _ParamPrimitive[int]):
    """
    Subclass of :py:class:`ParamData` and ``int``.

    Parameter data integer. All ``int`` methods and operations are available; however,
    note that ordinary ``int`` objects will be returned.
    """

    # Based on https://github.com/python/typeshed/blob/main/stdlib/builtins.pyi
    @overload
    def __init__(self, x: ConvertibleToInt = 0, /): ...

    # Based on https://github.com/python/typeshed/blob/main/stdlib/builtins.pyi
    @overload
    def __init__(self, x: str | bytes | bytearray, /, base: SupportsIndex = 10): ...

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        super().__init__()

    @property
    def value(self) -> int:
        return int(self)

    def __repr__(self) -> str:
        # Override __repr__() from base class int
        return _ParamPrimitive.__repr__(self)


class ParamBool(ParamInt):
    """
    Subclass of :py:class:`ParamInt`.

    Parameter data boolean. All ``int`` and ``bool`` methods and operations are
    available; however, note that ordinary ``int`` objects (``0`` or ``1``) will be
    returned.
    """

    # Based on https://github.com/python/typeshed/blob/main/stdlib/builtins.pyi
    def __new__(cls, x: object = False, /) -> Self:
        # Convert any object to a boolean to emulate bool()
        return super().__new__(cls, bool(x))

    # Based on https://github.com/python/typeshed/blob/main/stdlib/builtins.pyi
    # pylint: disable-next=unused-argument
    def __init__(self, o: object = False, /) -> None:
        super().__init__()

    @property
    def value(self) -> bool:
        return bool(self)


class ParamFloat(float, _ParamPrimitive[float]):
    """
    Subclass of :py:class:`ParamData` and ``float``.

    Parameter data float. All ``float`` methods and operations are available; however,
    note that ordinary ``float`` objects will be returned.
    """

    # Based on https://github.com/python/typeshed/blob/main/stdlib/builtins.pyi
    # pylint: disable-next=unused-argument
    def __init__(self, x: ConvertibleToFloat = 0.0, /) -> None:
        super().__init__()

    @property
    def value(self) -> float:
        return float(self)

    def __repr__(self) -> str:
        # Override __repr__() from base class float
        return _ParamPrimitive.__repr__(self)


class ParamStr(str, _ParamPrimitive[str]):
    """
    Subclass of :py:class:`ParamData` and ``str``.

    Parameter data string. All ``str`` methods and operations are available; however,
    note that ordinary ``str`` objects will be returned.
    """

    # Based on https://github.com/python/typeshed/blob/main/stdlib/builtins.pyi
    @overload
    def __init__(
        self,
        object: object = "",  # pylint: disable=redefined-builtin
        /,
    ) -> None: ...

    # Based on https://github.com/python/typeshed/blob/main/stdlib/builtins.pyi
    @overload
    def __init__(
        self,
        object: Buffer = b"",  # pylint: disable=redefined-builtin
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> None: ...

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        super().__init__()

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

    @classmethod
    def _from_json(cls, json_data: None) -> Self:
        return cls()

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return other is None or isinstance(other, ParamNone)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        # Show empty parentheses
        return f"{type(self).__name__}()"
