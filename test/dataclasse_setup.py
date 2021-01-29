from dataclasses import dataclass, field

from paiargparse.dataclass_meta import dc_meta


@dataclass
class Level2:
    p1: int = 0


@dataclass
class Level2a(Level2):
    p1a: float = 0.1


@dataclass
class Level2b(Level2):
    pb: bool = True


@dataclass
class Level1:
    p1: int = 0
    p2: float = 0.2
    l: Level2 = field(default_factory=Level2)


@dataclass
class Level1b:
    p1: int
    p2: str = ''


@dataclass
class TestMetaLevel2:
    p: str = field(default='', metadata=dc_meta(separator='+'))


@dataclass
class TestMetaLevel1:
    p: int = 0
    sub: TestMetaLevel2 = field(default_factory=TestMetaLevel2, metadata=dc_meta(
        help='Help str',
        separator='/',
    ))


