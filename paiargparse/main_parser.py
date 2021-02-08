from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from typing import Any

from paiargparse.dataclass_parser import PAIDataClassArgumentParser


class PAIArgumentParser(ArgumentParser):
    """
    Argument parser based on hierarchical dataclasses
    """

    def __init__(self,
                 add_help=True,
                 formatter_class=ArgumentDefaultsHelpFormatter,
                 ignore_required=False,
                 *args, **kwargs):
        super(PAIArgumentParser, self).__init__(add_help=False, formatter_class=formatter_class, *args, **kwargs)

        self._data_class_parser = PAIDataClassArgumentParser(add_help=add_help, formatter_class=formatter_class,
                                                             ignore_required=ignore_required)

    def add_root_argument(self, param_name: str, dc_type: Any, default: Any = None):
        self._data_class_parser.add_root_argument(param_name, dc_type, default)

    def parse_known_args(self, args=None, namespace=None):
        # parse args that match the default arg parser
        namespace, args = super(PAIArgumentParser, self).parse_known_args(args, namespace)

        # (recursively) parse args that match the data class arg parser
        namespace, args = self._data_class_parser.parse_known_args(args, namespace)

        # Ok!
        return namespace, args
