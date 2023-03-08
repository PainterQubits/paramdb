"""Tests for the paramdb._param_data._collections module."""

from typing import Any
from copy import deepcopy
from datetime import datetime
import pytest
from tests.helpers import CustomParamList, CustomParamDict
from paramdb import ParamData, ParamList, ParamDict

ParamCollection = ParamList | ParamDict
Contents = list[Any] | dict[str, Any]
CustomParamCollection = CustomParamList | CustomParamDict


@pytest.fixture(
    name="param_collection",
    params=["param_list", "param_dict"],
)
def fixture_param_collection(request: pytest.FixtureRequest) -> ParamCollection:
    """Parameter collection."""
    param_collection: ParamCollection = deepcopy(request.getfixturevalue(request.param))
    return param_collection


@pytest.fixture(name="param_collection_type")
def fixture_param_collection_type(
    param_collection: ParamCollection,
) -> type[ParamCollection]:
    """Type of the parameter collection."""
    return type(param_collection)


@pytest.fixture(name="contents")
def fixture_contents(
    param_collection: ParamCollection, request: pytest.FixtureRequest
) -> Contents:
    """Contents of the parameter collection."""
    contents: Contents
    if isinstance(param_collection, ParamList):
        contents = request.getfixturevalue("param_list_contents")
    elif isinstance(param_collection, ParamDict):
        contents = request.getfixturevalue("param_dict_contents")
    return deepcopy(contents)


@pytest.fixture(name="contents_type")
def fixture_contents_type(contents: Contents) -> type[Contents]:
    """Type of the parameter collection contents."""
    return type(contents)


@pytest.fixture(name="custom_param_collection_type")
def fixture_custom_param_collection_type(
    param_collection: ParamCollection,
) -> type[CustomParamCollection]:
    """Custom parameter collection subclass."""
    if isinstance(param_collection, ParamList):
        return CustomParamList
    if isinstance(param_collection, ParamDict):
        return CustomParamDict


@pytest.fixture(name="custom_param_collection")
def fixture_param_collection_subclass(
    custom_param_collection_type: type[CustomParamCollection], contents: Any
) -> CustomParamCollection:
    """Custom parameter collection object."""
    return custom_param_collection_type(deepcopy(contents))


def test_param_collection_init_empty(
    param_collection_type: type[ParamCollection],
    contents_type: type[Contents],
) -> None:
    """Can initialize an empty parameter collection."""
    assert not contents_type(param_collection_type())


def test_param_list_init(
    param_list: ParamList[Any], param_list_contents: list[Any]
) -> None:
    """
    Can initialize a parameter list from a list, and its children correctly identify it
    as the parent.
    """
    assert list(param_list) == param_list_contents
    for item in param_list:
        if isinstance(item, ParamData):
            assert item.parent is param_list


def test_param_dict_init(
    param_dict: ParamDict[Any], param_dict_contents: dict[str, Any]
) -> None:
    """
    Can initialize a parameter dictionary from a dictionary, and its children correctly
    identify it as the parent.
    """
    assert dict(param_dict) == param_dict_contents
    for item in param_dict.values():
        if isinstance(item, ParamData):
            assert item.parent is param_dict


def test_param_collection_len_empty(
    param_collection_type: type[ParamCollection],
) -> None:
    """Can get the length of an empty parameter collection."""
    assert len(param_collection_type()) == 0


def test_param_collection_len_nonempty(
    param_collection: ParamCollection,
    contents: Contents,
) -> None:
    """Can get the length of a nonempty parameter collection."""
    assert len(param_collection) == len(contents)


def test_param_collection_eq(
    param_collection_type: type[ParamCollection],
    param_collection: ParamCollection,
    contents: Any,
) -> None:
    """
    Two parameter collections are equal if they have the same class and contents.
    """
    assert param_collection == param_collection_type(contents)


def test_param_collection_neq_contents(
    param_collection_type: type[ParamCollection],
    param_collection: ParamCollection,
) -> None:
    """
    Two parameter collections are not equal if they have the same class but different
    contents.
    """
    assert param_collection != param_collection_type()


