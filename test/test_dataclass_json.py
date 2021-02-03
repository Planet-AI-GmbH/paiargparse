import unittest

from paiargparse import PAIArgumentParser
from test.dataclasse_setup import Level1


class TestPAIParser(unittest.TestCase):
    def test_two_dc_change(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', Level1)
        args = parser.parse_args(args=['--arg.l.p1', '-13', '--arg.l', 'test.test_data_class:Level2a', '--arg.l.p1a', '0.5'])
        dc = args.arg
        r = Level1.from_json(dc.to_json())

        self.assertEqual(r, dc)


if __name__ == '__main__':
    unittest.main()
