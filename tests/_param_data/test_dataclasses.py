"""Tests for the paramdb._param_data._dataclasses module."""

from typing import Union
from copy import deepcopy
import pytest
from tests.helpers import (
    SimpleParam,
    SubclassParam,
    ComplexParam,
    capture_start_end_times,
)
from paramdb import ParamDataclass, ParamData

ParamDataclassObject = Union[SimpleParam, SubclassParam, ComplexParam]


@pytest.fixture(
    name="param_dataclass_object",
    params=["simple_param", "subclass_param", "complex_param"],
)
def fixture_param_dataclass_object(
    request: pytest.FixtureRequest,
) -> ParamDataclassObject:
    """Parameter dataclass object."""
    param_dataclass_object: ParamDataclassObject = deepcopy(
        request.getfixturevalue(request.param)
    )
    return param_dataclass_object


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
    Parameter dataclass properties can be accessed via dot notation and index brackets.
    """
    assert param_dataclass_object.number == number
    assert param_dataclass_object.string == string
    assert param_dataclass_object["number"] == number
    assert param_dataclass_object["string"] == string


def test_param_dataclass_set(
    param_dataclass_object: ParamDataclassObject, number: float
) -> None:
    """
    Parameter dataclass properties can be updated via dot notation and index brackets.
    """
    param_dataclass_object.number += 1
    assert param_dataclass_object.number == number + 1
    param_dataclass_object["number"] -= 1
    assert param_dataclass_object.number == number


def test_param_dataclass_set_last_updated(
    param_dataclass_object: ParamDataclassObject,
) -> None:
    """
    A parameter dataclass object updates last updated timestamp when a field is set.
    """
    with capture_start_end_times() as times:
        param_dataclass_object.number = 4.56
    assert times.start < param_dataclass_object.last_updated.timestamp() < times.end


def test_param_dataclass_set_last_updated_non_field(
    param_dataclass_object: ParamDataclassObject,
) -> None:
    """
    A parameter dataclass object does not update last updated timestamp when a non-field
    parameter is set.
    """
    with capture_start_end_times() as times:
        param_dataclass_object.non_field = 1.23
    assert param_dataclass_object.last_updated.timestamp() < times.start


def test_param_dataclass_init_parent(complex_param: ComplexParam) -> None:
    """
    Parameter dataclass children correctly identify their parent after initialization.
    """
    assert complex_param.simple_param is not None
    assert complex_param.param_list is not None
    assert complex_param.param_dict is not None
    assert complex_param.simple_param.parent is complex_param
    assert complex_param.param_list.parent is complex_param
    assert complex_param.param_dict.parent is complex_param


def test_param_dataclass_set_parent(
    complex_param: ComplexParam, param_data: ParamData
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
