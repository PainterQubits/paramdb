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
from astropy.units import Quantity  # type: ignore # pylint: disable=import-error
from paramdb import ParamData, ParamDataclass, ParamList, ParamDict

DEFAULT_NUMBER = 1.23
DEFAULT_STRING = "test"


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
    param_data: ParamData | None = None


class CustomParamList(ParamList[Any]):
    """Custom parameter list subclass."""


class CustomParamDict(ParamDict[Any]):
    """Custom parameter dictionary subclass."""


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
