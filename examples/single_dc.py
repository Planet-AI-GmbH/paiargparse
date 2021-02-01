import json

from paiargparse import pai_dataclass, PAIArgumentParser


@pai_dataclass
class ParamSet1:
    required_str_param: str
    int_param: int = 0
    float_param: float = 1.0


@pai_dataclass
class ParamSet2:
    required_str_param: str
    int_param: int = 4
    float_param: float = 5.0


if __name__ == '__main__':
    parser = PAIArgumentParser()

    # ParamSet 1
    parser.add_root_argument("set1", ParamSet1)

    # ParamSet 2 but with different default
    parser.add_root_argument("set2", ParamSet2, default=ParamSet2(required_str_param="test_str", int_param=5))

    # parse args
    args = parser.parse_args()

    print(json.dumps({'set1': args.set1.to_dict(), 'set2': args.set2.to_dict()}))
