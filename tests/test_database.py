"""Tests for the paramdb._database module."""

from typing import Any
from pathlib import Path
from pytest import fixture, raises
from tests.conftest import CustomStruct, CustomParam
from paramdb import CommitNotFoundError
from paramdb._database import ParamDB


def isolated_commit(db_path: str, message: str, data: Any) -> None:
    """
    Open an isolated connection to the database and commit the given data and message.
    This is useful to simulate committing in a separate program.
    """
    param_db = ParamDB[Any](db_path)
    param_db.commit(message, data)


@fixture(name="db_path")
def fixture_db_path(tmp_path: Path) -> str:
    """Return a path to use for a `ParamDB`."""
    return str(tmp_path / "param.db")


def test_create(db_path: str) -> None:
    """Parameter DB can be created."""
    ParamDB[Any](db_path)


def test_commit(db_path: str, param_data: CustomStruct | CustomParam) -> None:
    """Can commit parameters and structures to the database."""
    param_db = ParamDB[Any](db_path)
    param_db.commit("Initial commit", param_data)


def test_commit_complex(db_path: str, complex_struct: CustomStruct) -> None:
    """Can commit a complex structure to the database."""
    test_commit(db_path, complex_struct)


def test_commit_multiple(db_path: str, complex_struct: CustomStruct) -> None:
    """Can make multiple commits to the database."""
    param_db = ParamDB[CustomStruct](db_path)
    for i in range(10):
        param_db.commit(f"Commit {i}", complex_struct)


def test_fail_to_load_empty(db_path: str) -> None:
    """Loading from an empty DB raises an exception."""
    param_db = ParamDB[Any](db_path)
    with raises(CommitNotFoundError) as exc_info:
        param_db.load()
        assert (
            str(exc_info.value)
            == f"Cannot load parameter because database '{db_path}' has no commits."
        )


def test_load(db_path: str, param_data: CustomStruct | CustomParam) -> None:
    """Can load parameters and structures from the database."""
    test_commit(db_path, param_data)
    param_db = ParamDB[CustomStruct | CustomParam](db_path)
    param_data_loaded = param_db.load()
    assert param_data == param_data_loaded


def test_load_complex(db_path: str, complex_struct: CustomStruct) -> None:
    """Can load a complex structure from the database."""
    test_load(db_path, complex_struct)
