"""Tests for the paramdb._param_data module."""

from __future__ import annotations

from time import sleep
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pytest
from pytest import FixtureRequest
from paramdb._param_data import Struct, Param

SLEEP_TIME = 0.01
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


def update_param_and_assert_struct_last_updated_changed(
    param: CustomParam, struct: CustomStruct
) -> None:
    """
    Helper function for the following tests.

    Update the given parameter (assumed to exist within the given structure) and assert
    that the structure's last updated time correctly reflects that something was
    just updated.
    """
    sleep(SLEEP_TIME)  # Wait so following datetimes are different than previous ones
    start = datetime.now()
    param.number += 1
    end = datetime.now()
    assert struct.last_updated is not None and start <= struct.last_updated <= end


@pytest.fixture(name="number")
def fixture_number() -> float:
    """Number used to initialize parameter data."""
    return 1.23


@pytest.fixture(name="string")
def fixture_string() -> str:
    """String used to initialize parameter data."""
    return "test"


@pytest.fixture(name="param_data", params=[CustomStruct, CustomParam])
def fixture_param_data(
    request: FixtureRequest, number: float, string: str
) -> CustomStruct | CustomParam:
    """Parameter data object, either a parameter or structure."""
    param_data_class: type[CustomStruct | CustomParam] = request.param
    return param_data_class(number=number, string=string)


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


def test_property_access(
    number: float, string: str, param_data: CustomParam | CustomStruct
) -> None:
    """Parameter data properties can be accessed via dot notation and index brackets."""
    assert param_data.number == number
    assert param_data.string == string
    assert param_data["number"] == number
    assert param_data["string"] == string


def test_struct_property_update(
    number: float, param_data: CustomParam | CustomStruct
) -> None:
    """Parameter data properties can be updated via dot notation and index brackets."""
    param_data.number += 1
    assert param_data.number == number + 1
    param_data["number"] -= 1
    assert param_data.number == number


def test_param_default_last_updated() -> None:
    """Parameter object initializes the last updated time to the current time."""
    start = datetime.now()
    param = CustomParam()
    end = datetime.now()
    assert start <= param.last_updated <= end


def test_param_initialize_last_updated() -> None:
    """
    Parameter object initializes the last updated time to the given value instead of the
    current time.
    """
    last_updated = datetime.now() - timedelta(days=1)
    param = CustomParam(_last_updated=last_updated)
    assert param.last_updated == last_updated


def test_param_update_last_updated() -> None:
    """
    Parameter object updates the last updated time when a property is updated with dot
    notation or index brackets.
    """
    # Dot notation access
    param = CustomParam()
    sleep(SLEEP_TIME)  # Wait so following datetimes are different than previous ones
    start = datetime.now()
    param.number += 1
    end = datetime.now()
    assert start <= param.last_updated <= end

    # Index bracket access
    sleep(SLEEP_TIME)  # Wait so following datetimes are different than previous ones
    start = datetime.now()
    param["number"] += 1
    end = datetime.now()
    assert start <= param.last_updated <= end


def test_struct_no_last_updated() -> None:
    """Structure object that contains no parameters has no last updated time."""
    struct = CustomStruct()
    assert struct.last_updated is None


def test_struct_last_updated_from_param(complex_struct: CustomStruct) -> None:
    """Structure object can find the most recent last updated time from a parameter."""
    param = complex_struct.param
    assert param is not None
    update_param_and_assert_struct_last_updated_changed(param, complex_struct)


def test_struct_last_updated_from_struct(complex_struct: CustomStruct) -> None:
    """Structure object can find the most recent last updated time from a structure."""
    struct = complex_struct.struct
    assert struct is not None
    param_in_struct = struct.param
    assert param_in_struct is not None
    update_param_and_assert_struct_last_updated_changed(param_in_struct, complex_struct)


def test_struct_last_updated_from_param_in_list(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter within
    a list.
    """
    param_in_list = complex_struct.param_list[0]
    assert isinstance(param_in_list, CustomParam)
    update_param_and_assert_struct_last_updated_changed(param_in_list, complex_struct)


def test_struct_last_updated_from_list_in_list(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    list within a list.
    """
    list_in_list = complex_struct.param_list[1]
    assert isinstance(list_in_list, list)
    param_in_list_in_list = list_in_list[0]
    update_param_and_assert_struct_last_updated_changed(
        param_in_list_in_list, complex_struct
    )


def test_struct_last_updated_from_dict_in_list(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    dictionary within a list.
    """
    dict_in_list = complex_struct.param_list[2]
    assert isinstance(dict_in_list, dict)
    param_in_dict_in_list = dict_in_list["p1"]
    update_param_and_assert_struct_last_updated_changed(
        param_in_dict_in_list, complex_struct
    )


def test_struct_last_updated_from_param_in_dict(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter within
    a dictionary.
    """
    param_in_dict = complex_struct.param_dict["param"]
    assert isinstance(param_in_dict, CustomParam)
    update_param_and_assert_struct_last_updated_changed(param_in_dict, complex_struct)


def test_struct_last_updated_from_list_in_dict(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    list within a list.
    """
    list_in_dict = complex_struct.param_dict["list"]
    assert isinstance(list_in_dict, list)
    param_in_list_in_list = list_in_dict[0]
    update_param_and_assert_struct_last_updated_changed(
        param_in_list_in_list, complex_struct
    )


def test_struct_last_updated_from_dict_in_dict(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    dictionary within a list.
    """
    dict_in_dict = complex_struct.param_dict["dict"]
    assert isinstance(dict_in_dict, dict)
    param_in_dict_in_list = dict_in_dict["p1"]
    update_param_and_assert_struct_last_updated_changed(
        param_in_dict_in_list, complex_struct
    )
