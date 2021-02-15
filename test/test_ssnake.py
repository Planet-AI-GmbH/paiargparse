import unittest
from dataclasses import dataclass, field

from paiargparse import pai_dataclass, pai_meta, PAIArgumentParser


@pai_dataclass
@dataclass
class Child2:
    p2: int = 1

@pai_dataclass
@dataclass
class Child:
    p1: int = 2
    c: Child2 = field(default_factory=Child2)

@pai_dataclass
@dataclass
class Root:
    ssc: Child = field(default_factory=Child, metadata=pai_meta(mode='ssnake'))
    sc: Child = field(default_factory=Child)


class TestSSnake(unittest.TestCase):
    def test_ssnake(self):
        parser = PAIArgumentParser()
        parser.add_root_argument('root', Root)
        root: Root = parser.parse_args([
            '--ssc.p1', '5',
            '--ssc.c.p2', '7',
            '--root.sc.p1', '2']).root
        self.assertEqual(5, root.ssc.p1)
        self.assertEqual(7, root.ssc.c.p2)
        self.assertEqual(2, root.sc.p1)
