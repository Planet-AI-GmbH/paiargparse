import unittest
from dataclasses import field, dataclass
from typing import List

from paiargparse import pai_dataclass, PAIArgumentParser


@pai_dataclass
@dataclass
class Sub:
    int_arg: int = -1


@pai_dataclass
@dataclass
class DC:
    l: List[Sub] = field(default_factory=list)


@pai_dataclass
@dataclass
class DCWithDefault:
    l: List[Sub] = field(default_factory=lambda: [Sub(-2), Sub(2)])


@pai_dataclass
@dataclass
class DCPrimitve:
    l: List[int] = field(default_factory=list)
    dl: List[int] = field(default_factory=lambda: [1, 2])


class TestDataClassList(unittest.TestCase):
    def test_primitive_list(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DCPrimitve)
        dc: DCPrimitve = parser.parse_args(
            [
                '--root.l', '0', '1', '0',
            ]
        ).root

        self.assertListEqual(dc.l, [0, 1, 0])
        self.assertListEqual(dc.dl, [1, 2])

    def test_primitive_list_default(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DCPrimitve, DCPrimitve(dl=[4, 5]))
        dc: DCPrimitve = parser.parse_args(
            [
            ]
        ).root

        self.assertListEqual(dc.l, [])
        self.assertListEqual(dc.dl, [4, 5])

    def test_data_class_list(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DC)
        dc: DC = parser.parse_args(
            [
                '--root.l', 'test.test_dataclass_list:Sub', 'test.test_dataclass_list:Sub',
                '--root.l.1.int_arg', '-2',
            ]
        ).root

        self.assertListEqual(
            [Sub(int_arg=-1), Sub(int_arg=-2)],
            dc.l
        )

    def test_data_class_list_default(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DC, DC(l=[Sub(int_arg=-1), Sub(int_arg=-2)]))
        dc: DC = parser.parse_args(
            [
                '--root.l.1.int_arg', '-4',
            ]
        ).root

        self.assertListEqual(
            [Sub(int_arg=-1), Sub(int_arg=-4)],
            dc.l
        )

    def test_data_class_list_with_default(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', DCWithDefault)
        dc: DCWithDefault = parser.parse_args(
            [
                '--root.l.1.int_arg', '-4',
            ]
        ).root

        self.assertListEqual(
            [Sub(int_arg=-2), Sub(int_arg=-4)],
            dc.l
        )
