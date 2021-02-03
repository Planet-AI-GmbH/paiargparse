import unittest

from paiargparse import PAIArgumentParser, RequiredArgumentError
from test.dataclasse_setup import Level1b, Level2, Level1, Level2a


class TestPAIParser(unittest.TestCase):
    def test_three_dc(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg0', Level1b)
        parser.add_root_argument('arg1', Level2)
        parser.add_root_argument('arg2', Level2a)
        parser.add_root_argument('arg3', Level1)
        args = parser.parse_args(args=['--arg0.p1', '0', '--arg2.p1a', '0.5'])

        self.assertIsInstance(args.arg0, Level1b)
        self.assertIsInstance(args.arg1, Level2)
        self.assertIsInstance(args.arg2, Level2a)
        self.assertIsInstance(args.arg3, Level1)

    def test_three_dc_required(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg0', Level1b)
        parser.add_root_argument('arg1', Level2)
        parser.add_root_argument('arg2', Level2a)
        parser.add_root_argument('arg3', Level1)
        with self.assertRaises(RequiredArgumentError):
            parser.parse_args(args=['--arg3.p1', '0', '--arg2.p1a', '0.5'])


if __name__ == '__main__':
    unittest.main()
