import unittest
from dataclasses import dataclass, field
from typing import Optional

from paiargparse import pai_dataclass, PAIArgumentParser, pai_meta


@pai_dataclass
@dataclass
class Sub:
    f1: Optional[float] = None


@pai_dataclass
@dataclass
class Base:
    i1: Optional[int] = None
    i2: Optional[int] = -1
    i3: int = 3

    sub1: Optional[Sub] = field(default_factory=Sub, metadata=pai_meta(choices=[Sub]))
    sub2: Optional[Sub] = field(default=None, metadata=pai_meta(choices=[Sub]))


class TestOptional(unittest.TestCase):
    def test_optionals(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base)
        base: Base = parser.parse_args([]).root

        self.assertIsNone(base.i1)
        self.assertEqual(base.i2, -1)
        self.assertIsInstance(base.sub1, Sub)
        self.assertIsNone(base.sub1.f1)
        self.assertIsNone(base.sub2)

    def test_optionals_args(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base)
        base: Base = parser.parse_args(['--root.i1', '2', '--root.i2', 'None', '--root.sub2', 'Sub', '--root.sub1', 'None']).root

        self.assertEqual(base.i1, 2)
        self.assertIsNone(base.i2)
        self.assertIsInstance(base.sub2, Sub)
        self.assertIsNone(base.sub2.f1)
        self.assertIsNone(base.sub1)
