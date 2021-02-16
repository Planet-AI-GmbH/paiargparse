import unittest
from dataclasses import dataclass, field
from typing import Dict, List

from paiargparse import pai_dataclass, PAIArgumentParser


@pai_dataclass
@dataclass
class Child:
    s: str = ''


@pai_dataclass
@dataclass
class Base:
    i: int = 0
    c: Child = field(default_factory=Child)
    d: Dict[str, Child] = field(default_factory=lambda: {'first': Child(), 'second': Child()})
    l: List[Child] = field(default_factory=lambda: [Child(), Child()])


class TestIgnore(unittest.TestCase):
    def test_primitive(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root'])
        with self.assertRaises(SystemExit):
            parser.parse_args(['--root.i', '1']).root

        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.'])
        with self.assertRaises(SystemExit):
            parser.parse_args(['--root.i', '1']).root

        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.i'])
        with self.assertRaises(SystemExit):
            parser.parse_args(['--root.i', '1']).root

        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.s'])
        base: Base = parser.parse_args(['--root.i', '1']).root
        self.assertEqual(base.i, 1)

        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.c'])
        with self.assertRaises(SystemExit):
            parser.parse_args(['--root.c.s', 'asdf']).root

        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.i'])
        base: Base = parser.parse_args(['--root.c.s', 'asdf']).root
        self.assertEqual(base.c.s, 'asdf')

    def test_dict(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.d.first'])
        with self.assertRaises(SystemExit):
            parser.parse_args(['--root.d.first.s', 'asdf']).root

        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.i'])
        base: Base = parser.parse_args(['--root.d.first.s', 'asdf']).root
        self.assertEqual(base.d['first'].s, 'asdf')

        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.d.first'])
        base: Base = parser.parse_args(['--root.d.second.s', 'asdf']).root
        self.assertEqual(base.d['first'].s, '')
        self.assertEqual(base.d['second'].s, 'asdf')

    def test_list(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.l.0'])
        with self.assertRaises(SystemExit):
            parser.parse_args(['--root.l.0.s', 'asdf']).root

        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.i'])
        base: Base = parser.parse_args(['--root.l.0.s', 'asdf']).root
        self.assertEqual(base.l[0].s, 'asdf')

        parser = PAIArgumentParser()
        parser.add_root_argument('root', Base, ignore=['root.l.0'])
        base: Base = parser.parse_args(['--root.l.1.s', 'asdf']).root
        self.assertEqual(base.l[0].s, '')
        self.assertEqual(base.l[1].s, 'asdf')

