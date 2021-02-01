from dataclasses import dataclass

from dataclasses_json import dataclass_json

from paiargparse.dataclass_json_overrides import PaiDataClassMixin

DEFAULT_SEPARATOR = '.'


def pai_meta(*,
             help=None,
             separator=DEFAULT_SEPARATOR,
             ):
    assert(separator in '/._-+')
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
    # apply dataclass_json and dataclass
    cls = dataclass_json(dataclass(cls))

    # override to dict and from dict
    cls.to_dict = PaiDataClassMixin.to_dict
    cls.from_dict = classmethod(PaiDataClassMixin.from_dict.__func__)
    PaiDataClassMixin.register(cls)
    return cls


