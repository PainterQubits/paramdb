"""
Test configuration file that defines fixtures and parameter data classes.

Called automatically by Pytest before running tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from pytest import fixture, FixtureRequest
from paramdb import Struct, Param


DEFAULT_NUMBER = 1.23
DEFAULT_STRING = "test"


@dataclass
class CustomStruct(Struct):
    """Custom parameter structure."""

    number: float = DEFAULT_NUMBER
    string: str = DEFAULT_STRING
    param: CustomParam | None = None
    struct: CustomStruct | None = None
    param_list: list[CustomParam | list[CustomParam] | dict[str, CustomParam]] = field(
        default_factory=list
    )
    param_dict: dict[
        str, CustomParam | list[CustomParam] | dict[str, CustomParam]
    ] = field(default_factory=dict)


@dataclass
class CustomParam(Param):
    """Custom parameter."""

    number: float = DEFAULT_NUMBER
    string: str = DEFAULT_STRING


@fixture
def number() -> float:
    """Number used to initialize parameter data."""
    return DEFAULT_NUMBER


@fixture
def string() -> str:
    """String used to initialize parameter data."""
    return DEFAULT_STRING


@fixture(params=[CustomStruct, CustomParam])
def param_data(
    request: FixtureRequest,
    number: float,  # pylint: disable=redefined-outer-name
    string: str,  # pylint: disable=redefined-outer-name
) -> CustomStruct | CustomParam:
    """Parameter data object, either a parameter or structure."""
    param_data_class: type[CustomStruct | CustomParam] = request.param
    return param_data_class(number=number, string=string)


@fixture(name="complex_struct")
def fixture_complex_struct() -> CustomStruct:
    """Structure that contains parameters, structures, lists, and dictionaries."""
    return CustomStruct(
        param=CustomParam(),
        struct=CustomStruct(param=CustomParam()),
        param_list=[CustomParam(), [CustomParam()], {"p1": CustomParam()}],
        param_dict={
            "param": CustomParam(),
            "list": [CustomParam()],
            "dict": {"p1": CustomParam()},
        },
    )


@fixture
def db_path(tmp_path: Path) -> str:
    """Return a path to use for a `ParamDB`."""
    return str(tmp_path / "param.db")
