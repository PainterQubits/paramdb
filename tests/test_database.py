"""Tests for the paramdb._database module."""

from typing import Any
from copy import deepcopy
import os
import time
from pathlib import Path
import pytest
from tests.helpers import (
    CustomStruct,
    CustomParam,
    CustomParamList,
    CustomParamDict,
    sleep_for_datetime,
)
from paramdb import (
    ParamData,
    Struct,
    ParamList,
    ParamDict,
    ParamDB,
    CommitEntry,
    CLASS_NAME_KEY,
)
from paramdb._param_data._param_data import _param_classes


class Unknown(Struct):
    """
    Class that is unknown to ParamDB. By default, it will get added to the private
    param class dictionary when created, but on the next line we manually delete it.
    """


del _param_classes[Unknown.__name__]


@pytest.fixture(name="db_path")
def fixture_db_path(tmp_path: Path) -> str:
    """Return a path to use for a `ParamDB`."""
    return str(tmp_path / "param.db")


def test_create_database(db_path: str) -> None:
    """Parameter DB can be created on disk."""
    assert not os.path.exists(db_path)
    ParamDB[Any](db_path)
    assert os.path.exists(db_path)


def test_commit_not_json_serializable_fails(db_path: str) -> None:
    """Fails to commit a class that ParamDB does not know how to convert to JSON."""

    class NotJSONSerializable:
        """Class that ParamDB does not know how to serialize as JSON."""

    param_db = ParamDB[NotJSONSerializable](db_path)
    data = NotJSONSerializable()
    with pytest.raises(TypeError) as exc_info:
        param_db.commit("Initial commit", data)
    assert (
        str(exc_info.value)
        == f"'{NotJSONSerializable.__module__}.{NotJSONSerializable.__name__}' object"
        f" {repr(data)} is not JSON serializable, so the commit failed"
    )


def test_load_unknown_class_fails(db_path: str) -> None:
    """
    Fails to load an instance of an unknown class (i.e. one that is unknown to ParamDB).
    This simulates trying to load from a database in a program where a particular class
    is not properly defined.
    """
    param_db = ParamDB[Unknown](db_path)
    param_db.commit("Initial commit", Unknown())
    with pytest.raises(ValueError) as exc_info:
        param_db.load()
    assert (
        str(exc_info.value)
        == f"class '{Unknown.__name__}' is not known to ParamDB, so the load failed"
    )


def test_load_empty_fails(db_path: str) -> None:
    """Fails to loading from an empty database."""
    param_db = ParamDB[Any](db_path)
    with pytest.raises(IndexError) as exc_info:
        param_db.load()
    assert (
        str(exc_info.value)
        == f"cannot load most recent commit because database '{db_path}' has no commits"
    )


def test_load_nonexistent_commit_fails(db_path: str) -> None:
    """Fails to loading a commit that does not exist."""
    # Empty database
    param_db = ParamDB[Any](db_path)
    with pytest.raises(IndexError) as exc_info:
        param_db.load(1)
    assert str(exc_info.value) == f"commit 1 does not exist in database '{db_path}'"

    # Database with one commit
    param_db.commit("Initial commit", {})
    with pytest.raises(IndexError) as exc_info:
        param_db.load(100)
    assert str(exc_info.value) == f"commit 100 does not exist in database '{db_path}'"


def test_commit_and_load(db_path: str, param_data: ParamData) -> None:
    """Can commit and load parameter data."""
    param_db = ParamDB[ParamData](db_path)
    param_db.commit("Initial commit", param_data)

    # Can load the most recent commit
    sleep_for_datetime()
    param_data_loaded_most_recent = param_db.load()
    assert param_data_loaded_most_recent == param_data
    assert param_data_loaded_most_recent.last_updated == param_data.last_updated

    # Can load by commit ID
    sleep_for_datetime()
    param_data_loaded_first_commit = param_db.load(1)
    assert param_data_loaded_first_commit == param_data_loaded_most_recent
    assert (
        param_data_loaded_first_commit.last_updated
        == param_data_loaded_most_recent.last_updated
    )


def test_load_classes_false(db_path: str, param_data: ParamData) -> None:
    """Can load data as dictionaries if load_classes is false."""
    param_db = ParamDB[ParamData](db_path)
    param_db.commit("Initial commit", param_data)
    data_loaded = param_db.load(load_classes=False)

    # Check that loaded dictionary has the correct type and keys
    assert isinstance(data_loaded, dict)
    assert data_loaded.pop(CLASS_NAME_KEY) == type(param_data).__name__
    param_data_dict = param_data.to_dict()
    assert data_loaded.keys() == param_data_dict.keys()

    # Check that loaded dictionary has the correct values
    for key, value in data_loaded.items():
        value_from_param_data = param_data_dict[key]
        if isinstance(value_from_param_data, ParamData):
            assert value.pop(CLASS_NAME_KEY) == type(value_from_param_data).__name__
            assert value.keys() == value_from_param_data.to_dict().keys()
        else:
            if isinstance(value, list):
                assert isinstance(value_from_param_data, list)
                assert len(value) == len(value_from_param_data)
            elif isinstance(value, dict):
                assert isinstance(value_from_param_data, dict)
                assert value.keys() == value_from_param_data.keys()
            else:
                assert value == value_from_param_data


def test_load_classes_false_unknown_class(db_path: str) -> None:
    """
    Can load an instance of an unknown class (i.e. one that is unknown to ParamDB).
    """
    param_db = ParamDB[Unknown](db_path)
    param_db.commit("Initial commit", Unknown())
    data_loaded = param_db.load(load_classes=False)
    assert data_loaded.pop(CLASS_NAME_KEY) == Unknown.__name__


