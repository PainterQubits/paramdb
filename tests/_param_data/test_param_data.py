"""Tests for the paramdb._param_data._param_data module."""

from dataclasses import is_dataclass
from copy import deepcopy
import pytest
from tests.helpers import CustomStruct, Times, capture_start_end_times
from paramdb import ParamData
from paramdb._param_data._param_data import get_param_class


def test_custom_subclass_extra_kwarg(param_data: ParamData) -> None:
    """Extra keyword arugments in a custom parameter data subclass raise a TypeError."""
    cls = type(param_data)
    with pytest.raises(TypeError) as exc_info:
        # pylint: disable-next=unused-variable
        class CustomParamData(cls, extra_kwarg="test"):  # type: ignore
            """Custom parameter data class with an extra keyword arugment."""

    error_message = str(exc_info.value)
    if is_dataclass(cls):
        assert (
            error_message
            == "dataclass() got an unexpected keyword argument 'extra_kwarg'"
        )
    else:
        assert "takes no keyword arguments" in error_message


def test_is_param_data(param_data: ParamData) -> None:
    """Parameter data object is an instance of the `ParamData` class."""
    assert isinstance(param_data, ParamData)


def test_get_param_class(param_data: ParamData) -> None:
    """Parameter classes can be retrieved by name."""
    param_class = type(param_data)
    assert get_param_class(param_class.__name__) is param_class


def test_param_data_last_updated(
    updated_param_data: ParamData, updated_times: Times
) -> None:
    """Updating simple parameter data updates the last updated time."""
    assert updated_param_data.last_updated is not None
    assert (
        updated_times.start
        < updated_param_data.last_updated.timestamp()
        < updated_times.end
    )


def test_list_or_dict_last_updated(
    updated_param_data: ParamData, updated_times: Times
) -> None:
    """Can get last updated from a Python list or dictionary."""
    # Can get last updated time from within a list
    struct_with_list = CustomStruct(
        list=[CustomStruct(), [updated_param_data, CustomStruct()]]
    )
    assert struct_with_list.last_updated is not None
    assert (
        updated_times.start
        < struct_with_list.last_updated.timestamp()
        < updated_times.end
    )

    # Can get last updated time from within a dictionary
    struct_with_dict = CustomStruct(
        dict={
            "p1": CustomStruct(),
            "p2": {"p1": updated_param_data, "p2": CustomStruct()},
        }
    )
    assert struct_with_dict.last_updated is not None
    assert (
        updated_times.start
        < struct_with_list.last_updated.timestamp()
        < updated_times.end
    )


def test_child_does_not_change(param_data: ParamData) -> None:
    """
    Including a parameter data object as a child within a parent structure does not
    change the parameter in terms of equality comparison (i.e. public properties,
    importantly last_updated, have not changed).
    """
    param_data_original = deepcopy(param_data)
    with capture_start_end_times():
        _ = CustomStruct(param_data=param_data)
    assert param_data == param_data_original


def test_to_and_from_dict(param_data: ParamData) -> None:
    """Parameter data can be converted to and from a dictionary."""
    param_data_dict = param_data.to_dict()
    assert isinstance(param_data_dict, dict)
    with capture_start_end_times():
        param_data_from_dict = param_data.from_dict(param_data_dict)
    assert param_data_from_dict == param_data
    assert param_data_from_dict.last_updated == param_data.last_updated


def test_no_parent_fails(param_data: ParamData) -> None:
    """Fails to get the parent when there is no parent."""
    with pytest.raises(ValueError) as exc_info:
        _ = param_data.parent
    assert (
        str(exc_info.value)
        == f"'{type(param_data).__name__}' object has no parent, or its parent has not"
        " been initialized yet"
    )


def test_self_is_root(param_data: ParamData) -> None:
    """Parameter data object with no parent returns itself as the root."""
    assert param_data.root is param_data


def test_parent_is_root(param_data: ParamData) -> None:
    """
    Parameter data object with a parent that has no parent returns the parent as the
    root.
    """
    parent = CustomStruct(param_data=param_data)
    assert param_data.root is parent


def test_parent_of_parent_is_root(param_data: ParamData) -> None:
    """
    Parameter data object with a parent that has a parent returns the highest level
    parent as the root.
    """
    root = CustomStruct(struct=CustomStruct(param_data=param_data))
    assert param_data.root is root
