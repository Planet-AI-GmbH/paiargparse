from dataclasses import field, dataclass

from paiargparse import pai_dataclass, pai_meta


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
    p2: float = field(default=1, metadata=pai_meta(mode='ignore'))


@pai_dataclass
@dataclass
class Parent:
    req_int: int = field(metadata=pai_meta(mode='flat'))

    child: ChildBase = field(default_factory=Child1, metadata=pai_meta(help='Select the child', mode='flat'))
