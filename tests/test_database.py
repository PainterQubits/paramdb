"""Tests for the paramdb._database module."""

from typing import Any
from pathlib import Path
from pytest import fixture, raises
from paramdb import CommitNotFoundError
from paramdb._database import ParamDB


@fixture(name="db_path")
def fixture_db_path(tmp_path: Path) -> str:
    """Return a path to use for a `ParamDB`."""
    return str(tmp_path / "param.db")


def test_create_param_db(db_path: str) -> None:
    """Parameter DB can be created."""
    ParamDB[Any](db_path)


def test_fail_to_load_empty_db(db_path: str) -> None:
    """Loading from an empty DB raises an exception."""
    param_db = ParamDB[Any](db_path)
    with raises(CommitNotFoundError) as exc_info:
        param_db.load()
        assert (
            str(exc_info.value)
            == f"Cannot load parameter because database '{db_path}' has no commits."
        )
