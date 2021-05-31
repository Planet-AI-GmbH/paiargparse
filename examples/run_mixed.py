import json

from examples.structures.hierarchical import Parent
from paiargparse import PAIArgumentParser


if __name__ == "__main__":
    parser = PAIArgumentParser()
    parser.add_argument("positional_arg", type=str, help="A positional arg")
    parser.add_argument("--required_arg", type=int, help="This parameter must be specified", required=True)
    parser.add_root_argument("root", Parent)
    args = parser.parse_args()

    d = vars(args)
    d["root"] = d["root"].to_dict()
    print(json.dumps(d))
