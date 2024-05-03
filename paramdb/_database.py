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
from paramdb._param_data._param_data import ParamData, get_param_class

try:
    from astropy.units import Quantity  # type: ignore

    _ASTROPY_INSTALLED = True
except ImportError:
    _ASTROPY_INSTALLED = False

T = TypeVar("T")
_SelectT = TypeVar("_SelectT", bound=Select[Any])

CLASS_NAME_KEY = "__type"
"""
Dictionary key corresponding to an object's class name in the JSON representation of a
ParamDB commit.
"""


def _compress(text: str) -> bytes:
    """Compress the given text using Zstandard."""
    return ZstdCompressor().compress(text.encode())


def _decompress(compressed_text: bytes) -> str:
    """Decompress the given compressed text using Zstandard."""
    return ZstdDecompressor().decompress(compressed_text).decode()


def _full_class_name(cls: type) -> str:
    """
    Return the full name of the given class, including the module. Used to convert
    non-parameter-data objects to and from JSON.
    """
    return f"{cls.__module__}.{cls.__name__}"


def _from_dict(json_dict: dict[str, Any]) -> Any:
    """
    If the given dictionary created by ``json.loads()`` has the key ``CLASS_NAME_KEY``,
    attempt to construct an object of the named type from it. Otherwise, return the
    dictionary unchanged.

    If load_classes is False, then parameter data objects will be loaded as
    dictionaries.
    """
    if CLASS_NAME_KEY not in json_dict:
        return json_dict
    class_name = json_dict.pop(CLASS_NAME_KEY)
    if class_name == _full_class_name(datetime):
        return datetime.fromisoformat(json_dict["isoformat"]).astimezone()
    if _ASTROPY_INSTALLED and class_name == _full_class_name(Quantity):
        return Quantity(**json_dict)
    param_class = get_param_class(class_name)
    if param_class is not None:
        return param_class.from_dict(json_dict)
    raise ValueError(
        f"class '{class_name}' is not known to ParamDB, so the load failed"
    )


def _preprocess_json(obj: Any) -> Any:
    """
    Preprocess the given object and its children into a JSON-serializable format.
    Compared with ``json.dumps()``, this function can define custom logic for dealing
    with subclasses of ``int``, ``float``, and ``str``.
    """
    if isinstance(obj, ParamData):
        return {CLASS_NAME_KEY: type(obj).__name__} | _preprocess_json(obj.to_dict())
    if isinstance(obj, (int, float, bool, str)) or obj is None:
        return obj
    if isinstance(obj, (list, tuple)):
        return [_preprocess_json(value) for value in obj]
    if isinstance(obj, dict):
        return {key: _preprocess_json(value) for key, value in obj.items()}
    class_full_name = _full_class_name(type(obj))
    class_full_name_dict = {CLASS_NAME_KEY: class_full_name}
    if isinstance(obj, datetime):
        return class_full_name_dict | {"isoformat": obj.isoformat()}
    if _ASTROPY_INSTALLED and isinstance(obj, Quantity):
        return class_full_name_dict | {"value": obj.value, "unit": str(obj.unit)}
    raise TypeError(
        f"'{class_full_name}' object {repr(obj)} is not JSON serializable, so the"
        " commit failed"
    )


def _encode(obj: Any) -> bytes:
    """Encode the given object into bytes that will be stored in the database."""
    # pylint: disable=no-member
    return _compress(json.dumps(_preprocess_json(obj)))


def _decode(data: bytes, load_classes: bool) -> Any:
    """
    Decode an object from the given data from the database. Classes will be loaded in
    if ``load_classes`` is True; otherwise, classes will be loaded as dictionaries.
    """
    return json.loads(
        _decompress(data),
        object_hook=_from_dict if load_classes else None,
    )


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
class CommitEntryWithData(CommitEntry, Generic[T]):
    """
    Subclass of :py:class:`CommitEntry`.

    Entry for a commit containing the ID, message, and timestamp, as well as the data.
    """

    data: T
    """Data contained in this commit."""


class ParamDB(Generic[T]):
    """
    Parameter database. The database is created in a file at the given path if it does
    not exist. To work with type checking, this class can be parameterized with a root
    data type ``T``. For example::

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
        self, message: str, data: T, timestamp: datetime | None = None
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
        self, commit_id: int | None = None, *, load_classes: Literal[True] = True
    ) -> T: ...

    @overload
    def load(
        self, commit_id: int | None = None, *, load_classes: Literal[False]
    ) -> Any: ...

    def load(self, commit_id: int | None = None, *, load_classes: bool = True) -> Any:
        """
        Load and return data from the database. If a commit ID is given, load from that
        commit; otherwise, load from the most recent commit. Raise an ``IndexError`` if
        the specified commit does not exist. Note that commit IDs begin at 1.

        By default, parameter data, ``datetime``, and Astropy ``Quantity`` classes are
        reconstructed. The relevant parameter data classes must be defined in the
        current program. However, if ``load_classes`` is False, classes are loaded
        directly from the database as dictionaries with the class name in the key
        :py:const:`~paramdb._database.CLASS_NAME_KEY`.
        """
        select_stmt = self._select_commit(select(_Snapshot.data), commit_id)
        with self._Session() as session:
            data = session.scalar(select_stmt)
        if data is None:
            raise self._index_error(commit_id)
        return _decode(data, load_classes)

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
        load_classes: Literal[True] = True,
    ) -> list[CommitEntryWithData[T]]: ...

    @overload
    def commit_history_with_data(
        self,
        start: int | None = None,
        end: int | None = None,
        *,
        load_classes: Literal[False],
    ) -> list[CommitEntryWithData[Any]]: ...

    def commit_history_with_data(
        self,
        start: int | None = None,
        end: int | None = None,
        *,
        load_classes: bool = True,
    ) -> list[CommitEntryWithData[Any]]:
        """
        Retrieve the commit history with data as a list of
        :py:class:`CommitEntryWithData` objects between the provided start and end
        indices, which work like slicing a Python list.

        See :py:meth:`ParamDB.load` for the behavior of ``load_classes``.
        """
        with self._Session() as session:
            select_stmt = self._select_slice(select(_Snapshot), start, end)
            snapshots = session.scalars(select_stmt)
            return [
                CommitEntryWithData(
                    snapshot.id,
                    snapshot.message,
                    snapshot.timestamp,
                    _decode(snapshot.data, load_classes),
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
