from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, _SubParsersAction
from dataclasses import MISSING
from functools import partial
from typing import Any, List, Type

import editdistance

from paiargparse.dataclass_parser import PAIDataClassArgumentParser, UnknownArgumentError


class PAIArgumentParser(ArgumentParser):
    """
    Argument parser based on hierarchical dataclasses

    Call `add_root_argument("arg", DataClass)` to add a dataclass to the arguments
    """

    def __init__(self,
                 add_help=True,
                 formatter_class=ArgumentDefaultsHelpFormatter,
                 ignore_required=False,
                 root_parser: 'PAIArgumentParser' = None,
                 allow_abbrev=False,
                 *args, **kwargs):
        super(PAIArgumentParser, self).__init__(add_help=False, formatter_class=formatter_class,
                                                allow_abbrev=allow_abbrev, *args, **kwargs)
        self.root_parser = root_parser if root_parser else self
        self._all_actions = []

        self._data_class_parser = self._data_class_argument_parser_cls()(
            add_help=add_help, formatter_class=formatter_class, ignore_required=ignore_required,
            allow_abbrev=allow_abbrev)

        # Register the custom subparser that stores the root parser
        self._registries['action']['parsers'] = partial(_SubParsersActionWithRoot, root_parser=self.root_parser)

    def _data_class_argument_parser_cls(self) -> Type[PAIDataClassArgumentParser]:
        return PAIDataClassArgumentParser

    def add_root_argument(self, param_name: str, dc_type: Any, default: Any = MISSING, ignore: List[str] = None,
                          flat=False):
        self._data_class_parser.add_root_argument(param_name, dc_type, default, ignore=ignore, flat=flat)

    def parse_known_args(self, args=None, namespace=None):
        # parse args that match the default arg parser
        namespace, args = super(PAIArgumentParser, self).parse_known_args(args, namespace)

        # (recursively) parse args that match the data class arg parser
        namespace, args = self._data_class_parser.parse_known_args(args, namespace)

        # Collect all known args, since now the args might have changes after parsing
        self._collect_all_actions()

        # Ok!
        return namespace, args

    def parse_args(self, args=None, namespace=None):
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            # unknown arguments, but search for nearest matches
            alt_actions = find_alt_actions([a for a in argv if a.startswith('--')], self._all_actions)
            help_str = ['\n' + f'\t{arg}. Alternative: {alt}' for arg, alt in zip(argv, alt_actions)]
            raise UnknownArgumentError(f"Unknown Arguments {' '.join(argv)}. Possible alternatives:{''.join(help_str)}")
        return args

    def _collect_all_actions(self):
        """
        Collect all parsed actions (also of subparsers) to the root parsers
        This will be used to display alternatives on unknown args
        """
        self.root_parser._all_actions.extend(self._actions + self._data_class_parser._actions)


def find_alt_actions(argv: List[str], actions) -> List[str]:
    """
    Find alternative actions for a given list of args.
    Note, argv should only contain "--" args
    """
    all_option_strings = sum([a.option_strings for a in actions], [])
    if len(all_option_strings) == 0:
        return ['No alternative available.'] * len(argv)

    distances = [[(option, editdistance.eval(arg, option)) for option in all_option_strings] for arg in argv]
    for distance in distances:
        distance.sort(key=lambda x: x[1])

    return [s[0][0] for s in distances]


class _SubParsersActionWithRoot(_SubParsersAction):
    """
    Override SubParsers action to store the root parsers and pass it to PAIArgParser on construction (add_parse)
    """

    def __init__(self, *args, root_parser, **kwargs):
        super(_SubParsersActionWithRoot, self).__init__(*args, **kwargs)
        self.root_parser = root_parser

    def add_parser(self, *args, **kwargs):
        return super(_SubParsersActionWithRoot, self).add_parser(*args, root_parser=self.root_parser, **kwargs)
