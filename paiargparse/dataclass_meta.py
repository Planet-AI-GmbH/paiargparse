from dataclasses import is_dataclass
from typing import List, Any

from dataclasses_json import dataclass_json

from paiargparse.dataclass_json_overrides import PaiDataClassMixin

DEFAULT_SEPARATOR = '.'


def pai_meta(*,
             help=None,
             separator=DEFAULT_SEPARATOR,
             mode='snake',
             required=None,
             nargs='*',
             choices: List[Any] = None,
             disable_subclass_check=False,
             enforce_choices=None,  # if choices are dataclass, defaults to False, else True
             fix_dc=False,  # if True, the dataclass can not be overwritten
             ):
    assert (separator in '/._-+')
    assert (mode in {'snake', 'ignore', 'flat', 'ssnake'})
    assert (nargs in {'*', '+'})
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
    return locals()


def set_attr_forbid_unknown(cls):
    def __setattr__(self, key, value):
        if key not in self.__class__.__dataclass_fields__:
            raise AttributeError(
                f"Class {self.__class__} has no attribute {key}. "
                f"Available fields: {', '.join(self.__class__.__dataclass_fields__.keys())}")
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
        setattr(cls, '__pai_dataclass__', None)  # Mark this class as a pai dataclass
        setattr(cls, '__alt_name__', alt)
        cls = _process_class(cls)
        if no_assign_to_unknown:
            setattr(cls, '__setattr__', set_attr_forbid_unknown(cls))
        return cls

    if _cls is None:
        return wrap
    return wrap(_cls)


def _process_class(cls):
    # apply dataclass_json, dataclass must be assigned manually for intellisense
    assert (is_dataclass(cls))
    cls = dataclass_json(cls)

    # override to dict and from dict
    cls.to_dict = PaiDataClassMixin.to_dict
    cls.from_dict = classmethod(PaiDataClassMixin.from_dict.__func__)
    PaiDataClassMixin.register(cls)
    return cls
