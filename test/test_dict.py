import unittest
from dataclasses import field, dataclass
from typing import Dict

from paiargparse import pai_dataclass, PAIArgumentParser


@pai_dataclass
@dataclass
class Sub:
    p: int = 0


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
        ]).dc

        self.assertListEqual(['a', 'b', 'c'], list(dc.str_dc.keys()))
        self.assertIsInstance(dc.str_dc['a'], Sub)
        self.assertIsInstance(dc.str_dc['b'], Sub2)
        self.assertIsInstance(dc.str_dc['c'], Sub)
        self.assertEqual(dc.str_dc['a'].p, 1)
        self.assertEqual(dc.str_dc['b'].x, 'test')

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
