"""Tests for the paramdb._param_data module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from paramdb._param_data import ParamData, Struct, Param


@dataclass
class CustomStruct(Struct):
    """Custom parameter structure."""

    number: float = 1.23
    string: str = "test"
    param_list: list[CustomParam] = field(default_factory=list)
    param_dict: dict[str, CustomParam] = field(default_factory=dict)


@dataclass
class CustomParam(Param):
    """Custom parameter."""

    number: float = 1.23
    string: str = "test"


def test_struct_isinstance() -> None:
    """Structure object is an instance of its superclasses."""
    struct = CustomStruct()
    assert isinstance(struct, Struct)
    assert isinstance(struct, ParamData)


def test_param_isinstance() -> None:
    """Parameter object is an instance of its superclasses."""
    param = CustomParam()
    assert isinstance(param, Param)
    assert isinstance(param, ParamData)


def test_struct_dot_access() -> None:
    """Struct properties can be accessed via dot notation."""
    struct = CustomStruct()
    assert struct.number == 1.23
    assert struct.string == "test"


def test_param_dot_access() -> None:
    """Parameter properties can be accessed via dot notation."""
    param = CustomParam()
    assert param.number == 1.23
    assert param.string == "test"


def test_param_bracket_access() -> None:
    """Parameter properties can be accessed via index brackets."""
    param = CustomParam()
    assert param["number"] == 1.23
    assert param["string"] == "test"


def test_struct_no_last_updated() -> None:
    """Structure object that contains no parameters has no last updated time."""
    struct = CustomStruct()
    assert struct.last_updated is None


def test_param_init_last_updated_default() -> None:
    """Parameter object initializes the last updated time to a default value of now."""
    start = datetime.now()
    param = CustomParam()
    end = datetime.now()
    last_updated = param.last_updated
    assert start <= last_updated <= end


def test_param_init_last_updated() -> None:
    """Parameter object initializes the last updated time to the given value."""
    last_updated = datetime.now()
    param = CustomParam(_last_updated=last_updated)
    assert param.last_updated == last_updated


# def test_param_update_last_updated() -> None:
#     """Parameter object initializes the last updated time to the given value."""
#     basic_param = CustomParam()

#     basic_param.number += 1
#     assert basic_param.last_updated == last_updated
