"""Tests for the paramdb._param_data_mixin module."""

import pytest
from tests.param_data import CustomParam, CustomStruct
from paramdb import ParentMixin, RootMixin


class ParamWithParent(ParentMixin[CustomStruct], CustomParam):
    """Custom parameter with a ``CustomStruct`` parent."""


class StructWithParent(ParentMixin[CustomStruct], CustomStruct):
    """Custom structure with a ``CustomStruct`` parent."""


class ParamWithRoot(RootMixin[CustomStruct], CustomParam):
    """Custom parameter with a ``CustomStruct`` root."""


class StructWithRoot(RootMixin[CustomStruct], CustomStruct):
    """Custom structure with a ``CustomStruct`` parent."""


@pytest.fixture(name="with_parent_class", params=[ParamWithParent, StructWithParent])
def fixture_with_parent_class(
    request: pytest.FixtureRequest,
) -> type[ParamWithParent | StructWithParent]:
    """Parameter data class with the parent mixin."""
    with_parent_class: type[ParamWithParent | StructWithParent] = request.param
    return with_parent_class


@pytest.fixture(name="with_root_class", params=[ParamWithRoot, StructWithRoot])
def fixture_with_root_class(
    request: pytest.FixtureRequest,
) -> type[ParamWithRoot | StructWithRoot]:
    """Parameter data class with the root mixin."""
    with_root_class: type[ParamWithRoot | StructWithRoot] = request.param
    return with_root_class


def test_no_parent_fails(
    with_parent_class: type[ParamWithParent | StructWithParent],
) -> None:
    """Fails to get the parent when there is no parent."""
    param_data = with_parent_class()
    with pytest.raises(ValueError) as exc_info:
        _ = param_data.parent
    assert str(exc_info.value) == f"'{with_parent_class.__name__}' object has no parent"


def test_not_initialized_parent_fails(
    with_parent_class: type[ParamWithParent | StructWithParent],
) -> None:
    """Fails to get the parent before the object is done initializing."""

    class AccessParentBeforeInitialized(with_parent_class):  # type: ignore
        """Class that tries to access the parent while initializing."""

        def __post_init__(self) -> None:
            _ = self.parent
            super().__post_init__()

    with pytest.raises(ValueError) as exc_info:
        _ = AccessParentBeforeInitialized()
    assert (
        str(exc_info.value)
        == f"cannot access parent of '{AccessParentBeforeInitialized.__name__}' object"
        " before it is done initializing"
    )


def test_not_initialized_root_fails(
    with_root_class: type[ParamWithRoot | StructWithRoot],
) -> None:
    """Fails to get the root before the object is done initializing."""

    class AccessRootBeforeInitialized(with_root_class):  # type: ignore
        """Class that tries to access the parent while initializing."""

        def __post_init__(self) -> None:
            _ = self.root
            super().__post_init__()

    with pytest.raises(ValueError) as exc_info:
        _ = AccessRootBeforeInitialized()
    assert (
        str(exc_info.value)
        == f"cannot access root of '{AccessRootBeforeInitialized.__name__}' object"
        " before it is done initializing"
    )


def test_gets_most_recent_parent(
    with_parent_class: type[ParamWithParent | StructWithParent],
) -> None:
    """
    Parameter data object with the parent mixin can get its most recent parent object.
    """
    param_data = with_parent_class()
    parent_struct1 = CustomStruct(param_data=param_data)
    assert param_data.parent is parent_struct1

    # Parent refers to the most recent parent
    parent_struct2 = CustomStruct(param_data=param_data)
    assert param_data.parent is parent_struct2


def test_gets_most_recent_root(
    with_root_class: type[ParamWithRoot | StructWithRoot],
) -> None:
    """
    Parameter data object with the root mixin can get the most recent root object,
    including when it has no parent, one parent, and a higher level parent.
    """
    # Object is its own root
    param_data = with_root_class()
    assert param_data.root is param_data

    # Object's parent is the root
    parent_struct = CustomStruct(param_data=param_data)
    assert param_data.root is parent_struct

    # Parent of object's parent is the root
    root_struct = CustomStruct(struct=parent_struct)
    assert param_data.root is root_struct
