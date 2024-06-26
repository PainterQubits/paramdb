"""Base class for parameter files."""

from __future__ import annotations
from typing import TypeVar, Generic, cast
from abc import abstractmethod
from dataclasses import InitVar
from paramdb._param_data._dataclasses import ParamDataclass

try:
    import pandas as pd

    PANDAS_INSTALLED = True
except ImportError:
    PANDAS_INSTALLED = False

DataT = TypeVar("DataT")


class ParamFile(ParamDataclass, Generic[DataT]):
    """
    Subclass of :py:class:`ParamDataclass`.

    Base class for parameter file classes. Subclasses must implement the abstract
    methods :py:meth:`_save_data` and :py:meth:`_load_data`. For example::

        class ParamText(ParamFile[str]):
            def _save_data(self, path: str, data: str) -> None:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(data)

            def _load_data(self, path: str) -> str:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
    """

    path: str
    """Path to the file represented by this object."""
    initial_data: InitVar[DataT | None] = None

    # pylint: disable-next=arguments-differ
    def __post_init__(self, initial_data: DataT | None) -> None:
        super().__post_init__()
        if initial_data is not None:
            self.update_data(initial_data)

    @abstractmethod
    def _save_data(self, path: str, data: DataT) -> None:
        """Save the given data in a file at the given path."""

    @abstractmethod
    def _load_data(self, path: str) -> DataT:
        """Load data from the file at the given path."""

    @property
    def data(self) -> DataT:
        """Data stored in the file represented by this object."""
        return self._load_data(self.path)

    def update_data(self, data: DataT) -> None:
        """Update the data stored within the file represented by this object."""
        self._save_data(self.path, data)
        self._update_last_updated()


if PANDAS_INSTALLED:

    class ParamDataFrame(ParamFile[pd.DataFrame]):
        """
        Subclass of :py:class:`ParamFile`.

        Parameter data Pandas DataFrame, stored in a Pickle file. This class will only
        be defined if Pandas is installed.
        """

        def _load_data(self, path: str) -> pd.DataFrame:
            return cast(pd.DataFrame, pd.read_pickle(path))

        def _save_data(self, path: str, data: pd.DataFrame) -> None:
            data.to_pickle(path)
