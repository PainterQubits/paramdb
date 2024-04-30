"""Tests for the paramdb._param_data._primitives module."""

from typing import Union, cast
from copy import deepcopy
import math
import pytest
from paramdb import ParamInt, ParamFloat, ParamBool, ParamStr, ParamNone
from tests.helpers import (
    CustomParamInt,
    CustomParamFloat,
    CustomParamBool,
    CustomParamStr,
    CustomParamNone,
)

ParamPrimitive = Union[ParamInt, ParamFloat, ParamBool, ParamStr, ParamNone]
CustomParamPrimitive = Union[
    CustomParamInt, CustomParamFloat, CustomParamBool, CustomParamStr, CustomParamNone
]


@pytest.fixture(
    name="param_primitive",
    params=["param_int", "param_float", "param_bool", "param_str", "param_none"],
)
def fixture_param_primitive(request: pytest.FixtureRequest) -> ParamPrimitive:
    """Parameter primitive."""
    return cast(ParamPrimitive, deepcopy(request.getfixturevalue(request.param)))


@pytest.fixture(name="custom_param_primitive")
def fixture_custom_param_primitive(
    param_primitive: ParamPrimitive,
) -> CustomParamPrimitive:
    """Custom parameter primitive."""
    if isinstance(param_primitive, ParamInt):
        return CustomParamInt(param_primitive.value)
    if isinstance(param_primitive, ParamFloat):
        return CustomParamFloat(param_primitive.value)
    if isinstance(param_primitive, ParamBool):
        return CustomParamBool(param_primitive.value)
    if isinstance(param_primitive, ParamStr):
        return CustomParamStr(param_primitive.value)
    return CustomParamNone()


def test_param_int_isinstance(param_int: ParamInt) -> None:
    """Parameter integers are instances of ``int``."""
    assert isinstance(param_int, int)
    assert isinstance(CustomParamInt(param_int.value), int)


def test_param_float_isinstance(param_float: ParamFloat) -> None:
    """Parameter floats are instances of ``float``."""
    assert isinstance(param_float, float)
    assert isinstance(CustomParamFloat(param_float.value), float)


def test_param_bool_isinstance(param_bool: ParamBool) -> None:
    """Parameter booleans are instances of ``int``."""
    assert isinstance(param_bool, int)
    assert isinstance(CustomParamBool(param_bool.value), int)


def test_param_str_isinstance(param_str: ParamStr) -> None:
    """Parameter strings are instances of ``str``."""
    assert isinstance(param_str, str)
    assert isinstance(CustomParamStr(param_str.value), str)


def test_param_int_constructor() -> None:
    """The ``ParamInt`` constructor behaves like the ``int`` constructor."""
    assert ParamInt() == 0
    assert ParamInt(123) == 123
    assert ParamInt(123.0) == 123.0
    assert ParamInt(123.1) == 123
    assert ParamInt(123.9) == 123
    assert ParamInt("123") == 123
    assert ParamInt("0x42", base=16) == 66
    with pytest.raises(ValueError):
        ParamInt("hello")


def test_param_float_constructor() -> None:
    """The ``ParamFloat`` constructor behaves like the ``float`` constructor."""
    assert ParamFloat() == 0.0
    assert ParamFloat(123) == 123.0
    assert ParamFloat(1.23) == 1.23
    assert ParamFloat("1.23") == 1.23
    assert ParamFloat("inf") == float("inf")
    assert math.isnan(ParamFloat("nan"))
    with pytest.raises(ValueError):
        ParamFloat("hello")


def test_param_bool_constructor() -> None:
    """The ``ParamBool`` constructor behaves like the ``bool`` constructor."""
    assert ParamBool().value is False
    assert ParamBool(123).value is True
    assert ParamBool("").value is False
    assert ParamBool("hello").value is True


def test_param_str_constructor() -> None:
    """The ``ParamStr`` constructor behaves like the ``str`` constructor."""
    assert ParamStr() == ""
    assert ParamStr("hello") == "hello"
    assert ParamStr(123) == "123"
    assert ParamStr(b"hello", encoding="utf-8") == "hello"


