import json
import os
import unittest
from subprocess import check_output
import sys


this_dir = os.path.dirname(os.path.realpath(__file__))


class TestCmdLine(unittest.TestCase):
    def setUp(self) -> None:
        os.chdir(os.path.join(this_dir, '..', 'examples'))

    def test_single_dc(self):
        from examples.structures.single import ParamSet1, ParamSet2
        out = check_output([sys.executable, 'run_single.py', '--set1.required_str_param', 'test'])
        data_dict = json.loads(out)
        p1 = ParamSet1.from_dict(data_dict['set1'])
        p2 = ParamSet2.from_dict(data_dict['set2'])
        self.assertIsInstance(p1, ParamSet1)
        self.assertIsInstance(p2, ParamSet2)
        self.assertEqual('test', p1.required_str_param)

    def test_hierarchical_dc(self):
        from examples.structures.hierarchical import Child1, Parent, Child2
        out = check_output([sys.executable, 'run_hierarchical.py'])
        p = Parent.from_json(out)
        self.assertIsInstance(p.child, Child1)

        out = check_output([sys.executable,
                            'run_hierarchical.py',
                            '--root.child', 'examples.structures.hierarchical:Child2'])
        p = Parent.from_json(out)
        self.assertIsInstance(p.child, Child2)

    def test_flat_hierarchical_dc(self):
        from examples.structures.flat import Parent, Child1, Child2
        out = check_output([sys.executable, 'run_flat.py', '--req_int', '10'])
        p = Parent.from_json(out)
        self.assertEqual(p.req_int, 10)
        self.assertIsInstance(p.child, Child1)

        out = check_output([sys.executable,
                            'run_flat.py',
                            '--req_int', '5',
                            '--child', 'examples.structures.flat:Child2'])
        p = Parent.from_json(out)
        self.assertIsInstance(p.child, Child2)
