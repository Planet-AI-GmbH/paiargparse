from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from dataclasses import MISSING
from typing import Any, List, Type

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

        self._data_class_parser = self._data_class_argument_parser_cls()(
            add_help=add_help, formatter_class=formatter_class, ignore_required=ignore_required)

    def _data_class_argument_parser_cls(self) -> Type[PAIDataClassArgumentParser]:
        return PAIDataClassArgumentParser

    def add_root_argument(self, param_name: str, dc_type: Any, default: Any = MISSING, ignore: List[str] = None):
        self._data_class_parser.add_root_argument(param_name, dc_type, default, ignore=ignore)

    def parse_known_args(self, args=None, namespace=None):
        # parse args that match the default arg parser
        namespace, args = super(PAIArgumentParser, self).parse_known_args(args, namespace)

        # (recursively) parse args that match the data class arg parser
        namespace, args = self._data_class_parser.parse_known_args(args, namespace)

        # Ok!
        return namespace, args
