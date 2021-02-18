from dataclasses import dataclass, field, MISSING
from typing import Any, Dict


@dataclass
class PAINode:
    name: str  # Name of the argument
    arg_name: str  # full argument
    value: Any  # value of the argument the user specified, so if None, this is None!

    def is_missing(self):
        return self.value == MISSING


@dataclass
class PAINodeDataClass(PAINode):
    parsed_type: Any  # MISSING if not specified, else the type specified from the cmd line, if None, the user set an (optional) value to None via the cmd line
    default_value: Any  # MISSING if not specified, the default of the 'field' attribute or overwritten by the user via the default arg in 'add_root_argument'
    dcs: Dict[str, 'PAINodeDataClass'] = field(default_factory=dict)
    params: Dict[str, PAINode] = field(default_factory=dict)

    def all_param_values(self):
        return {
            **{k: v.value for k, v in self.dcs.items() if not v.is_missing()},
            **{k: v.value for k, v in self.params.items() if not v.is_missing()},
        }
