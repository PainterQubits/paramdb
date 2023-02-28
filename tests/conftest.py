"""Defines global fixtures. Called automatically by Pytest before running tests."""

import pytest
from tests.param_data import (
    DEFAULT_NUMBER,
    DEFAULT_STRING,
    CustomStruct,
    CustomParam,
)


@pytest.fixture(name="number")
def fixture_number() -> float:
    """Number used to initialize parameter data."""
    return DEFAULT_NUMBER


@pytest.fixture(name="string")
def fixture_string() -> str:
    """String used to initialize parameter data."""
    return DEFAULT_STRING


@pytest.fixture(name="simple_param")
def fixture_simple_param(number: float, string: str) -> CustomParam:
    """Simple parameter."""
    return CustomParam(number=number, string=string)


@pytest.fixture(name="simple_struct")
def fixture_simple_struct(number: float, string: str) -> CustomStruct:
    """Simple structure."""
    return CustomStruct(number=number, string=string)


@pytest.fixture(name="complex_struct")
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


@pytest.fixture(
    name="param_data", params=["simple_param", "simple_struct", "complex_struct"]
)
def fixture_param_data(request: pytest.FixtureRequest) -> CustomParam | CustomStruct:
    """Parameter data (a simple parameter, simple structure, or complex structure)."""
    param_data: CustomParam | CustomParam = request.getfixturevalue(request.param)
    return param_data
