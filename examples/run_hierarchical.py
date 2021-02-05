from examples.structures.hierarchical import Parent
from paiargparse import PAIArgumentParser


if __name__ == '__main__':
    parser = PAIArgumentParser()
    parser.add_root_argument("root", Parent)
    args = parser.parse_args()

    print(args.root.to_json())
