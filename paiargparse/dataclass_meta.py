from dataclasses import dataclass, is_dataclass
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
             ):
    # TODO: handle required!
    assert(separator in '/._-+')
    assert(mode in {'snake', 'ignore', 'flat'})
    assert(nargs in {'*', '+'})
    if choices is not None:
        data_class_choices = [cls.__name__ for cls in choices]
        if len(set(data_class_choices)) != len(data_class_choices):
            raise ValueError(f"Class names must be unique in pai_meta(choices): {data_class_choices}")
    return locals()


def pai_dataclass(_cls=None):
    """
    Based on the code in the `dataclasses` module to handle optional-parens
    decorators. See example below:

    @pai_dataclass
    class Example:
        ...
    """

    def wrap(cls):
        return _process_class(cls)

    if _cls is None:
        return wrap
    return wrap(_cls)


def _process_class(cls):
    # apply dataclass_json, dataclass must be assigned manually for intellisense
    assert(is_dataclass(cls))
    cls = dataclass_json(cls)

    # override to dict and from dict
    cls.to_dict = PaiDataClassMixin.to_dict
    cls.from_dict = classmethod(PaiDataClassMixin.from_dict.__func__)
    PaiDataClassMixin.register(cls)
    return cls