# pylint: disable-next=too-many-arguments
def test_commit_and_load_complex(
    db_path: str,
    number: float,
    string: str,
    param_list_contents: list[Any],
    param_dict_contents: dict[str, Any],
    param: CustomParam,
    struct: CustomStruct,
    param_list: ParamList[Any],
    param_dict: ParamDict[Any],
) -> None:
    """Can commit and load a complex parameter structure."""

    class Root(Struct):
        """Complex root structure to test the database."""

        number: float
        string: str
        list: list[Any]
        dict: dict[str, Any]
        param: CustomParam
        struct: CustomStruct
        param_list: ParamList[Any]
        param_dict: ParamDict[Any]
        custom_param_list: CustomParamList
        custom_param_dict: CustomParamDict

    root = Root(
        number=number,
        string=string,
        list=param_list_contents,
        dict=param_dict_contents,
        param=param,
        struct=struct,
        param_list=param_list,
        param_dict=param_dict,
        custom_param_list=CustomParamList(deepcopy(param_list_contents)),
        custom_param_dict=CustomParamDict(deepcopy(param_dict_contents)),
    )
    param_db = ParamDB[Root](db_path)
    param_db.commit("Initial commit", root)
    root_loaded = param_db.load()
    assert root_loaded == root
    assert root_loaded.last_updated == root.last_updated


def test_commit_load_multiple(db_path: str) -> None:
    """Can commit multiple times and load previous commits."""
    param_db = ParamDB[CustomParam](db_path)

    # Make 10 commits
    params = [CustomParam(number=i + 1) for i in range(10)]
    for i, param in enumerate(params):
        param_db.commit(f"Commit {i + 1}", param)

    # Load and verify the commits
    for i, param in enumerate(params):
        param_loaded = param_db.load(i + 1)
        assert param_loaded == param
        assert param_loaded.last_updated == param.last_updated


def test_separate_connections(db_path: str, param: CustomParam) -> None:
    """
    Can commit and load using separate connections. This simulates committing to the
    database in one program and loading in another program at a later time.
    """
    # Commit using one connection
    param_db1 = ParamDB[CustomParam](db_path)
    param_db1.commit("Initial commit", param)
    del param_db1

    # Load back using another connection
    param_db2 = ParamDB[CustomParam](db_path)
    param_loaded = param_db2.load()
    assert param == param_loaded
    assert param.last_updated == param_loaded.last_updated


def test_empty_num_commits(db_path: str) -> None:
    """An empty database has no commits according to num_commits."""
    param_db = ParamDB[CustomStruct](db_path)
    assert param_db.num_commits == 0


def test_num_commits(db_path: str, param: CustomParam) -> None:
    """A database with multiple commits has the correct value for num_commits."""
    param_db = ParamDB[CustomParam](db_path)
    for i in range(10):
        param_db.commit(f"Commit {i}", param)
    assert param_db.num_commits == 10


def test_empty_commit_history(db_path: str) -> None:
    """Loads an empty commit history from an empty database."""
    param_db = ParamDB[CustomStruct](db_path)
    assert param_db.commit_history() == []


def test_empty_commit_history_slice(db_path: str) -> None:
    """Correctly slices an empty commit history."""
    param_db = ParamDB[CustomStruct](db_path)
    assert param_db.commit_history(0) == []
    assert param_db.commit_history(0, 10) == []
    assert param_db.commit_history(-10) == []
    assert param_db.commit_history(-10, -5) == []


def test_commit_history(db_path: str, param: CustomParam) -> None:
    """Loads the correct commit history for a series of commits."""
    param_db = ParamDB[CustomParam](db_path)
    starts: list[float] = []
    ends: list[float] = []

    # Make 10 commits
    for i in range(10):
        starts.append(time.time())
        sleep_for_datetime()
        param_db.commit(f"Commit {i}", param)
        sleep_for_datetime()
        ends.append(time.time())

    # Load commit history
    commit_history = param_db.commit_history()
    for i, (commit_entry, start, end) in enumerate(zip(commit_history, starts, ends)):
        assert isinstance(commit_entry, CommitEntry)
        assert commit_entry.message == f"Commit {i}"
        assert start < commit_entry.timestamp.timestamp() < end


def test_commit_history_slice(db_path: str, param: CustomParam) -> None:
    """Loads the correct commit history for a series of commits."""
    param_db = ParamDB[CustomParam](db_path)

    # Make 10 commits
    for i in range(10):
        param_db.commit(f"Commit {i}", param)

    # Load slices of commit history
    commit_history = param_db.commit_history()
    start_ends = [
        (None, None),
        (0, None),
        (3, None),
        (9, None),
        (10, None),
        (20, None),
        (-1, None),
        (-3, None),
        (-10, None),
        (-20, None),
        (None, 10),
        (None, 7),
        (None, 1),
        (None, 0),
        (None, 20),
        (None, -1),
        (None, -3),
        (None, -9),
        (None, -10),
        (None, -20),
        (0, 10),
        (0, 7),
        (0, 20),
        (3, 10),
        (3, 7),
        (3, 20),
        (-20, 7),
        (-20, 20),
        (7, 3),
        (-6, -3),
        (-3, -6),
    ]
    for start, end in start_ends:
        assert param_db.commit_history(start, end) == commit_history[start:end]
