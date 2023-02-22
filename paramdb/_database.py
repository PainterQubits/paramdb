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
from paramdb._param_data import ParamData, get_param_class
from paramdb._exceptions import CommitNotFoundError


_T = TypeVar("_T", bound=Any)


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
    class_name_dict = {"__class__": obj.__class__.__name__}
    if isinstance(obj, datetime):
        return class_name_dict | {"isoformat": obj.isoformat()}
    if isinstance(obj, ParamData):
        return class_name_dict | obj.to_dict()
    raise TypeError(f"{repr(obj)} is not JSON serializable")


def _from_dict(json_dict: dict[str, Any]) -> dict[str, Any] | datetime | ParamData:
    """
    If the given dictionary created by `json.loads` has the key __class__, attempt to
    construct an object of the named class from it. Otherwise, return the dictionary
    unchanged.
    """
    if "__class__" in json_dict:
        class_name = json_dict.pop("__class__")
        if class_name == datetime.__name__:
            return datetime.fromisoformat(json_dict["isoformat"])
        param_class = get_param_class(class_name)
        if param_class is not None:
            return cast(ParamData, param_class.from_dict(json_dict))
        raise ValueError(f"'{class_name}' is not a known class")
    return json_dict


# pylint: disable-next=too-few-public-methods
class _Base(MappedAsDataclass, DeclarativeBase):
    """Base class for defining SQLAlchemy declarative mapping classes."""


# pylint: disable-next=too-few-public-methods
class _Snapshot(_Base):
    """Snapshot of the database."""

    __tablename__ = "snapshot"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    message: Mapped[str]
    data: Mapped[bytes]
    timestamp: Mapped[datetime] = mapped_column(default_factory=datetime.now)


@dataclass(frozen=True)
class CommitEntry:
    """Entry for a commit."""

    id: int
    message: str
    timestamp: datetime


class ParamDB(Generic[_T]):
    """Parameter database. The database is created in a file at the given path."""

    def __init__(self, path: str):
        self._engine = create_engine(URL.create("sqlite+pysqlite", database=path))
        self._Session = sessionmaker(self._engine)  # pylint: disable=invalid-name
        _Base.metadata.create_all(self._engine)

    def commit(self, message: str, data: _T) -> None:
        """Commit the current data to the database."""
        with self._Session.begin() as session:
            session.add(
                _Snapshot(
                    message=message,
                    data=_compress(json.dumps(data, default=_to_dict)),
                )
            )

    def load(self) -> _T:
        """
        Load and return the current parameters from the database. Raises an
        `EmptyDatabaseError` if there are no commits to load from.
        """
        with self._Session() as session:
            data = session.scalar(
                select(_Snapshot.data).order_by(desc(_Snapshot.id)).limit(1)
            )
        if data is None:
            raise CommitNotFoundError(
                "Cannot load parameter because database"
                f" '{self._engine.url.database}' has no commits."
            )
        return cast(_T, json.loads(_decompress(data), object_hook=_from_dict))

    def commit_history(self) -> list[CommitEntry]:
        """Retrieve the commit history."""
        with self._Session() as session:
            history_entries = session.execute(
                select(_Snapshot.id, _Snapshot.message, _Snapshot.timestamp).order_by(
                    _Snapshot.id
                )
            ).mappings()
        return [CommitEntry(**row_mapping) for row_mapping in history_entries]
