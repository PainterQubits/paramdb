"""Defines global fixtures. Called automatically by Pytest before running tests."""

from typing import Any
from copy import deepcopy
import pytest
from paramdb import (
    ParamData,
    ParamInt,
    ParamFloat,
    ParamBool,
    ParamStr,
    ParamNone,
    ParamDataFrame,
    ParamList,
    ParamDict,
)
from tests.helpers import (
    DEFAULT_NUMBER,
    DEFAULT_STRING,
    EmptyParam,
    SimpleParam,
    NoTypeValidationParam,
    WithTypeValidationParam,
    NoAssignmentValidationParam,
    WithAssignmentValidationParam,
    SubclassParam,
    ComplexParam,
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


@pytest.fixture(name="param_int")
def fixture_param_int() -> ParamInt:
    """Parameter integer object."""
    return ParamInt(123)


@pytest.fixture(name="param_float")
def fixture_param_float(number: float) -> ParamFloat:
    """Parameter float object."""
    return ParamFloat(number)


@pytest.fixture(name="param_bool")
def fixture_param_bool() -> ParamBool:
    """Parameter boolean object."""
    return ParamBool(True)


@pytest.fixture(name="param_str")
def fixture_param_str(string: str) -> ParamStr:
    """Parameter string object."""
    return ParamStr(string)


@pytest.fixture(name="param_none")
def fixture_param_none() -> ParamNone:
    """Parameter ``None`` object."""
    return ParamNone()


@pytest.fixture(name="param_data_frame")
def fixture_param_data_frame(string: str) -> ParamDataFrame:
    """Parameter DataFrame."""
    return ParamDataFrame(f"{string}.csv")


@pytest.fixture(name="empty_param")
def fixture_empty_param() -> EmptyParam:
    """Empty parameter data class object."""
    return EmptyParam()


@pytest.fixture(name="simple_param")
def fixture_simple_param(number: float, string: str) -> SimpleParam:
    """Simple parameter data class object."""
    return SimpleParam(number=number, string=string)


@pytest.fixture(name="no_type_validation_param")
def fixture_no_type_validation_param(
    number: float, string: str
) -> NoTypeValidationParam:
    """Parameter data class object without type validation."""
    return NoTypeValidationParam(number=number, string=string)


@pytest.fixture(name="with_type_validation_param")
def fixture_with_type_validation_param(
    number: float, string: str
) -> WithTypeValidationParam:
    """Parameter data class object type validation re-enabled."""
    return WithTypeValidationParam(number=number, string=string)


@pytest.fixture(name="no_assignment_validation_param")
def fixture_no_assignment_validation_param(
    number: float, string: str
) -> NoAssignmentValidationParam:
    """Parameter data class object without assignment validation."""
    return NoAssignmentValidationParam(number=number, string=string)


@pytest.fixture(name="with_assignment_validation_param")
def fixture_with_assignment_validation_param(
    number: float, string: str
) -> WithAssignmentValidationParam:
    """Parameter data class object with assignment validation re-enabled."""
    return WithAssignmentValidationParam(number=number, string=string)


@pytest.fixture(name="subclass_param")
def fixture_subclass_param(number: float, string: str) -> SubclassParam:
    """
    Parameter data class object that is a subclass of another parameter data class.
    """
    return SubclassParam(number=number, string=string, second_number=number)


@pytest.fixture(name="complex_param")
def fixture_complex_param(number: float, string: str) -> ComplexParam:
    """Complex parameter data class object."""
    return ComplexParam(
        number=number,
        string=string,
        param_data_frame=ParamDataFrame(string),
        empty_param=EmptyParam(),
        simple_param=SimpleParam(),
        no_type_validation_param=NoTypeValidationParam(),
        with_type_validation_param=WithTypeValidationParam(),
        no_assignment_validation_param=NoAssignmentValidationParam(),
        with_assignment_validation_param=WithAssignmentValidationParam(),
        subclass_param=SubclassParam(),
        complex_param=ComplexParam(),
        param_list=ParamList(),
        param_dict=ParamDict(),
    )


@pytest.fixture(name="param_list_contents")
def fixture_param_list_contents(number: float, string: str) -> list[Any]:
    """Contents to initialize a parameter list."""
    return [
        number,
        string,
        ParamInt(),
        ParamFloat(number),
        ParamBool(),
        ParamStr(string),
        ParamNone(),
        ParamDataFrame(string),
        EmptyParam(),
        SimpleParam(),
        NoTypeValidationParam(),
        WithTypeValidationParam(),
        NoAssignmentValidationParam(),
        WithAssignmentValidationParam(),
        SubclassParam(),
        ComplexParam(),
        ParamList(),
        ParamDict(),
    ]


@pytest.fixture(name="param_dict_contents")
# pylint: disable-next=too-many-arguments
def fixture_param_dict_contents(
    number: float,
    string: str,
    param_int: ParamInt,
    param_float: ParamFloat,
    param_bool: ParamBool,
    param_str: ParamStr,
    param_none: ParamNone,
    param_data_frame: ParamDataFrame,
    empty_param: EmptyParam,
    simple_param: SimpleParam,
    no_type_validation_param: NoTypeValidationParam,
    with_type_validation_param: WithTypeValidationParam,
    no_assignment_validation_param: NoAssignmentValidationParam,
    with_assignment_validation_param: WithAssignmentValidationParam,
    subclass_param: SubclassParam,
    complex_param: ComplexParam,
) -> dict[str, Any]:
    """Contents to initialize a parameter dictionary."""
    return {
        "number": number,
        "string": string,
        "param_int": param_int,
        "param_float": deepcopy(param_float),
        "param_bool": deepcopy(param_bool),
        "param_str": deepcopy(param_str),
        "param_none": deepcopy(param_none),
        "param_data_frame": deepcopy(param_data_frame),
        "empty_param": deepcopy(empty_param),
        "simple_param": deepcopy(simple_param),
        "no_type_validation_param": deepcopy(no_type_validation_param),
        "with_type_validation_param": deepcopy(with_type_validation_param),
        "no_assignment_validation_param": deepcopy(no_assignment_validation_param),
        "with_assignment_validation_param": deepcopy(with_assignment_validation_param),
        "subclass_param": deepcopy(subclass_param),
        "complex_param": deepcopy(complex_param),
        "param_list": ParamList(),
        "param_dict": ParamDict(),
    }


@pytest.fixture(name="empty_param_list")
def fixture_empty_param_list() -> ParamList[Any]:
    """Empty parameter list."""
    return ParamList()


@pytest.fixture(name="param_list")
def fixture_param_list(param_list_contents: list[Any]) -> ParamList[Any]:
    """Parameter list."""
    return ParamList(deepcopy(param_list_contents))


@pytest.fixture(name="empty_param_dict")
def fixture_empty_param_dict() -> ParamDict[Any]:
    """Empty parameter dictionary."""
    return ParamDict()


@pytest.fixture(name="param_dict")
def fixture_param_dict(param_dict_contents: dict[str, Any]) -> ParamDict[Any]:
    """Parameter dictionary."""
    return ParamDict(deepcopy(param_dict_contents))


@pytest.fixture(
    name="param_data",
    params=[
        "param_int",
        "param_float",
        "param_bool",
        "param_str",
        "param_none",
        "param_data_frame",
        "empty_param",
        "simple_param",
        "no_type_validation_param",
        "no_assignment_validation_param",
        "subclass_param",
        "complex_param",
        "empty_param_list",
        "param_list",
        "empty_param_dict",
        "param_dict",
    ],
)
def fixture_param_data(request: pytest.FixtureRequest) -> ParamData:
    """Parameter data."""
    param_data: ParamData = deepcopy(request.getfixturevalue(request.param))
    return param_data


@pytest.fixture(name="updated_param_data_and_times")
def fixture_updated_param_data_and_times(
    param_data: ParamData, number: float
) -> tuple[ParamData, Times]:
    """
    Parameter data that has been updated between the returned Times. Broken down into
    individual fixtures for parameter data and times below.
    """
    updated_param_data = deepcopy(param_data)
    with capture_start_end_times() as times:
        if isinstance(
            updated_param_data,
            (ParamInt, ParamFloat, ParamBool, ParamStr),
        ):
            updated_param_data = type(updated_param_data)(updated_param_data.value)
        elif isinstance(updated_param_data, (ParamNone, EmptyParam)):
            updated_param_data = type(updated_param_data)()
        elif isinstance(updated_param_data, ParamDataFrame):
            updated_param_data.path = ""
        elif isinstance(updated_param_data, SimpleParam):
            updated_param_data.number += 1
        elif isinstance(updated_param_data, SubclassParam):
            updated_param_data.second_number += 1
        elif isinstance(updated_param_data, ComplexParam):
            assert updated_param_data.simple_param is not None
            updated_param_data.simple_param.number += 1
        elif isinstance(updated_param_data, ParamList):
            if len(updated_param_data) == 0:
                updated_param_data.append(number)
            else:
                updated_param_data[9].number += 1
        elif isinstance(updated_param_data, ParamDict):
            if len(updated_param_data) == 0:
                updated_param_data["number"] = number
            else:
                updated_param_data.simple_param.number += 1
    return updated_param_data, times


@pytest.fixture(name="updated_param_data")
def fixture_updated_param_data(
    updated_param_data_and_times: tuple[ParamData, Times]
) -> ParamData:
    """Parameter data that has been updated."""
    return updated_param_data_and_times[0]


@pytest.fixture(name="updated_times")
def fixture_updated_times(
    updated_param_data_and_times: tuple[ParamData, Times]
) -> Times:
    """Times before and after param_data fixture was updated."""
    return updated_param_data_and_times[1]
