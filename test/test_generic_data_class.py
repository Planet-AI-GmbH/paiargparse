import unittest
from dataclasses import dataclass, field
from typing import TypeVar, Generic

from paiargparse import pai_dataclass, PAIArgumentParser


@pai_dataclass
@dataclass
class SubBase:
    p: int = 1

@pai_dataclass
@dataclass
class Sub1(SubBase):
    x: int = 1

T = TypeVar('T', bound=SubBase)

@pai_dataclass
@dataclass
class Base(Generic[T]):
    f1: T = field(default_factory=Sub1)

class TestGenericDataClass(unittest.TestCase):
    def test_genertic(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base)
        root: Base = parser.parse_args(['--root.f1.p', '2']).root

        self.assertEqual(2, root.f1.p)

    def test_generic_parse_dict(self):
        x = Base()
        self.assertEqual(x, Base.from_dict(x.to_dict()))
