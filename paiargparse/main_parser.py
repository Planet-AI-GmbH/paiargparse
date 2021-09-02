from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, _SubParsersAction, SUPPRESS, Action
from dataclasses import MISSING, is_dataclass
from functools import partial
from typing import Any, List, Type

import editdistance

from paiargparse.dataclass_parser import PAIDataClassArgumentParser, UnknownArgumentError


class PAIArgumentParser(ArgumentParser):
    """
    Argument parser based on hierarchical dataclasses

    Call `add_root_argument("arg", DataClass)` to add a dataclass to the arguments
    """

    def __init__(
        self,
        add_help=True,
        add_show=True,
        formatter_class=ArgumentDefaultsHelpFormatter,
        ignore_required=False,
        root_parser: "PAIArgumentParser" = None,
        allow_abbrev=False,
        *args,
        **kwargs,
    ):
        super(PAIArgumentParser, self).__init__(
            add_help=False, formatter_class=formatter_class, allow_abbrev=allow_abbrev, *args, **kwargs
        )
        self.root_parser = root_parser if root_parser else self
        self._all_actions = []
        self._add_help = add_help  # store if help should be set
        self._add_show = add_show

        self._data_class_parser = self._data_class_argument_parser_cls()(
            add_help=False, formatter_class=formatter_class, ignore_required=ignore_required, allow_abbrev=allow_abbrev
        )

        # Register the custom subparser that stores the root parser
        self._registries["action"]["parsers"] = partial(_SubParsersActionWithRoot, root_parser=self.root_parser)
        self.register("action", "show", _ShowParametersAction)

    def _data_class_argument_parser_cls(self) -> Type[PAIDataClassArgumentParser]:
        return PAIDataClassArgumentParser

    def add_root_argument(
        self, param_name: str, dc_type: Any, default: Any = MISSING, ignore: List[str] = None, flat=False
    ):
        self._data_class_parser.add_root_argument(param_name, dc_type, default, ignore=ignore, flat=flat)

    def parse_known_args(self, args=None, namespace=None):
        # parse args that match the default arg parser, first this, because these actions are allowed to add
        # additional "dataclass args"
        try:
            namespace, args = super(PAIArgumentParser, self).parse_known_args(args, namespace)
        except SystemExit as e:
            # store if an exception occurred
            exception = e
        else:
            exception = None

        # (recursively) parse args that match the data class arg parser
        namespace, args = self._data_class_parser.parse_known_args(args, namespace)

        # Collect all known args, since now the args might have changes after parsing
        self._collect_all_actions()

        if self._add_show:
            # add help as last
            self.add_argument("--show", action="show", default=SUPPRESS, help="show the parsed parameters")
            if len(args) > 0 and args[0] in {"--show"}:
                return super(PAIArgumentParser, self).parse_known_args(args, namespace)
        if self._add_help:
            # add help as last
            self.add_argument("-h", "--help", action="help", default=SUPPRESS, help="show this help message and exit")
            if len(args) > 0 and args[0] in {"-h", "--help"}:
                return super(PAIArgumentParser, self).parse_known_args(args, namespace)

        if exception:
            exit(1)

        # Ok!
        return namespace, args

    def parse_args(self, args=None, namespace=None):
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            # unknown arguments, but search for nearest matches
            alt_actions = find_alt_actions([a for a in argv if a.startswith("--")], self._all_actions, n_best=3)
            help_str = ["\n" + f"\t{arg} ==> {', '.join(alt)}" for arg, alt in zip(argv, alt_actions)]
            raise UnknownArgumentError(f"Unknown Arguments {' '.join(argv)}. Possible alternatives:{''.join(help_str)}")
        return args

    def _collect_all_actions(self):
        """
        Collect all parsed actions (also of subparsers) to the root parsers
        This will be used to display alternatives on unknown args
        """
        self.root_parser._all_actions.extend(self._actions + self._data_class_parser._actions)

    def format_help(self):
        formatter = self._get_formatter()

        # usage
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups + self._data_class_parser._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()


def _find_most_common_options(arg: str, all_option_strings: List[str]) -> List[str]:
    """Filter commands that (after splitting at '.' have the most common parts)

    e.g. arg="test.cmd.1" and all_option_string=["test.cmd.12" and "test.asdf.fasdf.asdf"] will only return "test.cmd.12"
    """
    cmd1 = set(arg.split("."))

    all_common_cmds = []
    max_common_cnt = 0
    for option_string in all_option_strings:
        cmd2 = set(option_string.split("."))
        common_cmds = cmd1.intersection(cmd2)
        all_common_cmds.append((option_string, common_cmds))
        max_common_cnt = max(max_common_cnt, len(common_cmds))

    # also allow max_comon_cnt -1 to add a bit more variance
    return [option_string for option_string, common_cmds in all_common_cmds if len(common_cmds) >= max_common_cnt - 1]


def find_alt_actions(argv: List[str], actions, n_best=1) -> List[str]:
    """
    Find alternative actions for a given list of args.
    Note, argv should only contain "--" args
    """
    all_option_strings = sum([a.option_strings for a in actions], [])
    if len(all_option_strings) == 0:
        return ["No alternative available."] * len(argv)

    distances = [
        [(option, editdistance.eval(arg, option)) for option in _find_most_common_options(arg, all_option_strings)]
        for arg in argv
    ]
    for distance in distances:
        distance.sort(key=lambda x: x[1])

    return [[x[0] for x in s[:n_best]] for s in distances]


class _SubParsersActionWithRoot(_SubParsersAction):
    """
    Override SubParsers action to store the root parsers and pass it to PAIArgParser on construction (add_parse)
    """

    def __init__(self, *args, root_parser, **kwargs):
        super(_SubParsersActionWithRoot, self).__init__(*args, **kwargs)
        self.root_parser = root_parser

    def add_parser(self, *args, **kwargs):
        return super(_SubParsersActionWithRoot, self).add_parser(*args, root_parser=self.root_parser, **kwargs)


class _ShowParametersAction(Action):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print("============================================================================")
        print("Parsed and default values of the available arguments:")
        for k, v in sorted(vars(namespace).items()):
            if is_dataclass(v):
                continue
            print(f"    {k}={v}")

        print()
        print("============================================================================")
        print("Resulting data classes:")
        for k, v in vars(namespace).items():
            if not is_dataclass(v):
                continue
            print()
            print(f"{k}={v.to_json(indent=2)}")

        print()
        print("============================================================================")
        exit(0)