def test_param_collection_neq_class(
    contents_type: type[Contents],
    param_collection: ParamCollection,
    custom_param_collection: CustomParamCollection,
    contents: Contents,
) -> None:
    """
    Two parameter collections are not equal if they have the same contents but different
    classes.
    """
    assert contents_type(param_collection) == contents_type(custom_param_collection)
    assert param_collection != custom_param_collection
    assert param_collection != contents


def test_param_collection_repr(
    param_collection_type: type[ParamCollection],
    param_collection: ParamCollection,
    contents: Any,
) -> None:
    """Parameter collection can be represented as a string."""
    assert repr(param_collection) == f"{param_collection_type.__name__}({contents})"


def test_param_collection_repr_subclass(
    custom_param_collection_type: type[CustomParamCollection],
    custom_param_collection: CustomParamCollection,
    contents: Any,
) -> None:
    """Custom parameter collection can be represented as a string."""
    assert (
        repr(custom_param_collection)
        == f"{custom_param_collection_type.__name__}({contents})"
    )


def test_param_collection_no_last_updated(
    param_collection_type: type[ParamCollection],
) -> None:
    """Empty parameter collection has no last updated time."""
    assert param_collection_type().last_updated is None


def test_param_list_last_updated(
    param_list: ParamList[Any],
    updated_param_data: ParamData,
    start: datetime,
    end: datetime,
) -> None:
    """Parameter list can correctly get the last updated time from its contents."""
    param_list.append(updated_param_data)
    assert param_list.last_updated is not None
    assert start < param_list.last_updated < end


def test_param_dict_last_updated(
    param_dict: ParamDict[Any],
    updated_param_data: ParamData,
    start: datetime,
    end: datetime,
) -> None:
    """Parameter list can correctly get the last updated time from its contents."""
    param_dict["param_data"] = updated_param_data
    assert param_dict.last_updated is not None
    assert start < param_dict.last_updated < end


def test_param_list_get_index(
    param_list: ParamList[Any], param_list_contents: list[Any]
) -> None:
    """Can get an item by index from a parameter list."""
    assert param_list[0] == param_list_contents[0]


def test_param_list_get_index_parent(param_list: ParamList[Any]) -> None:
    """Items gotten from a parameter list via an index have the correct parent."""
    assert param_list[2].parent is param_list


def test_param_list_get_slice(
    param_list: ParamList[Any], param_list_contents: list[Any]
) -> None:
    """Can get an item by slice from a parameter list."""
    assert isinstance(param_list[0:2], list)
    assert param_list[0:2] == param_list_contents[0:2]


def test_param_list_get_slice_parent(param_list: ParamList[Any]) -> None:
    """Items gotten from a parameter list via a slice have the correct parent."""
    sublist = param_list[2:4]
    assert sublist[0].parent is param_list
    assert sublist[1].parent is param_list


def test_param_list_set_index(param_list: ParamList[Any]) -> None:
    """Can set an item by index in a parameter list."""
    new_number = 4.56
    assert param_list[0] != new_number
    param_list[0] = new_number
    assert param_list[0] == new_number


def test_param_list_set_index_parent(
    param_list: ParamList[Any], param_data: ParamData
) -> None:
    """Parameter data added to a parameter list via indexing has the correct parent."""
    with pytest.raises(ValueError):
        _ = param_data.parent
    for _ in range(2):  # Run twice to check reassigning the same parameter data
        param_list[0] = param_data
        assert param_data.parent is param_list
    param_list[0] = None
    with pytest.raises(ValueError):
        _ = param_data.parent


def test_param_list_set_slice(param_list: ParamList[Any]) -> None:
    """Can set items by slice in a parameter list."""
    new_numbers = [4.56, 7.89]
    assert param_list[0:2] != new_numbers
    param_list[0:2] = new_numbers
    assert param_list[0:2] == new_numbers


def test_param_list_set_slice_parent(
    param_list: ParamList[Any], param_data: ParamData
) -> None:
    """Parameter data added to a parameter list via slicing has the correct parent."""
    for _ in range(2):  # Run twice to check reassigning the same parameter data
        param_list[0:2] = [None, param_data]
        assert param_data.parent is param_list
    param_list[0:2] = []
    with pytest.raises(ValueError):
        _ = param_data.parent


