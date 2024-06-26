"""Defines global fixtures. Called automatically by Pytest before running tests."""

from __future__ import annotations
from typing import Any
from copy import deepcopy
import pytest
from paramdb import ParamData, ParamDataFrame, ParamList, ParamDict
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
)


@pytest.fixture(name="number")
def fixture_number() -> float:
    """Number used to initialize parameter data."""
    return DEFAULT_NUMBER


@pytest.fixture(name="string")
def fixture_string() -> str:
    """String used to initialize parameter data."""
    return DEFAULT_STRING


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
        simple_param=SimpleParam(number=number),
        no_type_validation_param=NoTypeValidationParam(number=number),
        with_type_validation_param=WithTypeValidationParam(number=number),
        no_assignment_validation_param=NoAssignmentValidationParam(number=number),
        with_assignment_validation_param=WithAssignmentValidationParam(number=number),
        subclass_param=SubclassParam(number=number),
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
        ParamDataFrame(string),
        EmptyParam(),
        SimpleParam(number=number),
        NoTypeValidationParam(number=number),
        WithTypeValidationParam(number=number),
        NoAssignmentValidationParam(number=number),
        WithAssignmentValidationParam(number=number),
        SubclassParam(number=number),
        ComplexParam(),
        ParamList(),
        ParamDict(),
    ]


@pytest.fixture(name="param_dict_contents")
# pylint: disable-next=too-many-arguments,too-many-locals
def fixture_param_dict_contents(
    number: float,
    string: str,
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
def fixture_param_data(request: pytest.FixtureRequest) -> ParamData[Any]:
    """Parameter data."""
    param_data: ParamData[Any] = deepcopy(request.getfixturevalue(request.param))
    return param_data


@pytest.fixture(name="param_data_child_name")
def fixture_param_data_child_name(param_data: ParamData[Any]) -> str | int | None:
    """Name of a child in the parameter data."""
    if isinstance(param_data, ParamDataFrame):
        return "path"
    if isinstance(param_data, SimpleParam):
        return "number"
    if isinstance(param_data, SubclassParam):
        return "second_number"
    if isinstance(param_data, ComplexParam):
        return "simple_param"
    if isinstance(param_data, ParamList):
        return None if len(param_data) == 0 else 4
    if isinstance(param_data, ParamDict):
        return None if len(param_data) == 0 else "simple_param"
    return None
