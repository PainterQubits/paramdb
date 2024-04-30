"""Parameter data primitive classes."""

from __future__ import annotations
from typing import (
    Union,
    Literal,
    Callable,
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
from functools import wraps
from datetime import datetime, tzinfo
from typing_extensions import Self, Buffer
from paramdb._param_data._param_data import ParamData

try:
    from astropy.units import Quantity  # type: ignore
    import numpy as np
    from numpy.typing import DTypeLike

    _ASTROPY_INSTALLED = True
except ImportError:
    _ASTROPY_INSTALLED = False


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
        return isinstance(other, ParamNone)

    def __repr__(self) -> str:
        # Show empty parentheses
        return f"{type(self).__name__}()"


class ParamDatetime(datetime, _ParamPrimitive[datetime]):
    """
    Subclass of :py:class:`ParamData` and ``datetime.datetime``.

    Parameter data datetime. All ``datetime`` methods and operations are available.
    """

    # Based on https://github.com/python/typeshed/blob/main/stdlib/datetime.pyi
    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        year: SupportsIndex,
        month: SupportsIndex,
        day: SupportsIndex,
        hour: SupportsIndex = 0,
        minute: SupportsIndex = 0,
        second: SupportsIndex = 0,
        microsecond: SupportsIndex = 0,
        tzinfo: tzinfo | None = None,  # pylint: disable=redefined-outer-name
        *,
        fold: int = 0,
    ) -> None:
        # pylint: disable=unused-argument
        super().__init__()

    @property
    def value(self) -> datetime:
        return datetime(
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
            self.microsecond,
            self.tzinfo,
            fold=self.fold,
        )


if _ASTROPY_INSTALLED:

    def _wrap_update_last_updated(method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Wrap the given method inherited from ``Quantity``, updating the last updated
        time when it is called.
        """

        @wraps(method)
        def wrapped_method(self: Any, *args: Any, **kwargs: Any) -> Any:
            result = method(self, *args, **kwargs)
            if result is not NotImplemented:
                # Only update last updated time if the method succeeded and, in the case
                # of an operator, did not return NotImplemented
                # pylint: disable-next=protected-access
                _ParamPrimitive._update_last_updated(self)
            return result

        return wrapped_method

    class ParamQuantity(Quantity, _ParamPrimitive[Quantity]):  # type: ignore
        """
        Subclass of :py:class:`ParamData` and ``astropy.units.Quantity``. Only available
        if Astropy is installed.

        Parameter data Astropy Quantity. All ``Quantity`` methods and operations are
        available.
        """

        # Based on the signature of Quantity.__new__()
        # pylint: disable-next=too-many-arguments
        def __init__(
            self,
            value: Any,
            unit: Any | None = None,
            dtype: DTypeLike = np.inexact,
            copy: bool = True,
            order: Literal["C", "F", "A", "K"] | None = None,
            subok: bool = False,
            ndmin: int = 0,
        ) -> None:
            # pylint: disable=unused-argument
            super(_ParamPrimitive, self).__init__()

        def _new_view(self, *args: Any, **kwargs: Any) -> Any:
            view = super()._new_view(*args, **kwargs)
            super(_ParamPrimitive, view).__init__()
            return view

        # Wrap in-place operators to update last updated
        __iadd__ = _wrap_update_last_updated(Quantity.__iadd__)
        __isub__ = _wrap_update_last_updated(Quantity.__isub__)
        __imul__ = _wrap_update_last_updated(Quantity.__imul__)
        __itruediv__ = _wrap_update_last_updated(Quantity.__itruediv__)
        __ifloordiv__ = _wrap_update_last_updated(Quantity.__ifloordiv__)
        __ipow__ = _wrap_update_last_updated(Quantity.__ipow__)
        __imod__ = _wrap_update_last_updated(Quantity.__imod__)
        __ilshift__ = _wrap_update_last_updated(Quantity.__ilshift__)
        __irshift__ = _wrap_update_last_updated(Quantity.__irshift__)
        __iand__ = _wrap_update_last_updated(Quantity.__iand__)
        __ixor__ = _wrap_update_last_updated(Quantity.__ixor__)
        __ior__ = _wrap_update_last_updated(Quantity.__ior__)
        __imatmul__ = _wrap_update_last_updated(Quantity.__imatmul__)