def test_param_int_value() -> None:
    """Can access the primitive value of a parameter integer."""
    param_int_value = ParamInt(123).value
    assert type(param_int_value) is int  # pylint: disable=unidiomatic-typecheck
    assert param_int_value == 123


def test_param_float_value(number: float) -> None:
    """Can access the primitive value of a parameter float."""
    param_float_value = ParamFloat(number).value
    assert type(param_float_value) is float  # pylint: disable=unidiomatic-typecheck
    assert param_float_value == number


def test_param_bool_value() -> None:
    """Can access the primitive value of a parameter boolean."""
    assert ParamBool(True).value is True
    assert ParamBool(False).value is False
    assert ParamBool(0).value is False
    assert ParamBool(123).value is True


def test_param_str_value(string: str) -> None:
    """Can access the primitive value of a parameter string."""
    param_str_value = ParamStr(string).value
    assert type(param_str_value) is str  # pylint: disable=unidiomatic-typecheck
    assert param_str_value == string


def test_param_none_value() -> None:
    """Can access the primitive value of a parameter ``None``."""
    assert ParamNone().value is None


def test_param_primitive_repr(
    param_primitive: ParamPrimitive, custom_param_primitive: CustomParamPrimitive
) -> None:
    """Can represent a parameter primitive as a string using ``repr()``."""
    if isinstance(param_primitive, ParamNone):
        assert repr(param_primitive) == f"{ParamNone.__name__}()"
        assert repr(custom_param_primitive) == f"{CustomParamNone.__name__}()"
    else:
        assert (
            repr(param_primitive)
            == f"{type(param_primitive).__name__}({param_primitive.value!r})"
        )
        assert (
            repr(custom_param_primitive) == f"{type(custom_param_primitive).__name__}"
            f"({custom_param_primitive.value!r})"
        )


def test_param_primitive_bool(
    param_primitive: ParamPrimitive, custom_param_primitive: CustomParamPrimitive
) -> None:
    """Parameter primitive objects have the correct truth values."""
    assert bool(param_primitive) is bool(param_primitive.value)
    assert bool(custom_param_primitive) is bool(custom_param_primitive.value)


def test_param_primitive_eq(
    param_primitive: ParamPrimitive, custom_param_primitive: CustomParamPrimitive
) -> None:
    """
    Parameter primitive objects are equal to themselves, their vaues, and custom
    parameter primitive objects, and are not equal to other objects.
    """
    # pylint: disable=comparison-with-itself
    assert param_primitive == param_primitive
    assert param_primitive == custom_param_primitive
    assert custom_param_primitive == custom_param_primitive
    assert custom_param_primitive == param_primitive
    if isinstance(param_primitive, ParamNone):
        assert param_primitive != param_primitive.value
        assert custom_param_primitive != custom_param_primitive.value
    else:
        assert param_primitive == param_primitive.value
        assert custom_param_primitive == custom_param_primitive.value


def test_param_int_methods_return_int(param_int: ParamInt) -> None:
    """``ParamInt`` methods inherited from ``int`` return ``int`` objects."""
    # pylint: disable=unidiomatic-typecheck
    assert type(param_int + 123) is int
    assert type(-param_int) is int
    assert type(param_int.real) is int


def test_param_float_methods_return_float(param_float: ParamFloat) -> None:
    """``ParamFloat`` methods inherited from ``float`` return ``float`` objects."""
    # pylint: disable=unidiomatic-typecheck
    assert type(param_float + 123) is float
    assert type(-param_float) is float
    assert type(param_float.real) is float


def test_param_bool_methods_return_int() -> None:
    """``ParamBool`` methods inherited from ``int`` return ``int`` objects."""
    # pylint: disable=unidiomatic-typecheck
    assert type(ParamBool(True) ^ ParamBool(False)) is int
    assert type(ParamBool(True) | ParamBool(False)) is int


def test_param_str_methods_return_str(param_str: ParamStr) -> None:
    """``ParamStr`` methods inherited from ``str`` return ``str`` objects."""
    # pylint: disable=unidiomatic-typecheck
    assert type(param_str + "") is str
    assert type(param_str[::-1]) is str
    assert type(param_str.capitalize()) is str
