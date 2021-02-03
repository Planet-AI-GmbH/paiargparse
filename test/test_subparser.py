import unittest
from dataclasses import dataclass, field

from paiargparse import PAIArgumentParser, pai_dataclass, pai_meta


@pai_dataclass
@dataclass
class Sub1:
    p: int


@pai_dataclass
@dataclass
class Sub2:
    q: int = 5


@pai_dataclass
@dataclass
class Parent:
    c1: Sub1 = field(default_factory=lambda: Sub1(p=2))
    c2: Sub2 = field(default_factory=Sub2, metadata=pai_meta(mode='flat'))


class TestSubParser(unittest.TestCase):
    def test_sub_parser(self):
        parser = PAIArgumentParser()
        sub_parser = parser.add_subparsers(dest='sub', required=True)

        sub_parser1: PAIArgumentParser = sub_parser.add_parser('sub1')
        sub_parser1.add_root_argument('root', Sub1)
        sub_parser2: PAIArgumentParser = sub_parser.add_parser('sub2')
        sub_parser2.add_root_argument('root', Sub2)

        root = parser.parse_args(args=[
            'sub2'
        ]).root

        self.assertIsInstance(root, Sub2)
        self.assertEqual(root.q, 5)

    def test_sub_parser_args(self):
        parser = PAIArgumentParser()
        sub_parser = parser.add_subparsers(dest='sub', required=True)

        sub_parser1: PAIArgumentParser = sub_parser.add_parser('sub1')
        sub_parser1.add_root_argument('root', Sub1)
        sub_parser2: PAIArgumentParser = sub_parser.add_parser('sub2')
        sub_parser2.add_root_argument('root', Sub2)

        root = parser.parse_args(args=[
            'sub2',
            '--root.q', '10',
        ]).root

        self.assertIsInstance(root, Sub2)
        self.assertEqual(root.q, 10)

    def test_sub_parser_flat(self):
        parser = PAIArgumentParser()
        sub_parser = parser.add_subparsers(dest='sub', required=True)

        sub_parser1: PAIArgumentParser = sub_parser.add_parser('sub1')
        sub_parser1.add_root_argument('root', Parent)
        sub_parser2: PAIArgumentParser = sub_parser.add_parser('sub2')
        sub_parser2.add_root_argument('root', Parent)

        root = parser.parse_args(args=[
            'sub2',
            '--root.c1.p', '10',
        ]).root

        self.assertIsInstance(root.c1, Sub1)
        self.assertIsInstance(root.c2, Sub2)
        self.assertEqual(root.c1.p, 10)
