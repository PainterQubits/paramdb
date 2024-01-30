"""Defines global fixtures. Called automatically by Pytest before running tests."""

from typing import Any
from copy import deepcopy
import pytest
from paramdb import ParamData, ParamList, ParamDict
from tests.helpers import (
    DEFAULT_NUMBER,
    DEFAULT_STRING,
    CustomStruct,
    CustomParam,
    Times,
    capture_start_end_times,
)


@pytest.fixture(name="number")
def fixture_number() -> float:
    """Number used to initialize parameter data."""
    return DEFAULT_NUMBER


@pytest.fixture(name="string")
def fixture_string() -> str:
    """String used to initialize parameter data."""
    return DEFAULT_STRING


@pytest.fixture(name="param")
def fixture_param(number: float, string: str) -> CustomParam:
    """Parameter."""
    return CustomParam(number=number, string=string)


@pytest.fixture(name="struct")
def fixture_struct(number: float, string: str) -> CustomStruct:
    """Structure."""
    return CustomStruct(
        number=number,
        string=string,
        param=CustomParam(),
        struct=CustomStruct(),
        param_list=ParamList(),
        param_dict=ParamDict(),
    )


@pytest.fixture(name="param_list_contents")
def fixture_param_list_contents(number: float, string: str) -> list[Any]:
    """Contents to initialize a parameter list."""
    return [number, string, CustomParam(), CustomStruct(), ParamList(), ParamDict()]


@pytest.fixture(name="param_dict_contents")
def fixture_param_dict_contents(
    number: float, string: str, param: CustomParam, struct: CustomStruct
) -> dict[str, Any]:
    """Contents to initialize a parameter dictionary."""
    return {
        "number": number,
        "string": string,
        "param": deepcopy(param),
        "struct": deepcopy(struct),
        "param_list": ParamList(),
        "param_dict": ParamDict(),
    }


@pytest.fixture(name="param_list")
def fixture_param_list(param_list_contents: list[Any]) -> ParamList[Any]:
    """Parameter list."""
    return ParamList(deepcopy(param_list_contents))


@pytest.fixture(name="param_dict")
def fixture_param_dict(param_dict_contents: dict[str, Any]) -> ParamDict[Any]:
    """Parameter dictionary."""
    return ParamDict(deepcopy(param_dict_contents))


@pytest.fixture(
    name="param_data",
    params=["param", "struct", "param_list", "param_dict"],
)
def fixture_param_data(
    request: pytest.FixtureRequest,
) -> ParamData:
    """Parameter data."""
    param_data: ParamData = deepcopy(request.getfixturevalue(request.param))
    return param_data


@pytest.fixture(name="updated_param_data_and_times")
def fixture_updated_param_data_and_times(
    param_data: ParamData,
) -> tuple[ParamData, Times]:
    """
    Parameter data that has been updated between the returned Times. Broken down into
    individual fixtures for parameter data and times below.
    """
    updated_param_data = deepcopy(param_data)
    with capture_start_end_times() as times:
        if isinstance(updated_param_data, CustomParam):
            updated_param_data.number += 1
        if isinstance(updated_param_data, CustomStruct):
            assert updated_param_data.param is not None
            updated_param_data.param.number += 1
        if isinstance(updated_param_data, ParamList):
            updated_param_data[2].number += 1
        if isinstance(updated_param_data, ParamDict):
            updated_param_data.param.number += 1
    return updated_param_data, times


@pytest.fixture(name="updated_param_data")
def fixture_updated_param_data(
    updated_param_data_and_times: tuple[ParamData, Times]
) -> ParamData:
    """Parameter data that has been updated."""
    return updated_param_data_and_times[0]


@pytest.fixture(name="updated_times")
def fixture_start(updated_param_data_and_times: tuple[ParamData, Times]) -> Times:
    """Times before and after param_data fixture was updated."""
    return updated_param_data_and_times[1]
