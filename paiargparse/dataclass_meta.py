from dataclasses import is_dataclass
from typing import List, Any

from dataclasses_json import dataclass_json

from paiargparse.dataclass_json_overrides import PaiDataClassMixin

DEFAULT_SEPARATOR = "."


def pai_meta(
    *,
    help=None,
    separator=DEFAULT_SEPARATOR,
    mode="snake",
    required=None,
    nargs="*",
    choices: List[Any] = None,
    disable_subclass_check=False,
    enforce_choices=None,  # if choices are dataclass, defaults to False, else True
    fix_dc=False,  # if True, the dataclass can not be overwritten
    tuple_like=False,  # if True, enable fix dc and enable to set values similar to tuples
):
    """Meta information for a dataclass field.

    Arguments:
        help: string to show in the help of the command line
        separator: separator for this argument, by default a dot
        mode: how to concatenate this argument with its parent.
            snake (default): concatenate all parents with the separator
            ingnore: Do not show this argument in the command line at all
            flat: Add this argument as a root argument (no parents)
            ssnake: (short snake), only concatenate the name with the direct parent.
            required: (default None), override if this argument is required to specify from the command line, even if a default value is set.
            nargs: (default '*'), if '*', 0 arguments are legit, if '+', at least one argument must be passed to a List/Set
            choices: only allow the given values (consider using an enumeration instead of choices!)
            disable_subclass_check: (default false) Disable the check for a dataclass argument if the provided class is a subclass of the type.
            enforce_choices: Force that the choices must be matched. For dataclasses this is False by default, since the sub class might be derived. See also disable_subclass_check
            fix_dc: (applies only to dataclass fields) force that the type of the dataclass field must not be changed.
            typle_like: allow to set the fields of a dataclass as tuples (see README.md for usage)

    see also dataclass_json metadata for addtional options, e.g. for encoding and decoding to a dict/json
    """
    assert separator in "/._-+"
    assert mode in {"snake", "ignore", "flat", "ssnake"}
    assert nargs in {"*", "+"}
    if choices is not None:
        data_class_choices = [cls.__name__ for cls in choices if is_dataclass(cls)]
        if len(set(data_class_choices)) != len(data_class_choices):
            raise ValueError(f"Class names must be unique in pai_meta(choices): {data_class_choices}")
        primitive_choices = [cls for cls in choices if not is_dataclass(cls)]
        if len(set(primitive_choices)) != len(primitive_choices):
            raise ValueError(f"Choices must be unique in pai_meta(choices): {primitive_choices}")
        if len(data_class_choices) > 0 and len(primitive_choices):
            raise ValueError(f"Mixing of dataclasses and primitive types is not supported.")
        if enforce_choices is None:
            if data_class_choices:
                enforce_choices = False
            elif primitive_choices:
                enforce_choices = True

    if enforce_choices and choices is None:
        raise ValueError("If enforcing choices, choices are required.")
    if tuple_like:
        fix_dc = True
    return locals()


def set_attr_forbid_unknown(cls):
    """Override the __setattr__ method of a dataclass `cls` to forbid setting fields that do not exist in `cls`"""

    def __setattr__(self, key, value):
        if key not in self.__class__.__dataclass_fields__:
            raise AttributeError(
                f"Class {self.__class__} has no attribute {key}. "
                f"Available fields: {', '.join(self.__class__.__dataclass_fields__.keys())}"
            )
        else:
            return super(cls, self).__setattr__(key, value)

    return __setattr__


def pai_dataclass(_cls=None, alt=None, no_assign_to_unknown=True):
    """
    Based on the code in the `dataclasses` module to handle optional-parens
    decorators. See example below:

    @pai_dataclass
    class Example:
        ...

    alt allows you to specify an alternative name for this class that can be used if listed in pai_meta choices.
    """

    def wrap(cls):
        setattr(cls, "__pai_dataclass__", None)  # Mark this class as a pai dataclass
        setattr(cls, "__alt_name__", alt)
        cls = _process_class(cls)
        if no_assign_to_unknown:
            setattr(cls, "__setattr__", set_attr_forbid_unknown(cls))
        return cls

    if _cls is None:
        return wrap
    return wrap(_cls)


def _process_class(cls):
    # apply dataclass_json, dataclass must be assigned manually for intellisense
    assert is_dataclass(cls)
    cls = dataclass_json(cls)

    # override to dict and from dict
    cls.to_dict = PaiDataClassMixin.to_dict
    cls.from_dict = classmethod(PaiDataClassMixin.from_dict.__func__)
    PaiDataClassMixin.register(cls)
    return cls
