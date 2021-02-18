import unittest
from dataclasses import field, dataclass
from typing import Dict

from paiargparse import pai_dataclass, PAIArgumentParser

@pai_dataclass
@dataclass
class SubSub:
    int_arg: int = -2


@pai_dataclass
@dataclass
class Sub:
    p: int = 0
    sub_sub: SubSub = field(default_factory=SubSub)


@pai_dataclass
@dataclass
class Sub2:
    x: str = ''


@pai_dataclass
@dataclass
class DC:
    str_int: Dict[str, int] = field(default_factory=dict)
    int_str: Dict[int, str] = field(default_factory=dict)

    str_dc: Dict[str, Sub] = field(default_factory=dict)
    str_dc_default: Dict[str, Sub] = field(default_factory=lambda: {'a': Sub(), 'b': Sub2()})


class TestDict(unittest.TestCase):
    def test_primitive(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('dc', DC)
        dc: DC = parser.parse_args([
            '--dc.str_int', 'asdf=0', 'fdsa=1',
            '--dc.int_str', '2=qwer', '3=rewq',
        ]).dc

        self.assertDictEqual({'asdf': 0, 'fdsa': 1}, dc.str_int)
        self.assertDictEqual({2: 'qwer', 3: 'rewq'}, dc.int_str)

    def test_primitive_default(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('dc', DC, DC(str_int={'daf': 1}))
        dc: DC = parser.parse_args([
            '--dc.int_str', '2=qwer', '3=rewq',
        ]).dc

        self.assertDictEqual({'daf': 1}, dc.str_int)
        self.assertDictEqual({2: 'qwer', 3: 'rewq'}, dc.int_str)

    def test_str_dataclass_dict(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('dc', DC)
        dc: DC = parser.parse_args([
            '--dc.str_dc', 'a=test.test_dict:Sub', 'b=test.test_dict:Sub2', 'c',
            '--dc.str_dc.a.p', '1',
            '--dc.str_dc.b.x', 'test',
            '--dc.str_dc.a.sub_sub.int_arg', '10',
        ]).dc

        self.assertIsInstance(dc.str_dc, dict)
        self.assertListEqual(['a', 'b', 'c'], list(dc.str_dc.keys()))
        self.assertIsInstance(dc.str_dc['a'], Sub)
        self.assertIsInstance(dc.str_dc['b'], Sub2)
        self.assertIsInstance(dc.str_dc['c'], Sub)
        self.assertEqual(dc.str_dc['a'].p, 1)
        self.assertEqual(dc.str_dc['b'].x, 'test')
        self.assertEqual(dc.str_dc['a'].sub_sub.int_arg, 10)

    def test_str_dataclass_dict_default_field(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('dc', DC)
        dc: DC = parser.parse_args([
            '--dc.str_dc_default.a.p', '1',
            '--dc.str_dc_default.b.x', 'test',
            '--dc.str_dc_default.a.sub_sub.int_arg', '10',
        ]).dc

        self.assertListEqual(['a', 'b'], list(dc.str_dc_default.keys()))
        self.assertIsInstance(dc.str_dc_default['a'], Sub)
        self.assertIsInstance(dc.str_dc_default['b'], Sub2)
        self.assertEqual(dc.str_dc_default['a'].p, 1)
        self.assertEqual(dc.str_dc_default['b'].x, 'test')
        self.assertEqual(dc.str_dc_default['a'].sub_sub.int_arg, 10)

    def test_str_dataclass_dict_default(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('dc', DC, DC(str_dc={'a': Sub(p=1), 'b': Sub2(x='foo')}))
        dc: DC = parser.parse_args([
            '--dc.str_dc.a.p', '5',
        ]).dc

        self.assertListEqual(['a', 'b'], list(dc.str_dc.keys()))
        self.assertIsInstance(dc.str_dc['a'], Sub)
        self.assertIsInstance(dc.str_dc['b'], Sub2)
        self.assertEqual(dc.str_dc['a'].p, 5)
        self.assertEqual(dc.str_dc['b'].x, 'foo')
