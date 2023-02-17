"""Tests for the paramdb._param_data module."""

from paramdb._param_data import ParamData, Struct, Param, _param_classes


def test_create_struct() -> None:
    """Can create a parameter structure."""

    class TestStruct(Struct):
        """Test parameter structure."""

    test_struct = TestStruct()
    assert isinstance(test_struct, Struct)
    assert isinstance(test_struct, ParamData)


def test_create_param() -> None:
    """Can create a parameter."""

    class TestParam(Param):
        """Test parameter."""

    test_param = TestParam()
    assert isinstance(test_param, Param)
    assert isinstance(test_param, ParamData)


def test_struct_no_last_updated() -> None:
    """Parameter object is an instance of `ParamData`."""

    class TestStruct(Struct):
        """Test parameter structure."""

    test_struct = TestStruct()
    assert test_struct.last_updated is None
