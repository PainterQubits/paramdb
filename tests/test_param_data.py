"""Tests for the paramdb._param_data module."""

from __future__ import annotations

from time import sleep
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from paramdb._param_data import ParamData, Struct, Param

NUMBER = 1.23
STRING = "test"


@dataclass
class CustomStruct(Struct):
    """Custom parameter structure."""

    number: float = NUMBER
    string: str = STRING
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

    number: float = NUMBER
    string: str = STRING


def create_complex_struct() -> CustomStruct:
    """
    Create a structure that contains parameters, structures, lists, and dictionaries.
    """
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


def update_param_and_assert_struct_last_updated_changed(
    param: CustomParam, struct: CustomStruct
) -> None:
    """
    Update the given parameter (assumed to exist within the given structure) and assert
    that the structure's last updated time correctly reflects that something was
    just updated.
    """
    sleep(0.01)  # Ensure that following times differ from previous datetime.now()'s
    start = datetime.now()
    param.number += 1
    end = datetime.now()
    assert struct.last_updated is not None and start <= struct.last_updated <= end


def test_struct_isinstance() -> None:
    """Structure object is an instance of its superclasses."""
    struct = CustomStruct()
    assert isinstance(struct, Struct)
    assert isinstance(struct, ParamData)


def test_param_isinstance() -> None:
    """Parameter object is an instance of its superclasses."""
    param = CustomParam()
    assert isinstance(param, Param)
    assert isinstance(param, ParamData)


def test_struct_property_access() -> None:
    """Structure properties can be accessed via dot notation and index brackets."""
    struct = CustomStruct(number=NUMBER, string=STRING)
    assert struct.number == NUMBER
    assert struct.string == STRING
    assert struct["number"] == NUMBER
    assert struct["string"] == STRING


def test_struct_property_update() -> None:
    """Structure properties can be updated via dot notation and index brackets."""
    struct = CustomStruct(number=NUMBER)
    struct.number += 1
    assert struct.number == NUMBER + 1
    struct["number"] -= 1
    assert struct.number == NUMBER


def test_param_property_access() -> None:
    """Parameter properties can be accessed via dot notation and index brakets."""
    param = CustomParam(number=NUMBER, string=STRING)
    assert param.number == NUMBER
    assert param.string == STRING
    assert param["number"] == NUMBER
    assert param["string"] == STRING


def test_param_property_update() -> None:
    """Parameter properties can be updated via dot notation and index brackets."""
    param = CustomParam(number=NUMBER)
    param.number += 1
    assert param.number == NUMBER + 1
    param["number"] -= 1
    assert param.number == NUMBER


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
    param = CustomParam()
    sleep(0.01)  # Ensure that following times differ from previous datetime.now()'s
    start = datetime.now()
    param.number += 1
    end = datetime.now()
    assert start <= param.last_updated <= end
    sleep(0.01)  # Ensure that following times differ from previous datetime.now()'s
    start = datetime.now()
    param["number"] += 1
    end = datetime.now()
    assert start <= param.last_updated <= end


def test_struct_no_last_updated() -> None:
    """Structure object that contains no parameters has no last updated time."""
    struct = CustomStruct()
    assert struct.last_updated is None


def test_struct_last_updated_from_param() -> None:
    """Structure object can find the most recent last updated time from a parameter."""
    complex_struct = create_complex_struct()
    param = complex_struct.param
    assert param is not None
    update_param_and_assert_struct_last_updated_changed(param, complex_struct)


def test_struct_last_updated_from_struct() -> None:
    """Structure object can find the most recent last updated time from a structure."""
    complex_struct = create_complex_struct()
    struct = complex_struct.struct
    assert struct is not None
    param_in_struct = struct.param
    assert param_in_struct is not None
    update_param_and_assert_struct_last_updated_changed(param_in_struct, complex_struct)


def test_struct_last_updated_from_list() -> None:
    """
    Structure object can find the most recent last updated time from a parameter within
    a list.
    """
    complex_struct = create_complex_struct()
    param_in_list = complex_struct.param_list[0]
    assert isinstance(param_in_list, CustomParam)
    update_param_and_assert_struct_last_updated_changed(param_in_list, complex_struct)


def test_struct_last_updated_from_list_in_list() -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    list within a list.
    """
    complex_struct = create_complex_struct()
    list_in_list = complex_struct.param_list[1]
    assert isinstance(list_in_list, list)
    param_in_list_in_list = list_in_list[0]
    update_param_and_assert_struct_last_updated_changed(
        param_in_list_in_list, complex_struct
    )


def test_struct_last_updated_from_dict_in_list() -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    dictionary within a list.
    """
    complex_struct = create_complex_struct()
    dict_in_list = complex_struct.param_list[2]
    assert isinstance(dict_in_list, dict)
    param_in_dict_in_list = dict_in_list["p1"]
    update_param_and_assert_struct_last_updated_changed(
        param_in_dict_in_list, complex_struct
    )


def test_struct_last_updated_from_dict() -> None:
    """
    Structure object can find the most recent last updated time from a parameter within
    a dictionary.
    """
    complex_struct = create_complex_struct()
    param_in_dict = complex_struct.param_dict["param"]
    assert isinstance(param_in_dict, CustomParam)
    update_param_and_assert_struct_last_updated_changed(param_in_dict, complex_struct)


def test_struct_last_updated_from_list_in_dict() -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    list within a list.
    """
    complex_struct = create_complex_struct()
    list_in_dict = complex_struct.param_dict["list"]
    assert isinstance(list_in_dict, list)
    param_in_list_in_list = list_in_dict[0]
    update_param_and_assert_struct_last_updated_changed(
        param_in_list_in_list, complex_struct
    )


def test_struct_last_updated_from_dict_in_dict() -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    dictionary within a list.
    """
    complex_struct = create_complex_struct()
    dict_in_dict = complex_struct.param_dict["dict"]
    assert isinstance(dict_in_dict, dict)
    param_in_dict_in_list = dict_in_dict["p1"]
    update_param_and_assert_struct_last_updated_changed(
        param_in_dict_in_list, complex_struct
    )
