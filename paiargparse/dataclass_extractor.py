"""Utility functions to translate dataclass fields into valid command line arguments.

Use extract_args_from_dataclass(MyDataclass) to return a List[ArgumentField].
"""

from dataclasses import dataclass, MISSING
from enum import Enum
from typing import Any, List, Type, Optional, Tuple, Union, TypeVar

SUPPORTED_ENUM_TYPES = {int, str, float}


@dataclass
class ArgumentField:
    """Class that represents the parsed type of an argument of a pai_dataclass.

    see parsing in arg_from_field.

    E.g.:

    ```
    @pai_dataclass
    @dataclass
    class Foo:
       list_int: Optional[List[int]] = field(default_factory=list)
    ```

    will result in an `ArgumentField`:

    ```
    parsed_field = ArgumentField(
        name="list_int",
        type=int,
        meta={},  # since metadata is not specified in field
        optional=True,
        list=list,
        dataclass=False,
        default=list(),  # the called factory or the default value
        required=False,
        enum=None,
        dict_type=None,
    )
    ```

    """

    name: str
    type: Any
    meta: dict
    optional: bool
    list: Optional[Union[Type[list], Type[set]]]  # type `list` or `set`, since the other logic is identical, or None
    dataclass: bool  # is the type again a pai_dataclass
    default: Any
    required: bool
    enum: Optional[Type[Enum]]  # If set its an enum, this is the type
    dict_type: Any  # If set its a dict, this is the VALUE type, type is the key type

    def __post_init__(self):
        # check if it is a supported type
        if self.list and self.dict_type:
            raise ValueError(f"Only list or dict types are supported. See field {self.name}")

        if self.dict_type and self.dataclass:
            supported_types = {str}
            if self.type not in supported_types:
                raise TypeError(
                    f"If using a Dict[type, DataClass], type must be in {supported_types}, but got {self.type}. "
                    f"See field {self.name}."
                )

        if self.enum and self.meta.get("choices", None) is not None:
            raise ValueError(
                f"Choices are not supported on enum fields since they are automatically parsed by the "
                f"enum. (Caused by {self.name} with choices {self.meta['choices']}"
            )

    @staticmethod
    def from_field(name: str, meta: dict, field) -> "ArgumentField":
        """Parse the given Dataclass Field `field` with given `name` and `meta`."""
        is_optional, t = split_optional_type(field.type)
        is_list, t = split_list_type(t)
        t, dict_type = split_dict_type(t)
        enum_class, t = split_enum_type(t)
        if isinstance(t, TypeVar):
            if not hasattr(t, "__bound__"):
                raise ValueError(f"A TypeVar must have field 'bound' set.")
            else:
                t = t.__bound__

        if dict_type:
            is_dataclass = hasattr(dict_type, "__dataclass_fields__")
        else:
            is_dataclass = hasattr(t, "__dataclass_fields__")

        default = field.default
        if default == MISSING and field.default_factory != MISSING:
            default = field.default_factory()

        required = is_field_required(field)

        return ArgumentField(
            name=name,
            type=t,
            meta=meta,
            optional=is_optional,
            list=is_list,
            dataclass=is_dataclass,
            enum=enum_class,
            default=default,
            required=required,
            dict_type=dict_type,
        )


def split_optional_type(t):
    """Split optional from a type.

    E.g.:
        split_optional_type(Optional[int]) => True, int
        split_optional_type(int) => False, int
    """
    if isinstance(t, type):
        return False, t

    is_optional = hasattr(t, "__args__") and len(t.__args__) == 2 and t.__args__[-1] is type(None)
    if is_optional:
        return True, t.__args__[0]
    else:
        return False, t


def split_list_type(ftype) -> Tuple[Optional[Union[Type[list], Type[set]]], Any]:
    """Checks if the ftype is a List (or Set) type and return the list type and the inner type.

    Returns:
        `(None, ftype)` if not a list type,
        `(List, TYPE)` if `ftype = List[TYPE]` (analog for `Set`)

    E.g.:
        split_list_type(List[int]) => (List, int)
        split_list_type(int) => (None, int)
    """
    if isinstance(ftype, type):
        return None, ftype
    is_list = hasattr(ftype, "__args__") and len(ftype.__args__) == 1 and ftype._name == "List"

    if is_list:
        return list, ftype.__args__[0]

    is_set = hasattr(ftype, "__args__") and len(ftype.__args__) == 1 and ftype._name == "Set"
    if is_set:
        return set, ftype.__args__[0]
    else:
        return None, ftype


def split_dict_type(dtype):
    """Checks if dtype is a dictionary type, then return the types

    E.g.:
        split_dict_type(Dict[str, int]) -> str, int
        split_dict_type(str) -> str, None
    """
    if isinstance(dtype, type):
        return dtype, None
    is_dict = hasattr(dtype, "__args__") and len(dtype.__args__) == 2 and dtype._name == "Dict"
    if is_dict:
        return dtype.__args__
    else:
        return dtype, None


def split_enum_type(etype):
    """Checks if etype is an enum, then returns the enum type

    E.g.:
        class MyEnum(IntEnum):
            A = 1

        split_enum_type(MyEnum) -> MyEnum, int
        split_enum_type(str) -> None, str
    """
    try:
        is_enum = issubclass(etype, Enum)
    except TypeError:
        # etype is not a type, cant be enum
        return None, etype

    if not is_enum:
        return None, etype

    enum_type = None
    for t in SUPPORTED_ENUM_TYPES:
        if issubclass(etype, t):
            enum_type = t
            break
    if enum_type is None:
        raise ValueError(f"Unknown enum type of {enum_type}. Supported types are {SUPPORTED_ENUM_TYPES}")
    return etype, enum_type


def is_field_required(field):
    """Check if a field is required by checking if both the default value or the default_factory of a field are MISSING"""
    return field.default == MISSING and field.default_factory == MISSING


def extract_args_of_dataclass(dc, exclude_ignored=True) -> List[ArgumentField]:
    """Return all Arguments of a dataclass as List[ArgumentField]"""
    args = []
    for name, field in dc.__dataclass_fields__.items():
        meta: dict = field.metadata
        if exclude_ignored and meta.get("mode", "snake") == "ignore":
            continue

        arg = ArgumentField.from_field(name, meta, field)
        args.append(arg)

    return args


def enum_choices(enum_cls: Type[Enum]):
    return list(enum_cls.__members__.keys()) + list(str(v.value) for v in enum_cls.__members__.values())


def str_to_enum(v: str, enum_cls: Type[Enum], enum_type):
    try:
        return enum_cls(enum_type(v))
    except ValueError:
        pass

    for k, e in enum_cls.__members__.items():
        if k == v:
            return e

    raise ValueError(f"Could not match {v} to any valid key in {enum_cls.__members__.keys()}.")


def str_to_bool(v: str) -> bool:
    return (v.lower() in {"true", "y", "yes"}) or (v.isdigit() and int(v) > 0)