def test_param_list_insert(param_list: ParamList[Any]) -> None:
    """Can insert an item into a parameter list."""
    new_number = 4.56
    param_list.insert(1, new_number)
    assert param_list[1] == new_number


def test_param_list_insert_parent(
    param_list: ParamList[Any], param_data: ParamData
) -> None:
    """Parameter data added to a parameter list via insertion has the correct parent."""
    param_list.insert(1, param_data)
    assert param_data.parent is param_list


def test_param_list_del(
    param_list: ParamList[Any], param_list_contents: list[Any]
) -> None:
    """Can delete an item from a parameter list."""
    assert list(param_list) == param_list_contents
    del param_list[0]
    assert list(param_list) == param_list_contents[1:]


def test_param_list_del_parent(
    param_list: ParamList[Any], param_data: ParamData
) -> None:
    """An item deleted from a parameter list has no parent."""
    param_list.append(param_data)
    assert param_data.parent is param_list
    del param_list[-1]
    with pytest.raises(ValueError):
        _ = param_data.parent


def test_param_dict_key_error(param_dict: ParamDict[Any]) -> None:
    """Getting or deleting a nonexistent key raises a KeyError."""
    with pytest.raises(KeyError):
        _ = param_dict["nonexistent"]
    with pytest.raises(KeyError):
        del param_dict["nonexistent"]
    with pytest.raises(KeyError):
        _ = param_dict.nonexistent
    with pytest.raises(KeyError):
        del param_dict.nonexistent


def test_param_dict_attribute_error(param_dict: ParamDict[Any]) -> None:
    """Getting or deleting a nonexistent attribute raises an AttributeError."""
    with pytest.raises(AttributeError):
        _ = param_dict._nonexistent  # pylint: disable=protected-access
    with pytest.raises(AttributeError):
        del param_dict._nonexistent  # pylint: disable=protected-access


def test_param_dict_get(
    param_dict: ParamDict[Any], param_dict_contents: dict[str, Any]
) -> None:
    """
    Can get an item from a parameter dictionary using index bracket or dot notation.
    """
    assert param_dict["number"] == param_dict_contents["number"]
    assert param_dict.number == param_dict_contents["number"]


def test_param_dict_get_parent(param_dict: ParamDict[Any]) -> None:
    """An item gotten from a parameter dictionary has the correct parent."""
    assert param_dict["param"].parent is param_dict
    assert param_dict.param.parent is param_dict


def test_param_dict_set(param_dict: ParamDict[Any]) -> None:
    """Can set an item in a parameter list."""
    new_number_1 = 4.56
    new_number_2 = 7.89
    assert param_dict["number"] != new_number_1
    param_dict["number"] = new_number_1
    assert param_dict["number"] == new_number_1
    param_dict.number = new_number_2
    assert param_dict["number"] == new_number_2


def test_param_dict_set_parent(
    param_dict: ParamDict[Any], param_data: ParamData
) -> None:
    """Parameter data added to a parameter dictionary has the correct parent."""
    with pytest.raises(ValueError):
        _ = param_data.parent
    for _ in range(2):  # Run twice to check reassigning the same parameter data
        param_dict["param_data"] = param_data
        assert param_data.parent is param_dict
    param_dict["param_data"] = None
    with pytest.raises(ValueError):
        _ = param_data.parent


def test_param_dict_del_brackets(
    param_dict: ParamDict[Any], param_dict_contents: dict[str, Any]
) -> None:
    """Can delete items from a parameter dictionary."""
    assert dict(param_dict) == param_dict_contents
    del param_dict["number"]
    del param_dict.string
    del param_dict_contents["number"]
    del param_dict_contents["string"]
    assert dict(param_dict) == param_dict_contents


def test_param_dict_del_parent(
    param_dict: ParamDict[Any], param_data: ParamData
) -> None:
    """An item deleted from a parameter dictionary has no parent."""
    param_dict["param_data"] = param_data
    assert param_data.parent is param_dict
    del param_dict["param_data"]
    with pytest.raises(ValueError):
        _ = param_data.parent


def test_param_dict_iter(
    param_dict: ParamDict[Any], param_dict_contents: dict[str, Any]
) -> None:
    """A parameter dictionary correctly supports iteration."""
    for key, contents_key in zip(param_dict, param_dict_contents):
        assert key == contents_key
