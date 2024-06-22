"""Parameter database backend using SQLAlchemy and SQLite."""

from __future__ import annotations
from typing import TypeVar, Generic, Literal, Any, overload
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from zstandard import ZstdCompressor, ZstdDecompressor
from sqlalchemy import Select, URL, create_engine, select, func
from sqlalchemy.orm import (
    sessionmaker,
    MappedAsDataclass,
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from paramdb._param_data._param_data import ParamData, _ParamWrapper, get_param_class

try:
    from astropy.units import Quantity  # type: ignore[import-untyped]

    _ASTROPY_INSTALLED = True
except ImportError:
    _ASTROPY_INSTALLED = False

DataT = TypeVar("DataT")
_SelectT = TypeVar("_SelectT", bound=Select[Any])


class ParamDBType:
    """
    Type strings corresponding to different object types in the JSON representation of
    the data in a ParamDB commit.
    """

    DATETIME = "datetime"
    """Type string for ``datetime.datetime`` objects."""
    QUANTITY = "Quantity"
    """Type string ``astropy.units.Quantity`` objects."""
    LIST = "list"
    """Type string ordinary lists."""
    DICT = "dict"
    """Type string ordinary dictionaries."""
    PARAM_DATA = "ParamData"
    """
    Type string for :py:class:`ParamData` objects.

    The JSON object should either include a parameter class name, or be None if wrapping
    a non-:py:class:`ParamData` with parameter metadata (e.g. a last updated time).
    """


def _compress(text: str) -> bytes:
    """Compress the given text using Zstandard."""
    return ZstdCompressor().compress(text.encode())


def _decompress(compressed_text: bytes) -> str:
    """Decompress the given compressed text using Zstandard."""
    return ZstdDecompressor().decompress(compressed_text).decode()


def _encode_json(obj: Any) -> Any:
    """
    Encode the given object and its children into a JSON-serializable format.

    See ``ParamDB.load()`` for the format specification.
    """
    if isinstance(obj, (int, float, bool, str)) or obj is None:
        return obj
    if isinstance(obj, datetime):
        return {"type": ParamDBType.DATETIME, "timestamp": obj.timestamp()}
    if _ASTROPY_INSTALLED and isinstance(obj, Quantity):
        return {"type": ParamDBType.QUANTITY, "value": obj.value, "unit": str(obj.unit)}
    if isinstance(obj, (list, tuple)):
        return {"type": ParamDBType.LIST, "data": [_encode_json(item) for item in obj]}
    if isinstance(obj, dict):
        return {
            "type": ParamDBType.DICT,
            "data": {key: _encode_json(value) for key, value in obj.items()},
        }
    if isinstance(obj, ParamData):
        encoded_json = {"type": ParamDBType.PARAM_DATA}
        if not isinstance(obj, _ParamWrapper):
            encoded_json |= {"className": type(obj).__name__}
        encoded_json |= {
            "lastUpdated": obj.last_updated.timestamp(),
            "data": _encode_json(obj.to_json()),
        }
        return encoded_json
    raise TypeError(
        f"'{type(obj).__name__}' object {repr(obj)} is not JSON serializable, so the"
        " commit failed"
    )


def _decode_json(json_data: Any) -> Any:
    """Reconstruct an object encoded by ``_json_encode()``."""
    if isinstance(json_data, dict):
        param_db_type = json_data["type"]
        if param_db_type == ParamDBType.DATETIME:
            return datetime.fromtimestamp(
                json_data["timestamp"], timezone.utc
            ).astimezone()
        if _ASTROPY_INSTALLED and param_db_type == ParamDBType.QUANTITY:
            return Quantity(value=json_data["value"], unit=json_data["unit"])
        if param_db_type == ParamDBType.LIST:
            return [_decode_json(item) for item in json_data["data"]]
        if param_db_type == ParamDBType.DICT:
            return {
                key: _decode_json(value) for key, value in json_data["data"].items()
            }
        if param_db_type == ParamDBType.PARAM_DATA:
            class_name = json_data.get("className", None)
            param_class = (
                _ParamWrapper if class_name is None else get_param_class(class_name)
            )
            if param_class is not None:
                return param_class.from_json(
                    _decode_json(json_data["data"]), json_data["lastUpdated"]
                )
            raise ValueError(
                f"ParamData class '{class_name}' is not known to ParamDB, so the load"
                " failed"
            )
    return json_data


def _encode(obj: Any, raw_json: bool) -> bytes:
    """
    Encode the given object into bytes that will be stored in the database.

    If ``raw_json`` is True, the object will be assumed to be a raw JSON string and will
    only be compressed; otherwise, the given object will be first encoded as a JSON
    string.
    """
    return _compress(
        obj if raw_json else json.dumps(_encode_json(obj), separators=(",", ":"))
    )


def _decode(data: bytes, raw_json: bool) -> Any:
    """
    Decode an object from the given data from the database.

    If ``raw_json`` is True, the raw JSON string will from the database will be
    returned; otherwise, the JSON data will be parsed and decoded into the corresponding
    classes.
    """
    json_str = _decompress(data)
    return json_str if raw_json else _decode_json(json.loads(json_str))


class _Base(MappedAsDataclass, DeclarativeBase):
    """Base class for defining SQLAlchemy declarative mapping classes."""


class _Snapshot(_Base):
    """Snapshot of the database."""

    __tablename__ = "snapshot"

    message: Mapped[str]
    """Commit message."""
    data: Mapped[bytes]
    """Compressed data."""
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    """Commit ID."""
    timestamp: Mapped[datetime] = mapped_column(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    """Datetime in UTC time (since this is how SQLite stores datetimes)."""


@dataclass(frozen=True)
class CommitEntry:
    """Entry for a commit containing the ID, message, and timestamp."""

    id: int
    """Commit ID."""
    message: str
    """Commit message."""
    timestamp: datetime
    """When this commit was created."""

    def __post_init__(self) -> None:
        # Add timezone info to timestamp datetime object
        timestamp_aware = self.timestamp.replace(tzinfo=timezone.utc).astimezone()
        super().__setattr__("timestamp", timestamp_aware)


@dataclass(frozen=True)
class CommitEntryWithData(CommitEntry, Generic[DataT]):
    """
    Subclass of :py:class:`CommitEntry`.

    Entry for a commit containing the ID, message, and timestamp, as well as the data.
    """

    data: DataT
    """Data contained in this commit."""


class ParamDB(Generic[DataT]):
    """
    Parameter database. The database is created in a file at the given path if it does
    not exist. To work with type checking, this class can be parameterized with a root
    data type ``DataT``. For example::

        from paramdb import ParamDataclass, ParamDB

        class Root(ParamDataclass):
            ...

        param_db = ParamDB[Root]("path/to/param.db")
    """

    def __init__(self, path: str):
        self._path = path
        self._engine = create_engine(URL.create("sqlite+pysqlite", database=path))
        self._Session = sessionmaker(self._engine)  # pylint: disable=invalid-name
        _Base.metadata.create_all(self._engine)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(path={self.path!r})"

    def _index_error(self, commit_id: int | None) -> IndexError:
        """
        Returns an ``IndexError`` to raise if the given commit ID was not found in the
        database.
        """
        return IndexError(
            f"cannot load most recent commit because database '{self._path}' has no"
            " commits"
            if commit_id is None
            else f"commit {commit_id} does not exist in database" f" '{self._path}'"
        )

    def _select_commit(self, select_stmt: _SelectT, commit_id: int | None) -> _SelectT:
        """
        Modify the given ``_Snapshot`` select statement to return the commit specified
        by the given commit ID, or the latest commit if the commit ID is None.
        """
        return (
            select_stmt.order_by(_Snapshot.id.desc()).limit(1)  # Most recent commit
            if commit_id is None
            else select_stmt.where(_Snapshot.id == commit_id)  # Specified commit
        )

    def _select_slice(
        self, select_stmt: _SelectT, start: int | None, end: int | None
    ) -> _SelectT:
        """
        Modify the given Snapshot select statement to sort by commit ID and return the
        slice specified by the given start and end indices.
        """
        num_commits = self.num_commits
        start = 0 if start is None else start
        end = num_commits if end is None else end
        start = max(start + num_commits, 0) if start < 0 else start
        end = max(end + num_commits, 0) if end < 0 else end
        return (
            select_stmt.order_by(_Snapshot.id).offset(start).limit(max(end - start, 0))
        )

    @property
    def path(self) -> str:
        """Path of the database file."""
        return self._path

    @overload
    def commit(
        self,
        message: str,
        data: DataT,
        timestamp: datetime | None = None,
        *,
        raw_json: Literal[False] = False,
    ) -> CommitEntry: ...

    @overload
    def commit(
        self,
        message: str,
        data: str,
        timestamp: datetime | None = None,
        *,
        raw_json: Literal[True],
    ) -> CommitEntry: ...

    def commit(
        self,
        message: str,
        data: Any,
        timestamp: datetime | None = None,
        *,
        raw_json: bool = False,
    ) -> CommitEntry:
        """
        Commit the given data to the database with the given message and return a commit
        entry for the new commit.

        By default, the timestamp will be set to the current time. If a timestamp is
        given, it is used instead. Naive datetimes will be assumed to be in UTC time.

        By default, the given data will be converted into a JSON string, which is then
        saved to the database; however, if ``raw_json`` is True, then the given data is
        assumed to already be a JSON string in the format specified by
        :py:meth:`ParamDB.load`. Note that any string will be accepted, so be careful
        using this option. If the format is incorrect, loading this particular commit
        may fail.
        """
        with self._Session.begin() as session:
            kwargs: dict[str, Any] = {
                "message": message,
                "data": _encode(data, raw_json),
            }
            if timestamp is not None:
                utc_offset = timestamp.utcoffset()
                kwargs["timestamp"] = (
                    timestamp  # Assume naive datetime is already in UTC
                    if utc_offset is None
                    else timestamp.replace(tzinfo=None) - utc_offset  # Convert to UTC
                )
            snapshot = _Snapshot(**kwargs)
            session.add(snapshot)
            session.flush()  # Flush so the commit ID and timestamp are filled in
            return CommitEntry(snapshot.id, snapshot.message, snapshot.timestamp)

    @property
    def num_commits(self) -> int:
        """Number of commits in the database."""
        # pylint: disable-next=not-callable
        select_stmt = select(func.count()).select_from(_Snapshot)
        with self._Session() as session:
            count = session.scalar(select_stmt)
        return count if count is not None else 0

    @overload
    def load(
        self, commit_id: int | None = None, *, raw_json: Literal[False] = False
    ) -> DataT: ...

    @overload
    def load(self, commit_id: int | None = None, *, raw_json: Literal[True]) -> str: ...

    def load(self, commit_id: int | None = None, *, raw_json: bool = False) -> Any:
        """
        Load and return data from the database. If a commit ID is given, load from that
        commit; otherwise, load from the most recent commit. Raise an ``IndexError`` if
        the specified commit does not exist. Note that commit IDs begin at 1.

        By default, objects are reconstructed, which requires the relevant parameter
        data classes to be defined in the current program. However, if ``raw_json``
        is True, the JSON data is returned directly from the database as a string.
        The format of the JSON data is as follows::

            json_data =
                | int
                | float
                | bool
                | str
                | None
                | {"type": "datetime", "timestamp": float}
                | {"type": "Quantity", "value": float, "unit": str}
                | {"type": "list", "data": [json_data, ...]}
                | {"type": "dict", "data": {str: json_data, ...}}
                | {"type": "ParamData", "lastUpdated": float, "data": json_data}
                | {"type": "ParamData", "className": str, "lastUpdated": float, "data": json_data}
        """  # noqa: E501
        select_stmt = self._select_commit(select(_Snapshot.data), commit_id)
        with self._Session() as session:
            data = session.scalar(select_stmt)
        if data is None:
            raise self._index_error(commit_id)
        return _decode(data, raw_json)

    def load_commit_entry(self, commit_id: int | None = None) -> CommitEntry:
        """
        Load and return a commit entry from the database. If a commit ID is given, load
        that commit entry; otherwise, load the most recent commit entry. Raise an
        ``IndexError`` if the specified commit does not exist. Note that commit IDs
        begin at 1.
        """
        select_stmt = self._select_commit(
            select(_Snapshot.id, _Snapshot.message, _Snapshot.timestamp), commit_id
        )
        with self._Session() as session:
            commit_entry = session.execute(select_stmt).mappings().first()
        if commit_entry is None:
            raise self._index_error(commit_id)
        return None if commit_entry is None else CommitEntry(**commit_entry)

    def commit_history(
        self, start: int | None = None, end: int | None = None
    ) -> list[CommitEntry]:
        """
        Retrieve the commit history as a list of :py:class:`CommitEntry` objects between
        the provided start and end indices, which work like slicing a Python list.
        """
        select_stmt = self._select_slice(
            select(_Snapshot.id, _Snapshot.message, _Snapshot.timestamp), start, end
        )
        with self._Session() as session:
            entries = session.execute(select_stmt).mappings()
        return [CommitEntry(**dict(row_mapping)) for row_mapping in entries]

    @overload
    def commit_history_with_data(
        self,
        start: int | None = None,
        end: int | None = None,
        *,
        raw_json: Literal[False] = False,
    ) -> list[CommitEntryWithData[DataT]]: ...

    @overload
    def commit_history_with_data(
        self,
        start: int | None = None,
        end: int | None = None,
        *,
        raw_json: Literal[True],
    ) -> list[CommitEntryWithData[str]]: ...

    def commit_history_with_data(
        self,
        start: int | None = None,
        end: int | None = None,
        *,
        raw_json: bool = False,
    ) -> list[CommitEntryWithData[Any]]:
        """
        Retrieve the commit history with data as a list of
        :py:class:`CommitEntryWithData` objects between the provided start and end
        indices, which work like slicing a Python list.

        See :py:meth:`ParamDB.load` for the behavior of ``raw_json``.
        """
        with self._Session() as session:
            select_stmt = self._select_slice(select(_Snapshot), start, end)
            snapshots = session.scalars(select_stmt)
            return [
                CommitEntryWithData(
                    snapshot.id,
                    snapshot.message,
                    snapshot.timestamp,
                    _decode(snapshot.data, raw_json),
                )
                for snapshot in snapshots
            ]

    def dispose(self) -> None:
        """
        Dispose of the underlying SQLAlchemy connection pool. Usually this method does
        not need to be called since disposal happens automatically when the database is
        garbage collected, and typically only one global database object should be used.
        However, there are certain cases where it is useful to fully dispose of a
        database before the end of the program, such as when running a test suite. See
        https://docs.sqlalchemy.org/en/20/core/connections.html#engine-disposal for more
        information.
        """
        self._engine.dispose()
