import copy
import importlib
import warnings
from abc import ABC
from dataclasses import fields, MISSING, is_dataclass, _is_dataclass_instance
from typing import get_type_hints, Dict, Type, Mapping, Collection, TypeVar

from dataclasses_json.core import _user_overrides_or_exts, _decode_letter_case_overrides, _decode_generic, \
    _is_supported_generic, _support_extended_types, _encode_overrides
from dataclasses_json.utils import _handle_undefined_parameters_safe, _is_optional, _is_new_type
from dataclasses_json.api import A
from dataclasses_json.core import Json
import dataclasses_json


def _decode_dataclass(cls, kvs, infer_missing):
    if isinstance(kvs, cls):
        return kvs

    # >>> OVERRIDE TYPE
    if '__cls__' in kvs and kvs['__cls__'] != cls.__module__ + ':' + cls.__name__:
        module, name = kvs['__cls__'].split(":")
        cls = getattr(importlib.import_module(module), name)
    # <<< END

    overrides = _user_overrides_or_exts(cls)
    kvs = {} if kvs is None and infer_missing else kvs
    field_names = [field.name for field in fields(cls)]
    decode_names = _decode_letter_case_overrides(field_names, overrides)
    kvs = {decode_names.get(k, k): v for k, v in kvs.items()}
    missing_fields = {field for field in fields(cls) if field.name not in kvs}

    for field in missing_fields:
        if field.default is not MISSING:
            kvs[field.name] = field.default
        elif field.default_factory is not MISSING:
            kvs[field.name] = field.default_factory()
        elif infer_missing:
            kvs[field.name] = None

    # Perform undefined parameter action
    kvs = _handle_undefined_parameters_safe(cls, kvs, usage="from")

    init_kwargs = {}
    types = get_type_hints(cls)
    for field in fields(cls):
        # The field should be skipped from being added
        # to init_kwargs as it's not intended as a constructor argument.
        if not field.init:
            continue

        field_value = kvs[field.name]
        field_type = types[field.name]
        # >>> Support for Generic Types
        if isinstance(field_type, TypeVar):
            if not hasattr(field_type, '__bound__'):
                warnings.warn(
                    f"If using TypeVars, set the bound field for obtaining the default type. "
                )
            else:
                field_type = field_type.__bound__
        # <<< Support for Generic Types
        if field_value is None and not _is_optional(field_type):
            warning = (f"value of non-optional type {field.name} detected "
                       f"when decoding {cls.__name__}")
            if infer_missing:
                warnings.warn(
                    f"Missing {warning} and was defaulted to None by "
                    f"infer_missing=True. "
                    f"Set infer_missing=False (the default) to prevent this "
                    f"behavior.", RuntimeWarning)
            else:
                warnings.warn(f"`NoneType` object {warning}.", RuntimeWarning)
            init_kwargs[field.name] = field_value
            continue

        while True:
            if not _is_new_type(field_type):
                break

            field_type = field_type.__supertype__

        if (field.name in overrides
                and overrides[field.name].decoder is not None):
            # FIXME hack
            if field_type is type(field_value):
                init_kwargs[field.name] = field_value
            else:
                init_kwargs[field.name] = overrides[field.name].decoder(
                    field_value)
        elif is_dataclass(field_type):
            # FIXME this is a band-aid to deal with the value already being
            # serialized when handling nested marshmallow schema
            # proper fix is to investigate the marshmallow schema generation
            # code
            if is_dataclass(field_value):
                value = field_value
            else:
                value = _decode_dataclass(field_type, field_value,
                                          infer_missing)
            init_kwargs[field.name] = value
        elif _is_supported_generic(field_type) and field_type != str:
            init_kwargs[field.name] = _decode_generic(field_type,
                                                      field_value,
                                                      infer_missing)
        else:
            init_kwargs[field.name] = _support_extended_types(field_type,
                                                              field_value)

    return cls(**init_kwargs)


def _asdict(obj, encode_json=False):
    """
    A re-implementation of `asdict` (based on the original in the `dataclasses`
    source) to support arbitrary Collection and Mapping types.
    """
    if _is_dataclass_instance(obj):
        result = []
        for field in fields(obj):
            value = _asdict(getattr(obj, field.name), encode_json=encode_json)
            result.append((field.name, value))

        result = _handle_undefined_parameters_safe(cls=obj, kvs=dict(result),
                                                   usage="to")

        # >>> INSERTED HERE
        if hasattr(obj.__class__, '__pai_dataclass__'):
            result = dict(result)
            result['__cls__'] = obj.__class__.__module__ + ':' + obj.__class__.__name__
        # <<< END
        return _encode_overrides(dict(result), _user_overrides_or_exts(obj),
                                 encode_json=encode_json)
    elif isinstance(obj, Mapping):
        return dict((_asdict(k, encode_json=encode_json),
                     _asdict(v, encode_json=encode_json)) for k, v in
                    obj.items())
    elif isinstance(obj, Collection) and not isinstance(obj, str) \
            and not isinstance(obj, bytes):
        return list(_asdict(v, encode_json=encode_json) for v in obj)
    else:
        return copy.deepcopy(obj)


class PaiDataClassMixin(ABC):
    @classmethod
    def from_dict(cls: Type[A],
                  kvs: Json,
                  *,
                  infer_missing=False) -> A:
        # Use custom _decode_dataclass with fixed types
        return _decode_dataclass(cls, kvs, infer_missing)

    def to_dict(self, encode_json=False) -> Dict[str, Json]:
        d = _asdict(self, encode_json=encode_json)
        return d


# Override dataclass_json functions to include custom adaptions
dataclasses_json.core._decode_dataclass = _decode_dataclass
dataclasses_json.core._asdict = _asdict
