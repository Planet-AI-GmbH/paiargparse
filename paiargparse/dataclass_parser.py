from dataclasses import dataclass, _MISSING_TYPE
from enum import Enum
from typing import Any, List, Type

SUPPORTED_ENUM_TYPES = {int, str, float}


@dataclass
class ArgumentField:
    name: str
    type: Any
    meta: dict
    optional: bool
    list: bool
    dataclass: bool
    default: Any
    required: bool
    enum: Type[Enum]


def split_optional_type(t):
    if isinstance(t, type):
        return False, t

    is_optional = (hasattr(t, "__args__")
                   and len(t.__args__) == 2
                   and t.__args__[-1] is type(None)
                   )
    if is_optional:
        return True, t.__args__[0]
    else:
        return False, t


def split_list_type(ftype):
    if isinstance(ftype, type):
        return False, ftype
    is_list = (hasattr(ftype, "__args__")
               and len(ftype.__args__) == 1
               and ftype._name == 'List'
               )

    if is_list:
        return True, ftype.__args__[0]
    else:
        return False, ftype


def split_enum_type(etype):
    is_enum = issubclass(etype, Enum)
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


def arg_from_field(name, meta, field) -> ArgumentField:
    is_optional, t = split_optional_type(field.type)
    is_list, t = split_list_type(t)
    enum_class, t = split_enum_type(t)
    is_dataclass = hasattr(t, '__dataclass_fields__')

    default = field.default
    if isinstance(default, _MISSING_TYPE) and not isinstance(field.default_factory, _MISSING_TYPE):
        default = field.default_factory()

    required = is_field_required(field)

    return ArgumentField(name=name, type=t, meta=meta, optional=is_optional, list=is_list,
                         dataclass=is_dataclass, enum=enum_class,
                         default=default, required=required)


def is_field_required(field):
    return isinstance(field.default, _MISSING_TYPE) and isinstance(field.default_factory, _MISSING_TYPE)


def extract_args_of_dataclass(dc) -> List[ArgumentField]:
    args = []
    for name, field in dc.__dataclass_fields__.items():
        meta = field.metadata
        arg = arg_from_field(name, meta, field)
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
