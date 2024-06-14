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


class ParamDBKey:
    """
    Keys corresponding to different object types in the JSON representation of the data
    in a ParamDB commit.
    """

    DATETIME = "t"
    """Key for ``datetime.datetime`` objects."""
    QUANTITY = "q"
    """Key for ``astropy.units.quantity`` objects."""
    LIST = "l"
    """Key for ordinary lists."""
    DICT = "d"
    """Key for ordinary dictionaries."""
    WRAPPER = "w"
    """
    Key for non-:py:class:`ParamData` children of :py:class:`ParamData` objects, since
    they are wrapped with additional metadata, such as a last updated time.
    """
    PARAM = "p"
    """Key for :py:class:`ParamData` objects."""


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
        return [ParamDBKey.DATETIME, obj.timestamp()]
    if _ASTROPY_INSTALLED and isinstance(obj, Quantity):
        return [ParamDBKey.QUANTITY, obj.value, str(obj.unit)]
    if isinstance(obj, (list, tuple)):
        return [ParamDBKey.LIST, [_encode_json(item) for item in obj]]
    if isinstance(obj, dict):
        return [
            ParamDBKey.DICT,
            {key: _encode_json(value) for key, value in obj.items()},
        ]
    if isinstance(obj, ParamData):
        timestamp_and_json = [
            obj.last_updated.timestamp(),
            _encode_json(obj.to_json()),
        ]
        if isinstance(obj, _ParamWrapper):
            return [ParamDBKey.WRAPPER, *timestamp_and_json]
        return [ParamDBKey.PARAM, type(obj).__name__, *timestamp_and_json]
    raise TypeError(
        f"'{type(obj).__name__}' object {repr(obj)} is not JSON serializable, so the"
        " commit failed"
    )


def _decode_json(json_data: Any) -> Any:
    """Reconstruct an object encoded by ``_json_encode()``."""
    if isinstance(json_data, list):
        key, *data = json_data
        if key == ParamDBKey.DATETIME:
            return datetime.fromtimestamp(data[0], timezone.utc).astimezone()
        if _ASTROPY_INSTALLED and key == ParamDBKey.QUANTITY:
            return Quantity(*data)
        if key == ParamDBKey.LIST:
            return [_decode_json(item) for item in data[0]]
        if key == ParamDBKey.DICT:
            return {key: _decode_json(value) for key, value in data[0].items()}
        if key == ParamDBKey.WRAPPER:
            return _ParamWrapper.from_json(data[0], _decode_json(data[1]))
        if key == ParamDBKey.PARAM:
            class_name = data[0]
            param_class = get_param_class(class_name)
            if param_class is not None:
                return param_class.from_json(data[1], _decode_json(data[2]))
            raise ValueError(
                f"ParamData class '{class_name}' is not known to ParamDB, so the load"
                " failed"
            )
    return json_data


def _encode(obj: Any) -> bytes:
    """Encode the given object into bytes that will be stored in the database."""
    # pylint: disable=no-member
    return _compress(json.dumps(_encode_json(obj)))


def _decode(data: bytes, decode_json: bool) -> Any:
    """
    Decode an object from the given data from the database. Classes will be loaded in
    if ``load_classes`` is True; otherwise, classes will be loaded as dictionaries.
    """
    json_data = json.loads(_decompress(data))
    return _decode_json(json_data) if decode_json else json_data


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

    def commit(
        self, message: str, data: DataT, timestamp: datetime | None = None
    ) -> CommitEntry:
        """
        Commit the given data to the database with the given message and return a commit
        entry for the new commit.

        By default, the timestamp will be set to the current time. If a timestamp is
        given, it is used instead. Naive datetimes will be assumed to be in UTC time.
        """
        with self._Session.begin() as session:
            kwargs: dict[str, Any] = {"message": message, "data": _encode(data)}
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
        self, commit_id: int | None = None, *, decode_json: Literal[True] = True
    ) -> DataT: ...

    @overload
    def load(
        self, commit_id: int | None = None, *, decode_json: Literal[False]
    ) -> Any: ...

    def load(self, commit_id: int | None = None, *, decode_json: bool = True) -> Any:
        """
        Load and return data from the database. If a commit ID is given, load from that
        commit; otherwise, load from the most recent commit. Raise an ``IndexError`` if
        the specified commit does not exist. Note that commit IDs begin at 1.

        By default, objects are reconstructed, which requires the relevant parameter
        data classes to be defined in the current program. However, if ``decode_json``
        is False, the encoded JSON data is loaded directly from the database. The format
        of the encoded data is as follows (see :py:class:`ParamDBKey` for key codes)::

            json_data:
                | int
                | float
                | bool
                | str
                | None
                | [ParamDBKey.DATETIME, float<timestamp>]
                | [ParamDBKey.QUANTITY, float<value>, str<unit>]
                | [ParamDBKey.LIST, [json_data<item>, ...]]
                | [ParamDBKey.DICT, {str<key>: json_data<value>, ...}]
                | [ParamDBKey.WRAPPED, float<timestamp>, json_data<data>]
                | [ParamDBKey.PARAM, str<class_name>, float<timestamp>, json_data<data>]
        """
        select_stmt = self._select_commit(select(_Snapshot.data), commit_id)
        with self._Session() as session:
            data = session.scalar(select_stmt)
        if data is None:
            raise self._index_error(commit_id)
        return _decode(data, decode_json)

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
        decode_json: Literal[True] = True,
    ) -> list[CommitEntryWithData[DataT]]: ...

    @overload
    def commit_history_with_data(
        self,
        start: int | None = None,
        end: int | None = None,
        *,
        decode_json: Literal[False],
    ) -> list[CommitEntryWithData[Any]]: ...

    def commit_history_with_data(
        self,
        start: int | None = None,
        end: int | None = None,
        *,
        decode_json: bool = True,
    ) -> list[CommitEntryWithData[Any]]:
        """
        Retrieve the commit history with data as a list of
        :py:class:`CommitEntryWithData` objects between the provided start and end
        indices, which work like slicing a Python list.

        See :py:meth:`ParamDB.load` for the behavior of ``decode_json``.
        """
        with self._Session() as session:
            select_stmt = self._select_slice(select(_Snapshot), start, end)
            snapshots = session.scalars(select_stmt)
            return [
                CommitEntryWithData(
                    snapshot.id,
                    snapshot.message,
                    snapshot.timestamp,
                    _decode(snapshot.data, decode_json),
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
