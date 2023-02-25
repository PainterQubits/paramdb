"""Tests for the paramdb._database module."""

from typing import Any
import os
from datetime import datetime
from pytest import raises
from tests.conftest import CustomStruct, CustomParam
from tests.helpers import sleep_for_datetime
from paramdb import Struct, ParamDB, CommitEntry, CommitNotFoundError
from paramdb._param_data import _param_classes


def test_create(db_path: str) -> None:
    """Parameter DB can be created."""
    assert not os.path.exists(db_path)
    ParamDB[Any](db_path)
    assert os.path.exists(db_path)


def test_commit_not_json_serializable_fails(db_path: str) -> None:
    """Fails to commit a class that ParamDB does not know how to convert to JSON."""

    class NotJSONSerializable:  # pylint: disable=too-few-public-methods
        """Class that ParamDB does not know how to serialize as JSON."""

    param_db = ParamDB[NotJSONSerializable](db_path)
    data = NotJSONSerializable()
    with raises(TypeError) as exc_info:
        param_db.commit("Initial commit", data)
    assert str(exc_info.value) == f"{repr(data)} is not JSON serializable"


def test_load_unknown_class_fails(db_path: str) -> None:
    """
    Fails to load an unknown class (i.e. one that is unknown to ParamDB). This simulates
    trying to load from a database in a program where a particular class is not properly
    defined.
    """

    class Unknown(Struct):  # pylint: disable=too-few-public-methods
        """
        Class that is unknown to ParamDB. By default, it will get added to the private
        param class dictionary when created, but on the next line we manually delete it.
        """

    del _param_classes[Unknown.__name__]
    param_db = ParamDB[Unknown](db_path)
    data = Unknown()
    param_db.commit("Initial commit", data)
    with raises(ValueError) as exc_info:
        param_db.load()
    assert str(exc_info.value) == f"class '{Unknown.__name__}' is not known to paramdb"


def test_load_empty_fails(db_path: str) -> None:
    """Fails to loading from an empty database."""
    param_db = ParamDB[Any](db_path)
    with raises(CommitNotFoundError) as exc_info:
        param_db.load()
    assert (
        str(exc_info.value)
        == f"cannot load most recent data because database '{db_path}' has no commits"
    )


def test_load_nonexistent_commit_fails(db_path: str) -> None:
    """Fails to loading a commit that does not exist."""
    param_db = ParamDB[Any](db_path)
    with raises(CommitNotFoundError) as exc_info:
        param_db.load(1)
    assert str(exc_info.value) == f"commit 1 does not exist in database '{db_path}'"
    param_db.commit("Initial commit", {})
    with raises(CommitNotFoundError) as exc_info:
        param_db.load(100)
    assert str(exc_info.value) == f"commit 100 does not exist in database '{db_path}'"


def test_commit_load(db_path: str, param_data: CustomStruct | CustomParam) -> None:
    """Can commit and load parameters and structures."""
    param_db = ParamDB[CustomStruct | CustomParam](db_path)
    param_db.commit("Initial commit", param_data)

    # Can load the most recent commit
    param_data_loaded_most_recent = param_db.load()
    assert param_data_loaded_most_recent == param_data

    # Can load by commit ID
    param_data_loaded_first_commit = param_db.load(1)
    assert param_data_loaded_first_commit == param_data_loaded_most_recent


def test_commit_load_complex(db_path: str, complex_struct: CustomStruct) -> None:
    """Can commit and load a complex structure."""
    test_commit_load(db_path, complex_struct)


def test_commit_load_multiple(db_path: str) -> None:
    """Can commit multiple times and load previous commits."""
    param_db = ParamDB[CustomParam](db_path)

    # Commit several different parameters
    params = [CustomParam(number=i + 1) for i in range(10)]
    for i, param in enumerate(params):
        param_db.commit(f"Commit {i + 1}", param)

    # Load them back
    for i, param in enumerate(params):
        param_loaded = param_db.load(i + 1)
        assert param_loaded == param


def test_separate_connections(db_path: str, complex_struct: CustomStruct) -> None:
    """
    Can commit and load using separate connections. This simulates committing to the
    database in one program and loading in another program at a later time.
    """
    # Commit using one connection
    param_db1 = ParamDB[CustomStruct](db_path)
    param_db1.commit("Initial commit", complex_struct)
    del param_db1

    # Load back using another connection
    param_db2 = ParamDB[CustomStruct](db_path)
    complex_struct_loaded = param_db2.load()
    assert complex_struct == complex_struct_loaded


def test_empty_commit_history(db_path: str) -> None:
    """Loads an empty commit history for an empty database."""
    param_db = ParamDB[CustomStruct](db_path)
    commit_history = param_db.commit_history()
    assert commit_history == []


def test_commit_history(db_path: str, complex_struct: CustomStruct) -> None:
    """Loads the correct commit history for a series of commits."""
    starts = []
    ends = []
    param_db = ParamDB[CustomStruct](db_path)

    # Make several commits
    for i in range(10):
        starts.append(datetime.now())
        sleep_for_datetime()
        param_db.commit(f"Commit {i}", complex_struct)
        sleep_for_datetime()
        ends.append(datetime.now())

    # Load commit history
    commit_history = param_db.commit_history()
    for i, (commit_entry, start, end) in enumerate(zip(commit_history, starts, ends)):
        assert isinstance(commit_entry, CommitEntry)
        assert commit_entry.message == f"Commit {i}"
        assert start < commit_entry.timestamp < end
