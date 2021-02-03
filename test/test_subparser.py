import unittest
from dataclasses import dataclass

from paiargparse import PAIArgumentParser, pai_dataclass


@pai_dataclass
@dataclass
class Sub1:
    p: int


@pai_dataclass
@dataclass
class Sub2:
    q: int = 5


class TestSubParser(unittest.TestCase):
    def test_sub_parser(self):
        parser = PAIArgumentParser()
        sub_parser = parser.add_subparsers(dest='sub', required=True)

        sub_parser1: PAIArgumentParser = sub_parser.add_parser('sub1')
        sub_parser1.add_root_argument('root', Sub1)
        sub_parser2: PAIArgumentParser = sub_parser.add_parser('sub2')
        sub_parser2.add_root_argument('root', Sub2)

        args = parser.parse_args(args=[
            'sub2'
        ])

        print(args)
