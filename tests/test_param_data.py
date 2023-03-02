"""Tests for the paramdb._param_data module."""

from copy import deepcopy
from datetime import datetime, timedelta
from tests.param_data import CustomStruct, CustomParam
from tests.helpers import sleep_for_datetime
from paramdb import ParamData
from paramdb._param_data import get_param_class


def update_param_and_assert_last_updated_changed(
    param: CustomParam, param_data: ParamData
) -> None:
    """
    Update the given parameter (assumed to be or exist within the given parameter data)
    and assert that the structure's last updated time correctly reflects that something
    was just updated.
    """
    start = datetime.now()
    sleep_for_datetime()
    param.number += 1
    sleep_for_datetime()
    end = datetime.now()
    assert param_data.last_updated is not None and start < param_data.last_updated < end


def test_is_param_data(param_data: ParamData) -> None:
    """Parameter data object is an instance of the `ParamData` class."""
    assert isinstance(param_data, ParamData)


def test_get_param_class(param_data: ParamData) -> None:
    """Parameter classes can be retrieved by name."""
    param_class = param_data.__class__
    param_class_name = param_data.__class__.__name__
    assert get_param_class(param_class_name) is param_class


def test_property_access(
    param_data: CustomParam | CustomStruct, number: float, string: str
) -> None:
    """Parameter data properties can be accessed via dot notation and index brackets."""
    assert param_data.number == number
    assert param_data.string == string
    assert param_data["number"] == number
    assert param_data["string"] == string


def test_struct_property_update(
    param_data: CustomParam | CustomStruct, number: float
) -> None:
    """Parameter data properties can be updated via dot notation and index brackets."""
    param_data.number += 1
    assert param_data.number == number + 1
    param_data["number"] -= 1
    assert param_data.number == number


def test_param_default_last_updated() -> None:
    """Parameter object initializes the last updated time to the current time."""
    start = datetime.now()
    sleep_for_datetime()
    param = CustomParam()
    sleep_for_datetime()
    end = datetime.now()
    assert start < param.last_updated < end


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
    update_param_and_assert_last_updated_changed(param, param)

    # Index bracket access
    param = CustomParam()
    start = datetime.now()
    sleep_for_datetime()
    param["number"] += 1
    sleep_for_datetime()
    end = datetime.now()
    assert start < param.last_updated < end


def test_struct_no_last_updated() -> None:
    """Structure object that contains no parameters has no last updated time."""
    struct = CustomStruct()
    assert struct.last_updated is None


def test_struct_last_updated_from_param(complex_struct: CustomStruct) -> None:
    """Structure object can find the most recent last updated time from a parameter."""
    param = complex_struct.param
    assert param is not None
    update_param_and_assert_last_updated_changed(param, complex_struct)


def test_struct_last_updated_from_struct(complex_struct: CustomStruct) -> None:
    """Structure object can find the most recent last updated time from a structure."""
    struct = complex_struct.struct
    assert struct is not None
    param_in_struct = struct.param
    assert param_in_struct is not None
    update_param_and_assert_last_updated_changed(param_in_struct, complex_struct)


def test_struct_last_updated_from_param_in_list(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter within
    a list.
    """
    param_in_list = complex_struct.param_list[0]
    assert isinstance(param_in_list, CustomParam)
    update_param_and_assert_last_updated_changed(param_in_list, complex_struct)


def test_struct_last_updated_from_list_in_list(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    list within a list.
    """
    list_in_list = complex_struct.param_list[1]
    assert isinstance(list_in_list, list)
    param_in_list_in_list = list_in_list[0]
    update_param_and_assert_last_updated_changed(param_in_list_in_list, complex_struct)


def test_struct_last_updated_from_dict_in_list(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    dictionary within a list.
    """
    dict_in_list = complex_struct.param_list[2]
    assert isinstance(dict_in_list, dict)
    param_in_dict_in_list = dict_in_list["p1"]
    update_param_and_assert_last_updated_changed(param_in_dict_in_list, complex_struct)


def test_struct_last_updated_from_param_in_dict(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter within
    a dictionary.
    """
    param_in_dict = complex_struct.param_dict["param"]
    assert isinstance(param_in_dict, CustomParam)
    update_param_and_assert_last_updated_changed(param_in_dict, complex_struct)


def test_struct_last_updated_from_list_in_dict(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    list within a list.
    """
    list_in_dict = complex_struct.param_dict["list"]
    assert isinstance(list_in_dict, list)
    param_in_list_in_list = list_in_dict[0]
    update_param_and_assert_last_updated_changed(param_in_list_in_list, complex_struct)


def test_struct_last_updated_from_dict_in_dict(complex_struct: CustomStruct) -> None:
    """
    Structure object can find the most recent last updated time from a parameter in a
    dictionary within a list.
    """
    dict_in_dict = complex_struct.param_dict["dict"]
    assert isinstance(dict_in_dict, dict)
    param_in_dict_in_list = dict_in_dict["p1"]
    update_param_and_assert_last_updated_changed(param_in_dict_in_list, complex_struct)


def test_child_does_not_change(param_data: ParamData) -> None:
    """
    Including a parameter data object as a child within a parent structure does not
    change the parameter in terms of equality comparison (i.e. public properties,
    importantly last_updated, have not changed).
    """
    param_data_original = deepcopy(param_data)
    sleep_for_datetime()
    _ = CustomStruct(param_data=param_data)
    assert param_data == param_data_original


def test_to_and_from_dict(param_data: ParamData) -> None:
    """Parameter data can be converted to and from a dictionary."""
    param_data_dict = param_data.to_dict()
    assert isinstance(param_data_dict, dict)
    sleep_for_datetime()
    param_data_from_dict = param_data.from_dict(param_data_dict)
    assert param_data_from_dict == param_data
