import unittest

from paiargparse import PAIArgumentParser
from test.dataclasse_setup import TestMetaLevel1, TestMetaLevel2


class TestPAIParser(unittest.TestCase):
    def test_three_dc(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('arg', TestMetaLevel1)
        args = parser.parse_args(args=['--arg.p', '0', '--arg/sub+p', '0.5'])

        self.assertIsInstance(args.arg, TestMetaLevel1)
        self.assertIsInstance(args.arg.sub, TestMetaLevel2)
        self.assertEqual(args.arg.p, 0)
        self.assertEqual(args.arg.sub.p, '0.5')


if __name__ == '__main__':
    unittest.main()
