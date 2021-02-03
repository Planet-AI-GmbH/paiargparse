import unittest
from dataclasses import field, dataclass
from typing import Set

from paiargparse import pai_dataclass, PAIArgumentParser


@pai_dataclass
@dataclass
class DCPrimitive:
    l: Set[int] = field(default_factory=set)
    dl: Set[int] = field(default_factory=lambda: {1, 2})


class TestDataClassList(unittest.TestCase):
    def test_primitive_set(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DCPrimitive)
        dc: DCPrimitive = parser.parse_args(
            [
                '--root.l', '0', '1', '0',
            ]
        ).root

        self.assertSetEqual(dc.l, {0, 1, 0})
        self.assertSetEqual(dc.dl, {1, 2})

    def test_primitive_set_default(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DCPrimitive, DCPrimitive(dl={4, 5}))
        dc: DCPrimitive = parser.parse_args(
            [
            ]
        ).root

        self.assertSetEqual(dc.l, set())
        self.assertSetEqual(dc.dl, {4, 5})
