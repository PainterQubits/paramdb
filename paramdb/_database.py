"""Parameter database backend using SQLAlchemy and SQLite."""

from typing import TypeVar, Generic, Literal, Any, overload
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from zstandard import ZstdCompressor, ZstdDecompressor
from sqlalchemy import URL, create_engine, select, func
from sqlalchemy.orm import (
    sessionmaker,
    MappedAsDataclass,
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from paramdb._keys import CLASS_NAME_KEY
from paramdb._param_data._param_data import ParamData, get_param_class

try:
    from astropy.units import Quantity  # type: ignore

    ASTROPY_INSTALLED = True
except ImportError:
    ASTROPY_INSTALLED = False

T = TypeVar("T")


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


def _to_dict(obj: Any) -> Any:
    """
    Convert the given object into a dictionary to be passed to `json.dumps`.

    Note that objects within the dictionary do not need to be JSON serializable,
    since they will be recursively processed by `json.dumps`.
    """
    class_full_name = _full_class_name(type(obj))
    class_full_name_dict = {CLASS_NAME_KEY: class_full_name}
    if isinstance(obj, datetime):
        return class_full_name_dict | {"isoformat": obj.isoformat()}
    if ASTROPY_INSTALLED and isinstance(obj, Quantity):
        return class_full_name_dict | {"value": obj.value, "unit": str(obj.unit)}
    if isinstance(obj, ParamData):
        return {CLASS_NAME_KEY: type(obj).__name__} | obj.to_dict()
    raise TypeError(
        f"'{class_full_name}' object {repr(obj)} is not JSON serializable, so the"
        " commit failed"
    )


def _from_dict(json_dict: dict[str, Any]) -> Any:
    """
    If the given dictionary created by ``json.loads`` has the key ``CLASS_NAME_KEY``,
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
    if ASTROPY_INSTALLED and class_name == _full_class_name(Quantity):
        return Quantity(**json_dict)
    param_class = get_param_class(class_name)
    if param_class is not None:
        return param_class.from_dict(json_dict)
    raise ValueError(
        f"class '{class_name}' is not known to ParamDB, so the load failed"
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
    # datetime.utcnow is wrapped in a lambda function to allow it to be mocked in tests
    # where we want to control the time.
    timestamp: Mapped[datetime] = mapped_column(
        default_factory=lambda: datetime.utcnow()  # pylint: disable=unnecessary-lambda
    )
    """Naive datetime in UTC time (since this is how SQLite stores datetimes)."""


@dataclass(frozen=True)
class CommitEntry:
    """Entry for a commit given commit containing the ID, message, and timestamp."""

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


class ParamDB(Generic[T]):
    """
    Parameter database. The database is created in a file at the given path if it does
    not exist. To work with type checking, this class can be parameterized with a root
    data type ``T``. For example::

        from paramdb import Struct, ParamDB

        class Root(Struct):
            pass

        param_db = ParamDB[Root]("path/to/param.db")
    """

    def __init__(self, path: str):
        self._engine = create_engine(URL.create("sqlite+pysqlite", database=path))
        self._Session = sessionmaker(self._engine)  # pylint: disable=invalid-name
        _Base.metadata.create_all(self._engine)

    def commit(self, message: str, data: T) -> int:
        """
        Commit the given data to the database with the given message and return the ID
        of the new commit.
        """
        with self._Session.begin() as session:
            snapshot = _Snapshot(
                message=message,
                data=_compress(json.dumps(data, default=_to_dict)),
            )
            session.add(snapshot)
            session.flush()  # Flush so the commit ID is filled in
            return snapshot.id

    @overload
    def load(
        self, commit_id: int | None = None, *, load_classes: Literal[True] = True
    ) -> T:  # pragma: no cover
        ...

    @overload
    def load(
        self, commit_id: int | None = None, *, load_classes: Literal[False]
    ) -> dict[str, Any]:  # pragma: no cover
        ...

    def load(self, commit_id: int | None = None, *, load_classes: bool = True) -> Any:
        """
        Load and return data from the database. If a commit ID is given, load from that
        commit; otherwise, load from the most recent commit. Raise a ``IndexError`` if
        the specified commit does not exist. Note that commit IDs begin at 1.

        By default, parameter data, ``datetime``, and Astropy ``Quantity`` classes are
        reconstructed. The relevant parameter data classes must be defined in the
        current program. However, if ``load_classes`` is False, classes are loaded
        directly from the database as dictionaries with the class name in the key
        :py:const:`~paramdb._keys.CLASS_NAME_KEY` and, if they are parameters, the last
        updated time in the key :py:const:`~paramdb._keys.LAST_UPDATED_KEY`.
        """
        select_stmt = select(_Snapshot.data)
        select_stmt = (
            select_stmt.order_by(_Snapshot.id.desc()).limit(1)  # Most recent commit
            if commit_id is None
            else select_stmt.where(_Snapshot.id == commit_id)  # Specified commit
        )
        with self._Session() as session:
            data = session.scalar(select_stmt)
        if data is None:
            raise IndexError(
                f"cannot load most recent commit because database"
                f" '{self._engine.url.database}' has no commits"
                if commit_id is None
                else f"commit {commit_id} does not exist in database"
                f" '{self._engine.url.database}'"
            )
        return json.loads(
            _decompress(data),
            object_hook=_from_dict if load_classes else None,
        )

    @property
    def num_commits(self) -> int:
        """Number of commits in the database."""
        count_func = func.count()  # pylint: disable=not-callable
        select_stmt = select(count_func).select_from(_Snapshot)
        with self._Session() as session:
            count = session.execute(select_stmt).scalar()
        return count if count is not None else 0

    def commit_history(
        self,
        start: int | None = None,
        end: int | None = None,
    ) -> list[CommitEntry]:
        """
        Retrieve the commit history as a list of :py:class:`CommitEntry` between the
        provided start and end indices, which work like slicing a Python list.
        """
        num_commits = self.num_commits
        start = 0 if start is None else start
        end = num_commits if end is None else end
        start = max(start + num_commits, 0) if start < 0 else start
        end = max(end + num_commits, 0) if end < 0 else end
        with self._Session() as session:
            select_stmt = (
                select(_Snapshot.id, _Snapshot.message, _Snapshot.timestamp)
                .order_by(_Snapshot.id)
                .offset(start)
                .limit(max(end - start, 0))
            )
            history_entries = session.execute(select_stmt).mappings()
        return [CommitEntry(**dict(row_mapping)) for row_mapping in history_entries]

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
