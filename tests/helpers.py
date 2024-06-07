"""Helper functions for paramdb tests."""

# In Python 3.9, Pylint complains that field() cannot be used in parameter dataclasses,
# so we disable the rule here.
# pylint: disable=invalid-field-call

from __future__ import annotations
from typing import Any
from collections.abc import Iterator
from dataclasses import dataclass, field
from contextlib import contextmanager
import time
import pydantic
from astropy.units import Quantity  # type: ignore[import-untyped]
from paramdb import (
    ParamData,
    ParamDataclass,
    ParamFile,
    ParamDataFrame,
    ParamList,
    ParamDict,
)
from paramdb._param_data._param_data import _ParamWrapper

DEFAULT_NUMBER = 1.23
DEFAULT_STRING = "test"


class ParamTextFile(ParamFile[str]):
    """Parameter text file, created using ``ParamFile``."""

    def _save_data(self, path: str, data: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)

    def _load_data(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


class EmptyParam(ParamDataclass):
    """Empty parameter data class"""


class SimpleParam(ParamDataclass):
    """Simple parameter data class."""

    number: float = DEFAULT_NUMBER
    number_init_false: float = field(init=False, default=DEFAULT_NUMBER)
    number_with_units: Quantity = Quantity(12, "m")
    string: str = DEFAULT_STRING


class NoTypeValidationParam(SimpleParam, type_validation=False):
    """Parameter dataclass without type validation."""


class WithTypeValidationParam(SimpleParam, type_validation=True):
    """Parameter dataclass with type validation re-enabled."""


class NoAssignmentValidationParam(
    SimpleParam, pydantic_config=pydantic.ConfigDict(validate_assignment=False)
):
    """Parameter dataclass without assignment validation."""


class WithAssignmentValidationParam(
    SimpleParam, pydantic_config=pydantic.ConfigDict(validate_assignment=True)
):
    """Parameter dataclass with assignment validation re-enabled."""


class SubclassParam(SimpleParam):
    """Parameter data class that is a subclass of another parameter data class."""

    second_number: float = DEFAULT_NUMBER


class ComplexParam(ParamDataclass):
    """Complex parameter data class."""

    number: float = DEFAULT_NUMBER
    number_init_false: float = field(init=False, default=DEFAULT_NUMBER)
    string: str = DEFAULT_STRING
    list: list[Any] = field(default_factory=list)
    dict: dict[str, Any] = field(default_factory=dict)
    param_data_frame: ParamDataFrame | None = None
    empty_param: EmptyParam | None = None
    simple_param: SimpleParam | None = None
    no_type_validation_param: NoTypeValidationParam | None = None
    with_type_validation_param: WithTypeValidationParam | None = None
    no_assignment_validation_param: NoAssignmentValidationParam | None = None
    with_assignment_validation_param: WithAssignmentValidationParam | None = None
    subclass_param: SubclassParam | None = None
    complex_param: ComplexParam | None = None
    param_list: ParamList[Any] = field(default_factory=ParamList)
    param_dict: ParamDict[Any] = field(default_factory=ParamDict)
    param_data: ParamData[Any] | None = None


class CustomParamList(ParamList[Any]):
    """Custom parameter list subclass."""


class CustomParamDict(ParamDict[Any]):
    """Custom parameter dictionary subclass."""


def assert_param_data_strong_equals(
    param_data: ParamData[Any], other_param_data: ParamData[Any], child_name: str
) -> None:
    """
    Assert that the given parameter data is equal to the other parameter data based on
    equality as well as stronger tests, such as last updated times and children.
    """
    # pylint: disable=protected-access
    assert param_data == other_param_data
    assert param_data.last_updated == other_param_data.last_updated
    assert param_data.to_dict() == other_param_data.to_dict()
    if child_name is not None:
        assert param_data.child_last_updated(
            child_name
        ) == other_param_data.child_last_updated(child_name)
        child = param_data._get_wrapped_child(child_name)
        other_child = other_param_data._get_wrapped_child(child_name)
        if isinstance(other_child, _ParamWrapper):
            assert isinstance(child, _ParamWrapper)
            assert child.value == other_child.value
        else:
            assert child == other_child
            assert child.parent == other_child.parent


@dataclass
class Times:
    """Start and end times captured by ``capture_start_end_times()``."""

    start: float
    end: float = 0


@contextmanager
def capture_start_end_times(wait_time: float = 10e-6) -> Iterator[Times]:
    """
    Record the start and end times within a with statement using this context manager.

    Also waits for a short amount of time after setting the start time and before
    setting the end time so that following calls to ``datetime.now()`` are different
    that then one being targeted. This is necessary because a ``datetime`` object is
    only precise to microseconds (see
    https://docs.python.org/3/library/datetime.html#datetime-objects), whereas computers
    execute instructions faster. So without waiting a few microseconds, it is difficult
    to verify that something is using the current time.
    """
    times = Times(time.time())
    time.sleep(wait_time)
    yield times
    time.sleep(wait_time)
    times.end = time.time()
