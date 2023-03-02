"""Tests for the paramdb._param_data_mixin module."""

from dataclasses import dataclass
import pytest
from tests.param_data import CustomParam, CustomStruct
from paramdb import ParamData, ParentMixin, RootMixin


class ParamWithParent(ParentMixin[CustomStruct], CustomParam):
    """Custom parameter with a ``CustomStruct`` parent."""


class StructWithParent(ParentMixin[CustomStruct], CustomStruct):
    """Custom structure with a ``CustomStruct`` parent."""


class ParamWithRoot(RootMixin[CustomStruct], CustomParam):
    """Custom parameter with a ``CustomStruct`` root."""


class StructWithRoot(RootMixin[CustomStruct], CustomStruct):
    """Custom structure with a ``CustomStruct`` parent."""


Mixin = type[ParentMixin[CustomStruct]] | type[RootMixin[CustomStruct]]
WithParentClass = type[ParamWithParent] | type[StructWithParent]
WithRootClass = type[ParamWithRoot] | type[StructWithRoot]


@pytest.fixture(name="mixin", scope="module", params=[ParentMixin, RootMixin])
def fixture_mixin(request: pytest.FixtureRequest) -> Mixin:
    """Parent or root mixin."""
    mixin: Mixin = request.param
    return mixin


@pytest.fixture(
    name="with_parent_class", scope="module", params=[ParamWithParent, StructWithParent]
)
def fixture_with_parent_class(request: pytest.FixtureRequest) -> WithParentClass:
    """Parameter data class with the parent mixin."""
    with_parent_class: WithParentClass = request.param
    return with_parent_class


@pytest.fixture(
    name="with_root_class", scope="module", params=[ParamWithRoot, StructWithRoot]
)
def fixture_with_root_class(request: pytest.FixtureRequest) -> WithRootClass:
    """Parameter data class with the root mixin."""
    with_root_class: WithRootClass = request.param
    return with_root_class


def test_instantiate_mixin_fails(mixin: Mixin) -> None:
    """Fails to instantiate a mixin class directly."""
    with pytest.raises(TypeError) as exc_info:
        _ = mixin()
    assert (
        str(exc_info.value)
        == f"only subclasses of {mixin.__name__} can be instantiated"
    )


def test_instantiate_mixin_non_param_data_fails(mixin: Mixin) -> None:
    """Fails to instantiate a non-parameter-data class that uses a mixin."""

    class NonParamData(mixin):  # type: ignore
        """Not parameter data, but uses a mixin."""

    # Test a dataclass as well, since it overrides __init__ and could be a common
    # mistake since parameter data classes almost always use @dataclass
    @dataclass
    class NonParamDataDataclass(mixin):  # type: ignore
        """Dataclass that is not parameter data, but uses a mixin."""

    for non_param_data_class in [NonParamData, NonParamDataDataclass]:
        with pytest.raises(TypeError) as exc_info:
            _ = non_param_data_class()
        assert (
            str(exc_info.value)
            == f"'{non_param_data_class.__name__}' uses {mixin.__name__} but is not a"
            f" subclass of {ParamData.__name__}, so it cannot be instantiated"
        )


def test_no_parent_fails(with_parent_class: WithParentClass) -> None:
    """Fails to get the parent when there is no parent."""
    param_data = with_parent_class()
    with pytest.raises(ValueError) as exc_info:
        _ = param_data.parent
    assert str(exc_info.value) == f"'{with_parent_class.__name__}' object has no parent"


def test_not_initialized_parent_fails(with_parent_class: WithParentClass) -> None:
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


def test_not_initialized_root_fails(with_root_class: WithRootClass) -> None:
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


def test_gets_most_recent_parent(with_parent_class: WithParentClass) -> None:
    """
    Parameter data object with the parent mixin can get its most recent parent object.
    """
    param_data = with_parent_class()
    parent_struct1 = CustomStruct(param_data=param_data)
    assert param_data.parent is parent_struct1

    # Parent refers to the most recent parent
    parent_struct2 = CustomStruct(param_data=param_data)
    assert param_data.parent is parent_struct2


def test_gets_most_recent_root(with_root_class: WithRootClass) -> None:
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
