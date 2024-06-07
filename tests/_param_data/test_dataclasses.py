"""Tests for the paramdb._param_data._dataclasses module."""

from typing import Union, Any, cast
from copy import deepcopy
import pydantic
import pytest
from tests.helpers import (
    SimpleParam,
    NoTypeValidationParam,
    WithTypeValidationParam,
    NoAssignmentValidationParam,
    WithAssignmentValidationParam,
    SubclassParam,
    ComplexParam,
    capture_start_end_times,
)
from paramdb import ParamDataclass, ParamData

ParamDataclassObject = Union[
    SimpleParam,
    NoTypeValidationParam,
    WithTypeValidationParam,
    NoAssignmentValidationParam,
    WithAssignmentValidationParam,
    SubclassParam,
    ComplexParam,
]


@pytest.fixture(
    name="param_dataclass_object",
    params=[
        "simple_param",
        "no_type_validation_param",
        "with_type_validation_param",
        "no_assignment_validation_param",
        "with_assignment_validation_param",
        "subclass_param",
        "complex_param",
    ],
)
def fixture_param_dataclass_object(
    request: pytest.FixtureRequest,
) -> ParamDataclassObject:
    """Parameter data class object."""
    return cast(ParamDataclassObject, deepcopy(request.getfixturevalue(request.param)))


def test_param_dataclass_direct_instantiation_fails() -> None:
    """Fails to instantiate an object of type ``ParamDataclass``."""
    with pytest.raises(TypeError) as exc_info:
        ParamDataclass()
    assert (
        str(exc_info.value) == "only subclasses of ParamDataclass can be instantiated"
    )


def test_param_dataclass_get(
    param_dataclass_object: ParamDataclassObject, number: float, string: str
) -> None:
    """
    Parameter data class properties can be accessed via dot notation and index brackets.
    """
    assert param_dataclass_object.number == number
    assert param_dataclass_object.string == string
    assert param_dataclass_object["number"] == number
    assert param_dataclass_object["string"] == string


def test_param_dataclass_set(
    param_dataclass_object: ParamDataclassObject, number: float
) -> None:
    """
    Parameter data class properties can be updated via dot notation and index brackets.
    """
    param_dataclass_object.number += 1
    assert param_dataclass_object.number == number + 1
    param_dataclass_object["number"] -= 1
    assert param_dataclass_object.number == number


def test_param_dataclass_set_last_updated(
    param_dataclass_object: ParamDataclassObject,
) -> None:
    """
    A parameter data class object updates last updated timestamp when a field is set.
    """
    with capture_start_end_times() as times:
        param_dataclass_object.number = 4.56
    assert times.start < param_dataclass_object.last_updated.timestamp() < times.end


def test_param_dataclass_set_last_updated_non_field(
    param_dataclass_object: ParamDataclassObject,
) -> None:
    """
    A parameter data class object does not update last updated timestamp when a
    non-field parameter is set.
    """
    with capture_start_end_times() as times:
        # Use ParamData's setattr function to bypass Pydantic validation
        ParamData.__setattr__(param_dataclass_object, "non_field", 1.23)
    assert param_dataclass_object.last_updated.timestamp() < times.start


def test_param_dataclass_init_parent(complex_param: ComplexParam) -> None:
    """
    Parameter data class children correctly identify their parent after initialization.
    """
    assert complex_param.simple_param is not None
    assert complex_param.param_list is not None
    assert complex_param.param_dict is not None
    assert complex_param.simple_param.parent is complex_param
    assert complex_param.param_list.parent is complex_param
    assert complex_param.param_dict.parent is complex_param


def test_param_dataclass_set_parent(
    complex_param: ComplexParam, param_data: ParamData[Any]
) -> None:
    """Parameter data added to a structure has the correct parent."""
    with pytest.raises(ValueError):
        _ = param_data.parent
    for _ in range(2):  # Run twice to check reassigning the same parameter data
        complex_param.param_data = param_data
        assert param_data.parent is complex_param
    complex_param.param_data = None
    with pytest.raises(ValueError):
        _ = param_data.parent


def test_param_dataclass_init_wrong_type(
    param_dataclass_object: ParamDataclassObject,
) -> None:
    """
    Fails or succeeds to initialize a parameter object with a string value for a float
    field, depending on whether type validation is enabled.
    """
    string = "123"  # Use a string of a number to make sure strict mode is enabled
    param_dataclass_class = type(param_dataclass_object)
    if param_dataclass_class is NoTypeValidationParam:
        param = param_dataclass_class(number=string)  # type: ignore[arg-type]
        assert param.number == string  # type: ignore[comparison-overlap]
    else:
        with pytest.raises(pydantic.ValidationError) as exc_info:
            param_dataclass_class(number=string)  # type: ignore[arg-type]
        assert "Input should be a valid number" in str(exc_info.value)


def test_param_dataclass_init_default_wrong_type() -> None:
    """
    Fails or succeeds to initialize a parameter object with a default value having the
    wrong type
    """

    class DefaultWrongTypeParam(SimpleParam):
        """Parameter data class with a default value having the wrong type."""

        default_number: float = "123"  # type: ignore[assignment]

    with pytest.raises(pydantic.ValidationError) as exc_info:
        DefaultWrongTypeParam()
        assert "Input should be a valid number" in str(exc_info.value)


def test_param_dataclass_init_extra(
    param_dataclass_object: ParamDataclassObject, number: float
) -> None:
    """Fails to initialize a parameter object with an extra parameter."""
    param_dataclass_class = type(param_dataclass_object)
    exc_info: pytest.ExceptionInfo[Exception]
    if param_dataclass_class is NoTypeValidationParam:
        with pytest.raises(TypeError) as exc_info:
            param_dataclass_class(extra=number)  # type: ignore[call-arg]
        assert "__init__() got an unexpected keyword argument" in str(exc_info.value)
    else:
        with pytest.raises(pydantic.ValidationError) as exc_info:
            param_dataclass_class(extra=number)  # type: ignore[call-arg]
        assert "Unexpected keyword argument" in str(exc_info.value)


def test_param_dataclass_assignment_wrong_type(
    param_dataclass_object: ParamDataclassObject,
) -> None:
    """
    Fails or succeeds to assign a string value to a float field, depending on whether
    assignment validation is enabled.
    """
    string = "123"  # Use a string of a number to make sure strict mode is enabled
    if isinstance(
        param_dataclass_object, (NoTypeValidationParam, NoAssignmentValidationParam)
    ):
        param_dataclass_object.number = string  # type: ignore[assignment]
        assert (
            param_dataclass_object.number == string  # type: ignore[comparison-overlap]
        )
    else:
        with pytest.raises(pydantic.ValidationError) as exc_info:
            param_dataclass_object.number = string  # type: ignore[assignment]
        assert "Input should be a valid number" in str(exc_info.value)


def test_param_dataclass_assignment_extra(
    param_dataclass_object: ParamDataclassObject, number: float
) -> None:
    """
    Fails or succeeds to assign an extra parameter, depending on whether assignment
    validation is enabled.
    """
    if isinstance(
        param_dataclass_object, (NoTypeValidationParam, NoAssignmentValidationParam)
    ):
        param_dataclass_object.extra = number
        assert param_dataclass_object.extra == number
    else:
        with pytest.raises(pydantic.ValidationError) as exc_info:
            param_dataclass_object.extra = number
        assert "Object has no attribute 'extra'" in str(exc_info.value)
