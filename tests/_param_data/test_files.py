"""Tests for the paramdb._param_data._files module."""

from typing import Any
import os
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from paramdb import ParamFile, ParamDataFrame
from tests.helpers import ParamTextFile, capture_start_end_times


def _data_frame(rows: int, columns: int) -> pd.DataFrame:
    return pd.DataFrame(
        np.random.randn(rows, columns), columns=[f"col{n}" for n in range(columns)]
    )


def _assert_data_equals(param_file: ParamFile[Any], data: Any) -> None:
    if isinstance(param_file, ParamDataFrame):
        pd.testing.assert_frame_equal(param_file.data, data)
    else:
        assert param_file.data == data


@pytest.fixture(name="param_file_path")
def fixture_param_file_path(tmp_path: Path) -> str:
    """Path to the parameter file."""
    return str(tmp_path / "param_file_data")


@pytest.fixture(
    name="param_file_path_data",
    params=[
        (ParamDataFrame, _data_frame(10, 10)),
        (ParamDataFrame, _data_frame(100, 10)),
        (ParamDataFrame, _data_frame(10, 100)),
        (ParamTextFile, ""),
        (ParamTextFile, "hello"),
        (ParamTextFile, repr(np.random.randn(20, 20))),
    ],
)
def fixture_param_file_and_data(
    request: pytest.FixtureRequest, param_file_path: str
) -> tuple[Any, ParamFile[Any]]:
    """Parameter file, path, and data."""
    param_file_class: type[ParamFile[Any]] = request.param[0]
    data = request.param[1]
    return data, param_file_class(param_file_path, data)


@pytest.fixture(name="data")
def fixture_data(param_file_path_data: tuple[Any, ParamFile[Any]]) -> Any:
    """Parameter file data."""
    return param_file_path_data[0]


@pytest.fixture(name="param_file")
def fixture_param_file(
    param_file_path_data: tuple[Any, ParamFile[Any]]
) -> ParamFile[Any]:
    """Parameter file."""
    return param_file_path_data[1]


@pytest.fixture(name="param_file_existing")
def fixture_param_file_existing(
    param_file: ParamFile[Any], param_file_path: str
) -> ParamFile[Any]:
    """Parameter file that points to existing data."""
    return type(param_file)(param_file_path)


@pytest.fixture(name="different_data")
def fixture_different_data(param_file: ParamFile[Any]) -> Any:
    """Data that is different than what is stored in the parameter file."""
    if isinstance(param_file, ParamDataFrame):
        return _data_frame(3, 3)
    return "different"


def test_param_file_saves_file(
    param_file_path: str, param_file: ParamFile[Any], data: pd.DataFrame
) -> None:
    """Parameter file saves data in a file."""
    os.remove(param_file_path)
    assert not os.path.exists(param_file_path)
    type(param_file)(param_file_path, data)
    assert os.path.exists(param_file_path)
    if isinstance(param_file, ParamDataFrame):
        pd.testing.assert_frame_equal(data, pd.read_csv(param_file_path))
    else:
        with open(param_file_path, "r", encoding="utf-8") as f:
            assert data == f.read()


def test_param_file_path(param_file_path: str, param_file: ParamFile[Any]) -> None:
    """Parameter file returns the correct path."""
    assert param_file.path == param_file_path


def test_param_file_data(param_file: ParamFile[Any], data: Any) -> None:
    """Parameter file loads the correct data."""
    _assert_data_equals(param_file, data)


def test_param_file_existing_data(
    param_file: ParamFile[Any],
    param_file_existing: ParamFile[Any],
    data: Any,
) -> None:
    """Parameter file pointing to existing data can load that data."""
    _assert_data_equals(param_file_existing, data)
    _assert_data_equals(param_file_existing, param_file.data)


def test_param_file_update_path(
    tmp_path: Path,
    param_file: ParamFile[Any],
    different_data: Any,
) -> None:
    """Parameter file can update its path."""
    different_data_frame_path = str(tmp_path / "different_param_file_data")
    type(param_file)(different_data_frame_path, different_data)
    with capture_start_end_times() as times:
        param_file.path = different_data_frame_path
    assert times.start <= param_file.last_updated.timestamp() <= times.end
    assert param_file.path == different_data_frame_path
    _assert_data_equals(param_file, different_data)


def test_param_file_update_data(
    param_file: ParamFile[Any], different_data: Any
) -> None:
    """Parameter file can update the data file it points to."""
    with capture_start_end_times() as times:
        param_file.update_data(different_data)
    assert times.start <= param_file.last_updated.timestamp() <= times.end
    _assert_data_equals(param_file, different_data)


def test_param_file_frame_existing_update_data(
    param_file: ParamFile[Any],
    param_file_existing: ParamFile[Any],
    different_data: Any,
) -> None:
    """
    Parameter file pointing to existing data can update data, which updates the data
    loaded by the original Parameter DataFrame.
    """
    with capture_start_end_times() as times:
        param_file_existing.update_data(different_data)
    assert times.start <= param_file_existing.last_updated.timestamp() <= times.end
    assert param_file.last_updated.timestamp() <= times.end
    _assert_data_equals(param_file_existing, different_data)
    _assert_data_equals(param_file, different_data)
