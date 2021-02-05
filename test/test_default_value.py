import unittest

from paiargparse import PAIArgumentParser, RequiredArgumentError
from test.dataclasse_setup import Level1b, Level1, Level2a, Level2, Level1Base


class TestPAIParserDefault(unittest.TestCase):
    def test_required_from_default(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1b, default=Level1b(p1=-13))
        args = parser.parse_args(args=[])
        dc = args.arg

        self.assertIsInstance(dc, Level1b)
        self.assertEqual(dc.p1, -13)
        self.assertEqual(dc.p2, '')

    def test_required(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1b)
        with self.assertRaises(RequiredArgumentError):
            parser.parse_args(args=['--arg.p2', 'test'])

    def test_setting_argument_after_override(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1Base, default=Level1b(p1=-1))
        with self.assertRaises(SystemExit):
            parser.parse_args(args=['--arg.l.p1', '-13'])

    def test_setting_second_level(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1, default=Level1(p1=-1, l=Level2a(p1=-13)))
        dc = parser.parse_args(args=['--arg.l.p1a', '-13']).arg

        self.assertIsInstance(dc, Level1)
        self.assertIsInstance(dc.l, Level2a)
        self.assertEqual(dc.p1, -1)
        self.assertEqual(dc.l.p1, -13)
        self.assertEqual(dc.l.p1a, -13)

