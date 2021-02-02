from dataclasses import dataclass, _MISSING_TYPE, field
from typing import Any, Dict


@dataclass
class PAINode:
    name: str      # Name of the argument
    arg_name: str  # full argument
    value: Any     # value of the argument

    def is_null(self):
        return isinstance(self.value, _MISSING_TYPE)


@dataclass
class PAINodeDataClass(PAINode):
    type: Any
    default: Any = None
    dcs: Dict[str, 'PAINodeDataClass'] = field(default_factory=dict)
    params: Dict[str, PAINode] = field(default_factory=dict)

    def all_param_values(self):
        return {
            **{k: v.value for k, v in self.dcs.items() if not v.is_null()},
            **{k: v.value for k, v in self.params.items() if not v.is_null()},
        }
