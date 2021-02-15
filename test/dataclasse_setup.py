from dataclasses import field, dataclass

from paiargparse import pai_meta, pai_dataclass

@pai_dataclass
@dataclass
class Level3base:
    p: int = 1


@pai_dataclass
@dataclass
class Level3a(Level3base):
    t: float = 2


@pai_dataclass(alt="AlternativeLevel3")
@dataclass
class Level3aa(Level3a):
    q: int = 3


@pai_dataclass
@dataclass
class Level2:
    p1: int = 0
    lvl3: Level3base = field(default_factory=Level3a, metadata=pai_meta(choices=[Level3a, Level3aa], enforce_choices=True))


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
class Level1Base:
    pass


@pai_dataclass
@dataclass
class Level1(Level1Base):
    p1: int = 0
    p2: float = 0.2
    l: Level2 = field(default_factory=Level2)


@pai_dataclass
@dataclass
class Level1b(Level1Base):
    p1: int
    p2: str = ''


@pai_dataclass
@dataclass
class Level1Required:
    pdc: Level2


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


@pai_dataclass
@dataclass
class TestWithRequiredMeta:
    p: int = field(default=1, metadata=pai_meta(required=True))
