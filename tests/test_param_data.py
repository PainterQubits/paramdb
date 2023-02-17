"""Tests for the paramdb._param_data module."""

from datetime import datetime
from paramdb._param_data import ParamData, Struct, Param


class BasicStruct(Struct):
    """Empty parameter structure."""


class BasicParam(Param):
    """Empty parameter."""


def test_struct_isinstance() -> None:
    """Structure object is an instance of its superclasses."""
    basic_struct = BasicStruct()
    assert isinstance(basic_struct, Struct)
    assert isinstance(basic_struct, ParamData)


def test_param_isinstance() -> None:
    """Parameter object is an instance of its superclasses."""
    basic_param = BasicParam()
    assert isinstance(basic_param, Param)
    assert isinstance(basic_param, ParamData)


def test_struct_no_last_updated() -> None:
    """Structure object that contains no parameters has no last updated time."""
    basic_struct = BasicStruct()
    assert basic_struct.last_updated is None


def test_param_init_last_updated_default() -> None:
    """Parameter object initializes the last updated time to a default value of now."""
    start = datetime.now()
    basic_param = BasicParam()
    end = datetime.now()
    last_updated = basic_param.last_updated
    assert start <= last_updated <= end


def test_param_init_last_updated() -> None:
    """Parameter object initializes the last updated time to the given value."""
    last_updated = datetime.now()
    basic_param = BasicParam(_last_updated=last_updated)
    assert basic_param.last_updated == last_updated
