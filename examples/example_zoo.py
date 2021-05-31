from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List

from paiargparse import pai_dataclass, PAIArgumentParser, pai_meta


@pai_dataclass
@dataclass
class Animal(ABC):
    name: str
    age: Optional[int] = None

    @abstractmethod
    def make_sound(self):
        raise NotImplementedError


@pai_dataclass
@dataclass
class Dog(Animal):
    color: str = "black"

    def make_sound(self):
        if self.color == "brown":
            print(f"{self.name}: Woof, woof")
        else:
            print(f"{self.name}: Woof")


@pai_dataclass
@dataclass
class Duck(Animal):
    def make_sound(self):
        print(f"{self.name}: Quack")


@pai_dataclass
@dataclass
class Zookeeper:
    name: str
    age: int


@pai_dataclass
@dataclass
class Zoo:
    keeper: Zookeeper = field(default_factory=lambda: Zookeeper("Unknown", 50))
    animals: List[Animal] = field(default_factory=list, metadata=pai_meta(choices=[Duck, Dog]))

    def sound(self):
        print(f"Keeper {self.keeper.name}({self.keeper.age}) calls all animals.")
        for animal in self.animals:
            animal.make_sound()


if __name__ == "__main__":
    parser = PAIArgumentParser()
    parser.add_root_argument("zoo", Zoo)
    args = parser.parse_args()
    zoo: Zoo = args.zoo
    zoo.sound()

    # Serializing and deserializing as JSON preserves the actual dataclasses
    assert Zoo.from_json(zoo.to_json()) == zoo

    # Call Arguments:
    # * Set up the keeper name
    # * Setup three animals and set their properties
    # --------------------------------------
    # --zoo.keeper.name Barack
    # --zoo.animals Dog Dog Duck
    # --zoo.animals.0.name Steeve
    # --zoo.animals.0.color brown
    # --zoo.animals.1.name Jessy
    # --zoo.animals.2.name Donald

    # Output
    # --------------------------------------
    # Keeper Barack calls all animals.
    # Steeve: Woof, woof
    # Jessy: Woof
    # Donald: Quack
