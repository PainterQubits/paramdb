"""Tests for the paramdb._database module."""

from typing import Any
from dataclasses import dataclass
from copy import deepcopy
import os
from datetime import datetime
from pathlib import Path
import pytest
from tests.helpers import (
    CustomStruct,
    CustomParam,
    CustomParamList,
    CustomParamDict,
    sleep_for_datetime,
)
from paramdb import ParamData, Struct, ParamList, ParamDict, ParamDB, CommitEntry
from paramdb._param_data._param_data import _param_classes


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
        == f"'{NotJSONSerializable.__name__}' object {repr(data)} is not JSON"
        " serializable, so the commit failed"
    )


def test_load_unknown_class_fails(db_path: str) -> None:
    """
    Fails to load an unknown class (i.e. one that is unknown to ParamDB). This simulates
    trying to load from a database in a program where a particular class is not properly
    defined.
    """

    class Unknown(Struct):
        """
        Class that is unknown to ParamDB. By default, it will get added to the private
        param class dictionary when created, but on the next line we manually delete it.
        """

    del _param_classes[Unknown.__name__]
    param_db = ParamDB[Unknown](db_path)
    data = Unknown()
    param_db.commit("Initial commit", data)
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
    param_data_loaded_most_recent = param_db.load()
    assert param_data_loaded_most_recent == param_data

    # Can load by commit ID
    param_data_loaded_first_commit = param_db.load(1)
    assert param_data_loaded_first_commit == param_data_loaded_most_recent


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

    @dataclass
    # pylint: disable-next=too-many-instance-attributes
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
    simple_param_loaded = param_db2.load()
    assert param == simple_param_loaded


def test_empty_commit_history(db_path: str) -> None:
    """Loads an empty commit history from an empty database."""
    param_db = ParamDB[CustomStruct](db_path)
    commit_history = param_db.commit_history()
    assert commit_history == []


def test_commit_history(db_path: str, param: CustomParam) -> None:
    """Loads the correct commit history for a series of commits."""
    starts = []
    ends = []
    param_db = ParamDB[CustomParam](db_path)

    # Make 10 commits
    for i in range(10):
        starts.append(datetime.now())
        sleep_for_datetime()
        param_db.commit(f"Commit {i}", param)
        sleep_for_datetime()
        ends.append(datetime.now())

    # Load commit history
    commit_history = param_db.commit_history()
    for i, (commit_entry, start, end) in enumerate(zip(commit_history, starts, ends)):
        assert isinstance(commit_entry, CommitEntry)
        assert commit_entry.message == f"Commit {i}"
        assert start < commit_entry.timestamp < end
