import unittest

from paiargparse import PAIArgumentParser, RequiredArgumentError
from paiargparse.dataclass_parser import InvalidChoiceError
from test.dataclasse_setup import Level1b, Level2, Level1, Level2a, Level3a, TestWithRequiredMeta, \
    Level1Required, Level3aa, Level3base


class TestPAIParser(unittest.TestCase):
    def test_single_dc(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1b)
        args = parser.parse_args(args=['--arg.p1', '0', '--arg.p2', 'test'])
        dc = args.arg

        self.assertIsInstance(dc, Level1b)
        self.assertEqual(dc.p1, 0)
        self.assertEqual(dc.p2, 'test')

    def test_invalid_selection(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1)
        with self.assertRaises(TypeError):
            # Error that Level1 is not subclass of Level2 (type of arg.l)
            args = parser.parse_args(args=['--arg.p1', '0',
                                           '--arg.l', 'test.test_data_class:Level1b'])

    def test_invalid_choice(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1)
        with self.assertRaises(InvalidChoiceError):
            # Error that Level1 is not subclass of Level2 (type of arg.l)
            args = parser.parse_args(args=['--arg.p1', '0',
                                           '--arg.l.lvl3', 'test.test_data_class:Level3base'])

    def test_choice_by_alt_name(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1)
        args = parser.parse_args(args=['--arg.p1', '0',
                                       '--arg.l.lvl3', 'AlternativeLevel3'])
        self.assertIsInstance(args.arg.l.lvl3, Level3aa)

    def test_required(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1b)
        with self.assertRaises(RequiredArgumentError):
            parser.parse_args(args=['--arg.p2', 'test'])

    def test_required_dataclass(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1Required)
        with self.assertRaises(RequiredArgumentError):
            parser.parse_args(args=[])

    def test_required_via_meta(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', TestWithRequiredMeta)
        with self.assertRaises(RequiredArgumentError):
            parser.parse_args(args=[])

        parser = PAIArgumentParser(ignore_required=True)
        parser.add_root_argument('arg', TestWithRequiredMeta)
        arg = parser.parse_args(args=[]).arg
        self.assertEqual(1, arg.p)

    def test_two_dc(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1)
        args = parser.parse_args(args=['--arg.l.p1', '-13'])
        dc = args.arg

        self.assertIsInstance(dc, Level1)
        self.assertIsInstance(dc.l, Level2)
        self.assertEqual(dc.l.p1, -13)
        self.assertIsInstance(dc.l.lvl3, Level3a)

    def test_two_dc_change(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1)
        args = parser.parse_args(
            args=['--arg.l.p1', '-13', '--arg.l', 'test.test_data_class:Level2a', '--arg.l.p1a', '0.5'])
        dc = args.arg

        self.assertIsInstance(dc, Level1)
        self.assertIsInstance(dc.l, Level2a)
        self.assertEqual(dc.l.p1, -13)
        self.assertEqual(dc.l.p1a, 0.5)


if __name__ == '__main__':
    unittest.main()
