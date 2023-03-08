"""Parameter database backend using SQLAlchemy and SQLite."""

from typing import TypeVar, Generic, Any, cast
from dataclasses import dataclass
from datetime import datetime
import json
from zstandard import ZstdCompressor, ZstdDecompressor
from sqlalchemy import URL, create_engine, select, desc
from sqlalchemy.orm import (
    sessionmaker,
    MappedAsDataclass,
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from paramdb._param_data._param_data import ParamData, get_param_class

T = TypeVar("T")

# Name of the key storing the class name of a JSON-encoded object
CLASS_NAME_KEY = "__type"


def _compress(text: str) -> bytes:
    """Compress the given text using Zstandard."""
    return ZstdCompressor().compress(text.encode())


def _decompress(compressed_text: bytes) -> str:
    """Decompress the given compressed text using Zstandard."""
    return ZstdDecompressor().decompress(compressed_text).decode()


def _to_dict(obj: Any) -> Any:
    """
    Convert the given object into a dictionary to be passed to `json.dumps`.

    Note that objects within the dictionary do not need to be JSON serializable,
    since they will be recursively processed by `json.dumps`.
    """
    class_name = type(obj).__name__
    class_name_dict = {CLASS_NAME_KEY: class_name}
    if isinstance(obj, datetime):
        return class_name_dict | {"isoformat": obj.isoformat()}
    if isinstance(obj, ParamData):
        return class_name_dict | obj.to_dict()
    raise TypeError(
        f"'{class_name}' object {repr(obj)} is not JSON serializable, so the commit"
        " failed"
    )


def _from_dict(json_dict: dict[str, Any]) -> dict[str, Any] | datetime | ParamData:
    """
    If the given dictionary created by `json.loads` has the key `CLASS_NAME_KEY`,
    attempt to construct an object of the named type from it. Otherwise, return the
    dictionary unchanged.
    """
    if CLASS_NAME_KEY in json_dict:
        class_name = json_dict.pop(CLASS_NAME_KEY)
        if class_name == datetime.__name__:
            return datetime.fromisoformat(json_dict["isoformat"])
        param_class = get_param_class(class_name)
        if param_class is not None:
            return param_class.from_dict(json_dict)
        raise ValueError(
            f"class '{class_name}' is not known to ParamDB, so the load failed"
        )
    return json_dict


class _Base(MappedAsDataclass, DeclarativeBase):
    """Base class for defining SQLAlchemy declarative mapping classes."""


class _Snapshot(_Base):
    """Snapshot of the database."""

    __tablename__ = "snapshot"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    message: Mapped[str]
    data: Mapped[bytes]
    timestamp: Mapped[datetime] = mapped_column(default_factory=datetime.now)


@dataclass(frozen=True)
class CommitEntry:
    """Entry for a commit given commit containing the ID, message, and timestamp."""

    id: int  #: Commit ID
    message: str  #: Message for this commit
    timestamp: datetime  #: When this commit was created


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

    def commit(self, message: str, data: T) -> None:
        """Commit the current data to the database with the given message."""
        with self._Session.begin() as session:
            session.add(
                _Snapshot(
                    message=message,
                    data=_compress(json.dumps(data, default=_to_dict)),
                )
            )

    def load(self, commit_id: int | None = None) -> T:
        """
        Load and return data from the database. If a commit ID is given, load from that
        commit; otherwise, load from the most recent commit. Raise a ``IndexError`` if
        the specified commit does not exist.

        Note that commit IDs begin at 1.
        """
        select_stmt = select(_Snapshot.data)
        select_stmt = (
            select_stmt.order_by(desc(_Snapshot.id)).limit(1)  # Most recent commit
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
        return cast(T, json.loads(_decompress(data), object_hook=_from_dict))

    def commit_history(
        self, number: int | None = None, *, start: int | None = None
    ) -> list[CommitEntry]:
        """Retrieve the commit history as a list of :py:class:`CommitEntry`."""
        with self._Session() as session:
            history_entries = session.execute(
                select(_Snapshot.id, _Snapshot.message, _Snapshot.timestamp)
                .order_by(desc(_Snapshot.id))
                .limit(number)
            ).mappings()
        return [CommitEntry(**row_mapping) for row_mapping in history_entries]
