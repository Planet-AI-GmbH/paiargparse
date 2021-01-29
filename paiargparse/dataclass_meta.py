from dataclasses import dataclass

from dataclasses_json import dataclass_json

DEFAULT_SEPARATOR = '.'


def dc_meta(*,
            help=None,
            separator=DEFAULT_SEPARATOR,
            ):
    assert(separator in '/._-+')
    return locals()


def pai_dataclass():
    def wrapper(cls):
        return dataclass_json(dataclass(cls))

    return wrapper
