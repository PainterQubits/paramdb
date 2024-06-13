"""Tests for the paramdb._param_data._param_data module."""

from __future__ import annotations
from typing import Any
from dataclasses import is_dataclass
from copy import deepcopy
import pytest
from tests.helpers import (
    SimpleParam,
    ComplexParam,
    update_child,
    capture_start_end_times,
)
from paramdb import ParamData, ParamDataFrame
from paramdb._param_data._param_data import get_param_class


@pytest.fixture(name="param_data_type")
def fixture_param_data_type(param_data: ParamData[Any]) -> type[ParamData[Any]]:
    """Parameter data type."""
    return type(param_data)


def test_custom_subclass_extra_kwarg_fails(
    param_data_type: type[ParamData[Any]],
) -> None:
    """Extra keyword arugments in a custom parameter data subclass raise a TypeError."""
    with pytest.raises(TypeError) as exc_info:
        # pylint: disable-next=unused-variable
        class CustomParamData(
            param_data_type,  # type: ignore[valid-type,misc]
            extra_kwarg="test",  # type: ignore[call-arg]
        ):
            """Custom parameter data class with an extra keyword arugment."""

    error_message = str(exc_info.value)
    if is_dataclass(param_data_type):
        assert (
            error_message
            == "dataclass() got an unexpected keyword argument 'extra_kwarg'"
        )
    else:
        assert "takes no keyword arguments" in error_message


def test_is_param_data(param_data: ParamData[Any]) -> None:
    """Parameter data object is an instance of the `ParamData` class."""
    assert isinstance(param_data, ParamData)


def test_get_param_class(param_data: ParamData[Any]) -> None:
    """Parameter classes can be retrieved by name."""
    param_class = type(param_data)
    assert get_param_class(param_class.__name__) is param_class


def test_param_data_initial_last_updated(
    number: float, param_data_type: type[ParamData[Any]]
) -> None:
    """New parameter data objects are initialized with a last updated timestamp."""
    with capture_start_end_times() as times:
        new_param_data: ParamData[Any]
        if issubclass(param_data_type, ParamDataFrame):
            new_param_data = param_data_type("")
        elif issubclass(param_data_type, SimpleParam):
            new_param_data = param_data_type(number=number)
        else:
            new_param_data = param_data_type()
    assert new_param_data.last_updated is not None
    assert times.start < new_param_data.last_updated.timestamp() < times.end


def test_param_data_updating_child_updates_last_updated(
    param_data: ParamData[Any], param_data_child_name: str | int | None
) -> None:
    """The last updated time is updated when a child is updated."""
    if param_data_child_name is None:
        return
    with capture_start_end_times() as times:
        update_child(param_data, param_data_child_name)
    assert times.start < param_data.last_updated.timestamp() < times.end


def test_child_does_not_change(param_data: ParamData[Any]) -> None:
    """
    Including a parameter data object as a child within a parent structure does not
    change the parameter in terms of equality comparison (i.e. public properties,
    importantly ``last_updated``, have not changed).
    """
    param_data_original = deepcopy(param_data)
    with capture_start_end_times():
        _ = ComplexParam(param_data=param_data)
    assert param_data == param_data_original


def test_to_and_from_dict(param_data: ParamData[Any]) -> None:
    """Parameter data can be converted to and from a dictionary."""
    param_data_dict = param_data.to_dict()
    assert isinstance(param_data_dict, dict)
    with capture_start_end_times():
        param_data_from_dict = param_data.from_dict(param_data_dict)
    assert param_data_from_dict == param_data
    assert param_data_from_dict.last_updated == param_data.last_updated


def test_no_parent_fails(param_data: ParamData[Any]) -> None:
    """Fails to get the parent when there is no parent."""
    with pytest.raises(ValueError) as exc_info:
        _ = param_data.parent
    assert (
        str(exc_info.value)
        == f"'{type(param_data).__name__}' object has no parent, or its parent has not"
        " been initialized yet"
    )


def test_self_is_root(param_data: ParamData[Any]) -> None:
    """Parameter data object with no parent returns itself as the root."""
    assert param_data.root is param_data


def test_parent_is_root(param_data: ParamData[Any]) -> None:
    """
    Parameter data object with a parent that has no parent returns the parent as the
    root.
    """
    parent = ComplexParam(param_data=param_data)
    assert param_data.root is parent


def test_parent_of_parent_is_root(param_data: ParamData[Any]) -> None:
    """
    Parameter data object with a parent that has a parent returns the highest level
    parent as the root.
    """
    root = ComplexParam(complex_param=ComplexParam(param_data=param_data))
    assert param_data.root is root
