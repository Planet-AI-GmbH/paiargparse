from dataclasses import field

from paiargparse import pai_dataclass, pai_meta


@pai_dataclass
class ChildBase:
    shared_arg: float = 0.0


@pai_dataclass
class Child1(ChildBase):
    p1: int = 0


@pai_dataclass
class Child2(ChildBase):
    p2: float = 1


@pai_dataclass
class Parent:
    opt_int: int = -1

    child: ChildBase = field(default_factory=Child1, metadata=pai_meta(help='Select the child'))
