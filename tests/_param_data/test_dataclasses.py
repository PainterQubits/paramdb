"""Tests for the paramdb._param_data._dataclasses module."""

from copy import deepcopy
from datetime import datetime
import pytest
from tests.helpers import CustomParam, CustomStruct, sleep_for_datetime
from paramdb import ParamData

ParamDataclass = CustomParam | CustomStruct


@pytest.fixture(
    name="param_dataclass",
    params=["param", "struct"],
)
def fixture_param_dataclass(request: pytest.FixtureRequest) -> ParamDataclass:
    """Parameter dataclass."""
    param_dataclass: ParamDataclass = deepcopy(request.getfixturevalue(request.param))
    return param_dataclass


def test_param_dataclass_get(
    param_dataclass: ParamDataclass, number: float, string: str
) -> None:
    """
    Parameter dataclass properties can be accessed via dot notation and index brackets.
    """
    assert param_dataclass.number == number
    assert param_dataclass.string == string
    assert param_dataclass["number"] == number
    assert param_dataclass["string"] == string


def test_param_dataclass_set(param_dataclass: ParamDataclass, number: float) -> None:
    """Parameter data properties can be updated via dot notation and index brackets."""
    param_dataclass.number += 1
    assert param_dataclass.number == number + 1
    param_dataclass["number"] -= 1
    assert param_dataclass.number == number


def test_param_default_last_updated() -> None:
    """Parameter object initializes the last updated time to the current time."""
    start = datetime.now()
    sleep_for_datetime()
    param = CustomParam()
    sleep_for_datetime()
    end = datetime.now()
    assert start < param.last_updated < end


def test_struct_no_last_updated() -> None:
    """Structure object that contains no parameters has no last updated time."""
    struct = CustomStruct()
    assert struct.last_updated is None


def test_struct_last_updated(
    struct: CustomStruct, updated_param_data: ParamData, start: datetime, end: datetime
) -> None:
    """Structure can correctly get the last updated time from its contents."""
    struct.param_data = updated_param_data
    assert struct.last_updated is not None
    assert start < struct.last_updated < end


def test_struct_init_parent(struct: CustomStruct) -> None:
    """Structure children correctly identify it as a parent after initialization."""
    assert struct.param is not None
    assert struct.struct is not None
    assert struct.param.parent is struct
    assert struct.struct.parent is struct


def test_struct_set_parent(struct: CustomStruct, param_data: ParamData) -> None:
    """Parameter data added to a structure has the correct parent."""
    with pytest.raises(ValueError):
        _ = param_data.parent
    for _ in range(2):  # Run twice to check reassigning the same parameter data
        struct.param_data = param_data
        assert param_data.parent is struct
    struct.param_data = None
    with pytest.raises(ValueError):
        _ = param_data.parent
