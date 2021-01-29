from dataclasses import dataclass, _MISSING_TYPE
from typing import Any, List


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


def arg_from_field(name, meta, field) -> ArgumentField:
    is_optional, t = split_optional_type(field.type)
    is_list, t = split_list_type(t)
    is_dataclass = hasattr(t, '__dataclass_fields__')

    default = field.default
    if isinstance(default, _MISSING_TYPE) and not isinstance(field.default_factory, _MISSING_TYPE):
        default = field.default_factory()

    required = is_field_required(field)

    return ArgumentField(name=name, type=t, meta=meta, optional=is_optional, list=is_list, dataclass=is_dataclass,
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

