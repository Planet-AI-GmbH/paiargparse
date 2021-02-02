from dataclasses import field, dataclass
from enum import IntEnum, Enum

from paiargparse import pai_dataclass, pai_meta


class IntEnumEx(IntEnum):
    A = 0
    B = 1
    C = 2


class StrEnumEx(str, Enum):
    A = 'test1'
    B = 'test2'
    C = 'test3'


@pai_dataclass
@dataclass
class ChildBase:
    shared_arg: float = 0.0


@pai_dataclass
@dataclass
class Child1(ChildBase):
    p1: int = 0


@pai_dataclass
@dataclass
class Child2(ChildBase):
    p2: float = 1


@pai_dataclass
@dataclass
class Parent:
    opt_int: int = -1
    enum: IntEnumEx = IntEnumEx.B
    str_enum: StrEnumEx = StrEnumEx.A

    child: ChildBase = field(default_factory=Child1, metadata=pai_meta(help='Select the child'))
