"""Base class for parameter dataclasses."""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, is_dataclass, fields
from typing_extensions import Self, dataclass_transform
from paramdb._param_data._param_data import ParamData

try:
    import pydantic
    import pydantic.dataclasses

    _PYDANTIC_INSTALLED = True
except ImportError:
    _PYDANTIC_INSTALLED = False


@dataclass_transform()
class ParamDataclass(ParamData):
    """
    Subclass of :py:class:`ParamData`.

    Base class for parameter data classes. Subclasses are automatically converted to
    data classes. For example::

        class CustomParam(ParamDataclass):
            value1: float
            value2: int


    Any class keyword arguments (other than those described below) given when creating a
    subclass are passed internally to the ``@dataclass()`` decorator.

    If Pydantic is installed, then subclasses will have Pydantic runtime validation
    enabled by default. This can be disabled using the class keyword argument
    ``type_validation``. The following Pydantic configuration values are set by default:

    - extra: ``'forbid'`` (forbid extra attributes)
    - validate_assignment: ``True`` (validate on assignment as well as initialization)
    - arbitrary_types_allowed: ``True`` (allow arbitrary type hints)
    - strict: ``True`` (disable value coercion, e.g. '2' -> 2)
    - validate_default: ``True`` (validate default values)

    Pydantic configuration options can be updated using the class keyword argument
    ``pydantic_config``, which will merge new options with the existing configuration.
    See https://docs.pydantic.dev/latest/api/config for full configuration options.
    """

    __field_names: set[str]  # Data class field names
    __type_validation: bool = True  # Whether to use Pydantic
    __pydantic_config: pydantic.ConfigDict = {
        "extra": "forbid",
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "strict": True,
        "validate_default": True,
    }

    # Set in __init_subclass__() and used to set attributes within __setattr__()
    # pylint: disable-next=unused-argument
    def __base_setattr(self: Any, name: str, value: Any) -> None: ...

    def __init_subclass__(
        cls,
        /,
        type_validation: bool | None = None,
        pydantic_config: pydantic.ConfigDict | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init_subclass__()  # kwargs are passed to dataclass constructor
        if type_validation is not None:
            cls.__type_validation = type_validation
        if pydantic_config is not None:
            # Merge new Pydantic config with the old one
            cls.__pydantic_config = cls.__pydantic_config | pydantic_config
        cls.__base_setattr = super().__setattr__  # type: ignore
        if _PYDANTIC_INSTALLED and cls.__type_validation:
            # Transform the class into a Pydantic data class, with custom handling for
            # validate_assignment
            pydantic.dataclasses.dataclass(
                config=cls.__pydantic_config | {"validate_assignment": False}, **kwargs
            )(cls)
            if (
                "validate_assignment" in cls.__pydantic_config
                and cls.__pydantic_config["validate_assignment"]
            ):
                pydantic_validator = (
                    pydantic.dataclasses.is_pydantic_dataclass(cls)
                    and cls.__pydantic_validator__  # pylint: disable=no-member
                )
                if pydantic_validator:

                    def __base_setattr(self: Any, name: str, value: Any) -> None:
                        pydantic_validator.validate_assignment(self, name, value)

                    cls.__base_setattr = __base_setattr  # type: ignore
        else:
            # Transform the class into a data class
            dataclass(**kwargs)(cls)
        cls.__field_names = (
            {f.name for f in fields(cls)} if is_dataclass(cls) else set()
        )

    # pylint: disable-next=unused-argument
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        # Prevent instantiating ParamDataclass and call the superclass __init__() here
        # since __init__() will be overwritten by dataclass()
        if cls is ParamDataclass:
            raise TypeError(
                f"only subclasses of {ParamDataclass.__name__} can be instantiated"
            )
        self = super().__new__(cls)
        super().__init__(self)
        return self

    def __post_init__(self) -> None:
        for field_name in self.__field_names:
            self._add_child(getattr(self, field_name))

    def __getitem__(self, name: str) -> Any:
        # Enable getting attributes via square brackets
        return getattr(self, name)

    def __setitem__(self, name: str, value: Any) -> None:
        # Enable setting attributes via square brackets
        setattr(self, name, value)

    def __setattr__(self, name: str, value: Any) -> None:
        # If this attribute is a Data Class field, update last updated and children
        if name in self.__field_names:
            old_value = getattr(self, name) if hasattr(self, name) else None
            self.__base_setattr(name, value)
            self._update_last_updated()
            self._remove_child(old_value)
            self._add_child(value)
            return
        self.__base_setattr(name, value)

    def _to_json(self) -> dict[str, Any]:
        if is_dataclass(self):
            return {f.name: getattr(self, f.name) for f in fields(self) if f.init}
        return {}

    @classmethod
    def _from_json(cls, json_data: dict[str, Any]) -> Self:
        return cls(**json_data)
