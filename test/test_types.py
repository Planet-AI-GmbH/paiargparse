import unittest
from dataclasses import field
from enum import IntEnum, Enum
from typing import List

from paiargparse import PAIArgumentParser, pai_dataclass


class IntEnumEx(IntEnum):
    A = 0
    B = 1
    C = 2


class StrEnumEx(str, Enum):
    A = 'test1'
    B = 'test2'
    C = 'test3'


@pai_dataclass
class DifferentTypes:
    int_enum: IntEnumEx = IntEnumEx.A
    str_enum: StrEnumEx = StrEnumEx.A

    int_list: List[int] = field(default_factory=list)
    str_list: List[str] = field(default_factory=list)

    int_enum_list: List[IntEnumEx] = field(default_factory=list)


class TestPAIParser(unittest.TestCase):
    def test_enum(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DifferentTypes)
        dt: DifferentTypes = parser.parse_args(
            [
                '--root.int_enum', 'B',
                '--root.str_enum', 'test2',
             ]
        ).root
        self.assertEqual(IntEnumEx.B, dt.int_enum)
        self.assertEqual(StrEnumEx.B, dt.str_enum)

    def test_list(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DifferentTypes)
        dt: DifferentTypes = parser.parse_args(
            [
                '--root.int_list', '1', '2',
                '--root.str_list', 'test1', 'test2',
            ]
        ).root
        self.assertEqual([1, 2], dt.int_list)
        self.assertEqual(['test1', 'test2'], dt.str_list)

    def test_enum_list(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DifferentTypes)
        dt: DifferentTypes = parser.parse_args(
            [
                '--root.int_enum_list', '0', 'B',
            ]
        ).root
        self.assertEqual([IntEnumEx.A, IntEnumEx.B], dt.int_enum_list)