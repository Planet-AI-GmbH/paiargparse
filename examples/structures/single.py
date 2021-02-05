from dataclasses import dataclass

from paiargparse import pai_dataclass


@pai_dataclass
@dataclass
class ParamSet1:
    required_str_param: str
    int_param: int = 0
    float_param: float = 1.0


@pai_dataclass
@dataclass
class ParamSet2:
    required_str_param: str
    int_param: int = 4
    float_param: float = 5.0


