"""Base class for parameter dataclasses."""

from __future__ import annotations
from typing import Any, cast
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
class ParamDataclass(ParamData[str]):
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

    _field_names: set[str]  # Data class field names
    __type_validation: bool = True  # Whether to use Pydantic
    __pydantic_config: pydantic.ConfigDict = {
        "extra": "forbid",
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "strict": True,
        "validate_default": True,
    }
    _wrapped_children: dict[str, Any] | None = None  # Used when initializing from json

    # pylint: disable-next=unused-argument
    def __base_setattr(self: Any, name: str, value: Any) -> None:
        """
        If Pydantic is enabled and ``validate_assignment`` is True, this function will
        both set and validate the attribute; otherwise, it will be an ordinary setattr
        function.

        Set in ``__init_subclass__()`` and used to set attributes within
        ``__setattr__()``.
        """

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
        cls.__base_setattr = super().__setattr__  # type: ignore[assignment]
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

                    cls.__base_setattr = __base_setattr  # type: ignore[method-assign]
        else:
            # Transform the class into a data class
            dataclass(**kwargs)(cls)
        cls._field_names = {f.name for f in fields(cls)} if is_dataclass(cls) else set()

    # pylint: disable-next=unused-argument
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        # Prevent instantiating ParamDataclass and call the superclass __init__() here
        # since __init__() will be overwritten by dataclass()
        if cls is ParamDataclass:
            raise TypeError(
                f"only subclasses of {ParamDataclass.__name__} can be instantiated"
            )
        self = super().__new__(cls)
        super().__init__(self)  # type: ignore[arg-type]
        return self

    def __post_init__(self) -> None:
        # Wrap fields as children and process them
        for field in fields(self):  # type: ignore[arg-type]
            if self._wrapped_children is not None and field.init:
                wrapped_child = self._wrapped_children[field.name]
            else:
                wrapped_child = self._wrap_child(super().__getattribute__(field.name))
            super().__setattr__(field.name, wrapped_child)
            self._add_child(wrapped_child)

    def __getitem__(self, name: str) -> Any:
        # Enable getting attributes via square brackets
        return getattr(self, name)

    def __setitem__(self, name: str, value: Any) -> None:
        # Enable setting attributes via square brackets
        setattr(self, name, value)

    def __delitem__(self, name: str) -> None:
        # Enable deleting attributes via square brackets
        delattr(self, name)

    def __getattribute__(self, name: str) -> Any:
        # Unwrap child if the attribute is a field
        value = super().__getattribute__(name)
        if name in super().__getattribute__("_field_names"):
            return self._unwrap_child(value)
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        # If this attribute is a field, process the old and new child
        if name in self._field_names:
            try:
                old_wrapped_value = super().__getattribute__(name)
            except AttributeError:
                old_wrapped_value = None
            self.__base_setattr(name, value)  # May perform type validation
            wrapped_value = self._wrap_child(value)
            super().__setattr__(name, wrapped_value)
            self._remove_child(old_wrapped_value)
            self._add_child(wrapped_value)
        else:
            self.__base_setattr(name, value)

    def __delattr__(self, name: str) -> None:
        old_wrapped_value = super().__getattribute__(name)
        super().__delattr__(name)
        if name in self._field_names:
            self._remove_child(old_wrapped_value)

    def _get_wrapped_child(self, child_name: str) -> ParamData[Any]:
        if child_name in self._field_names:
            return cast(ParamData[Any], super().__getattribute__(child_name))
        return super()._get_wrapped_child(child_name)

    def to_json(self) -> dict[str, Any]:
        return {
            field.name: super(ParamData, self).__getattribute__(field.name)
            for field in fields(self)  # type: ignore[arg-type]
            if field.init
        }

    def _init_from_json(self, json_data: dict[str, Any]) -> None:
        unwrapped_children = {
            name: self._unwrap_child(wrapped_child)
            for name, wrapped_child in json_data.items()
        }
        super().__setattr__("_wrapped_children", json_data)
        # pylint: disable-next=unnecessary-dunder-call
        self.__init__(**unwrapped_children)  # type: ignore[misc]
        super().__delattr__("_wrapped_children")
