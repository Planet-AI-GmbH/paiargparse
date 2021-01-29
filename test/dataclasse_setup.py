from dataclasses import field

from paiargparse.dataclass_meta import dc_meta, pai_dataclass


@pai_dataclass
class Level2:
    p1: int = 0


@pai_dataclass
class Level2a(Level2):
    p1a: float = 0.1


@pai_dataclass
class Level2b(Level2):
    pb: bool = True


@pai_dataclass
class Level1:
    p1: int = 0
    p2: float = 0.2
    l: Level2 = field(default_factory=Level2)


@pai_dataclass
class Level1b:
    p1: int
    p2: str = ''


@pai_dataclass
class TestMetaLevel2:
    p: str = field(default='', metadata=dc_meta(separator='+'))


@pai_dataclass
class TestMetaLevel1:
    p: int = 0
    sub: TestMetaLevel2 = field(default_factory=TestMetaLevel2, metadata=dc_meta(
        help='Help str',
        separator='/',
    ))


