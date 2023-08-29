# pylint: skip-file

from __future__ import annotations
from typing import Optional, ClassVar, Any, get_origin
from dataclasses import Field, InitVar, dataclass, MISSING
from typing_extensions import Self, dataclass_transform


@dataclass_transform(kw_only_default=True)
class Base:
    __non_default_kwargs: list[str] | None = None

    def __init_subclass__(cls, /, kw_only: bool = True, **kwargs: Any) -> None:
        super().__init_subclass__()

        if kw_only:
            # Fix for kw_only functionality in Python 3.9
            cls.__non_default_kwargs = []
            type_hints: dict[str, Any] = getattr(cls, "__annotations__", {})

            for name, type_hint in type_hints.items():
                if type_hint is ClassVar or get_origin(type_hint) is ClassVar:
                    continue
                if hasattr(cls, name):
                    f = getattr(cls, name)
                    if isinstance(f, Field):
                        if (
                            f.init
                            and f.default is MISSING
                            and f.default_factory is MISSING
                        ):
                            cls.__non_default_kwargs.append(name)
                            f.default = None
                else:
                    cls.__non_default_kwargs.append(name)
                    setattr(cls, name, None)

            dataclass(**kwargs)(cls)

            original_init = cls.__init__

            def __init__(self: Self, **kwargs: Any) -> None:
                missing_kwargs = [
                    kwarg
                    for c in cls.mro()[::-1]
                    if issubclass(c, Base) and c.__non_default_kwargs is not None
                    for kwarg in c.__non_default_kwargs
                    if kwarg not in kwargs
                ]
                num_missing_kwargs = len(missing_kwargs)
                if num_missing_kwargs > 0:
                    raise TypeError(
                        f"{__init__.__name__}() missing {num_missing_kwargs} required"
                        " keyword-only argument"
                        f"{'s' if num_missing_kwargs > 1 else ''}:"
                        f" {repr(missing_kwargs)[1:-1]}"
                    )
                original_init(self, **kwargs)

            cls.__init__ = __init__  # type: ignore
        else:
            dataclass(**kwargs)(cls)


class Test(Base):
    a: int
    b: int
    c: Optional[int] = None


class Test2(Test, kw_only=False):
    d: ClassVar[int]
    e: InitVar[int]
    f: Optional[int]


Test2(1, 2)
