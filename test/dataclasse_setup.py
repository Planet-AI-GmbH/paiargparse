from dataclasses import field, dataclass

from paiargparse import pai_meta, pai_dataclass


@pai_dataclass
@dataclass
class Level2:
    p1: int = 0


@pai_dataclass
@dataclass
class Level2a(Level2):
    p1a: float = 0.1


@pai_dataclass
@dataclass
class Level2b(Level2):
    pb: bool = True


@pai_dataclass
@dataclass
class Level1:
    p1: int = 0
    p2: float = 0.2
    l: Level2 = field(default_factory=Level2)


@pai_dataclass
@dataclass
class Level1b:
    p1: int
    p2: str = ''


@pai_dataclass
@dataclass
class TestMetaLevel2:
    p: str = field(default='', metadata=pai_meta(separator='+'))


@pai_dataclass
@dataclass
class TestMetaLevel1:
    p: int = 0
    sub: TestMetaLevel2 = field(default_factory=TestMetaLevel2, metadata=pai_meta(
        help='Help str',
        separator='/',
    ))


