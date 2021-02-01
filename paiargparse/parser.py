import sys
from argparse import ArgumentParser, Action, SUPPRESS, ArgumentDefaultsHelpFormatter, Namespace
from dataclasses import MISSING
from typing import Any, Dict, NamedTuple
import importlib

from paiargparse.dataclass_meta import DEFAULT_SEPARATOR
from paiargparse.dataclass_parser import extract_args_of_dataclass, ArgumentField, str_to_enum, enum_choices
from paiargparse.param_tree import PAINode, PAINodeParam, PAINodeDataClass


class RequiredArgumentError(Exception):
    pass


def _setter_action(arg: PAINodeParam, field: ArgumentField):
    class FieldSetterAction(Action):
        def __call__(self, parser, args, values, option_string=None):
            if field.list:
                if field.enum:
                    arg.value = [str_to_enum(v, field.enum, field.type) for v in values]
                else:
                    arg.value = values
            else:
                if field.enum:
                    arg.value = str_to_enum(values, field.enum, field.type)
                else:
                    arg.value = values

    return FieldSetterAction


def _handle_data_class(
        parser: 'PAIArgumentParser',
        pai_node: PAINode,
        prefix: str,
        param_name: str,
        root: dict,
        values: Any,
        dc_type=None,
):
    # Add new args for this argument
    if dc_type is None:
        if values in parser._default_data_classes_to_set_after_next_run:
            v = parser._default_data_classes_to_set_after_next_run[values]
            if v.value:
                dc_type = v.value.__class__
            else:
                dc_type = v.dc_type

            del parser._default_data_classes_to_set_after_next_run[values]
        else:
            module, class_name = values.split(":")
            dc_type = getattr(importlib.import_module(module), class_name)
    pai_node.type = dc_type
    root_dcs = pai_node.dcs
    root_params = pai_node.params
    for arg in extract_args_of_dataclass(dc_type):
        sep = arg.meta.get('separator', DEFAULT_SEPARATOR)
        mode = arg.meta.get('mode', 'snake')

        if mode == 'ignore':
            continue

        if arg.dataclass:
            default = getattr(pai_node.default, arg.name) if hasattr(pai_node.default, arg.name) else arg.default
            root_dcs[arg.name] = PAINodeDataClass(name=arg.name,
                                                  arg_name=f"{prefix}{param_name}{sep}",
                                                  value=PAINode(
                                                      type=list if arg.list else arg.type,
                                                      default=default,
                                                      name=arg.name, arg_name=f"{prefix}{param_name}{sep}")
                                                  )
            parser.add_dc_argument(arg.name, arg.type, root_dcs[arg.name].value.dcs, f"{prefix}{param_name}{sep}",
                                   parent=root,
                                   nargs=arg.meta.get('nargs', '*') if arg.list else None,
                                   sep=sep,
                                   )
        else:
            if mode == 'snake':
                full_arg_name = f"{prefix}{param_name}{sep}{arg.name}"
            else:
                full_arg_name = f"{arg.name}"
            root_params[arg.name] = PAINodeParam(name=arg.name, arg_name=full_arg_name, value=MISSING)
            choices = enum_choices(arg.enum) if arg.enum else None
            arg_type = str if arg.enum else arg.type
            parser.add_argument(f"--{full_arg_name}",
                                default=None if isinstance(arg.default, MISSING.__class__) else arg.default,
                                help=arg.meta.get('help', "Missing help string"),
                                type=arg_type,
                                choices=choices,
                                action=_setter_action(root_params[arg.name], arg),
                                nargs=arg.meta.get('nargs', '*') if arg.list else None)


class DefaultArg(NamedTuple):
    dc_type: Any = None
    value: Any = None


class PAIArgumentParser(ArgumentParser):
    """
    Argument parser based on hierarchical dataclasses
    """
    def __init__(self,
                 formatter_class=ArgumentDefaultsHelpFormatter,
                 *args, **kwargs):
        super(PAIArgumentParser, self).__init__(add_help=False, formatter_class=formatter_class, *args, **kwargs)

        self._default_data_classes_to_set_after_next_run: Dict[str, DefaultArg] = {}
        self._params_tree = PAINode(None, name='', arg_name='')  # Root

    def _tree_to_data_class(self, node: PAINode):
        for k, v in node.dcs.items():
            node.dcs[k].value = self._tree_to_data_class(v.value)

        # construct actual dataclass
        param_values = node.all_param_values()
        if node.default:
            # set defaults
            if node.type not in {list, tuple}:
                for arg in extract_args_of_dataclass(node.default.__class__):
                    name = arg.name
                    if name in param_values:
                        # already set from cmd
                        continue
                    if name not in node.type.__dataclass_fields__:
                        # target data class does not have this field
                        continue
                    param_values[name] = getattr(node.default, name)

        if node.type in {list, tuple}:
            dc = node.type([v for k, v in param_values.items()])
        else:
            # Check for missing required fields
            missing_required = [f"--{node.params[field.name].arg_name}" for field in extract_args_of_dataclass(node.type) if field.name not in param_values and field.required]
            if len(missing_required) > 0:
                raise RequiredArgumentError('The following arguments are required: {}'.format(', '.join(missing_required)))

            # Instantiate the real class
            dc = node.type(**param_values)

        return dc

    def add_root_argument(self, param_name: str, dc_type: Any, default: Any=None):
        self._params_tree.dcs[param_name] = PAINodeDataClass(name=param_name,
                                                             arg_name=param_name,
                                                             value=PAINode(type=dc_type,
                                                                           default=default,
                                                                           name=param_name,
                                                                           arg_name=param_name,
                                                                           )
                                                             )
        self.add_dc_argument(param_name, dc_type, self._params_tree.dcs[param_name].value.dcs, prefix='', parent=self._params_tree.dcs)

    def add_dc_argument(self,
                        param_name: str,
                        dc_type: Any,
                        root: dict,
                        prefix: str,
                        parent: Dict[str, PAINodeDataClass],
                        nargs=None,
                        sep=DEFAULT_SEPARATOR,  # Only required for nargs
                        ):
        pai_node = parent[param_name].value

        class ListDataClassAction(Action):
            def __call__(self, parser: 'PAIArgumentParser', args, values, option_string=None):
                if len(values) == 1 and values[0] in parser._default_data_classes_to_set_after_next_run:
                    values = values[0]
                    defaults = parser._default_data_classes_to_set_after_next_run[values]
                    del parser._default_data_classes_to_set_after_next_run[values]
                    if defaults.value:
                        dc_types = [v.__class__ for v in defaults.value]
                        defaults = defaults.value
                    else:
                        dc_types = []
                        defaults = []
                else:
                    dc_types = []
                    for i, value in enumerate(values):
                        module, class_name = value.split(":")
                        dc_types.append(getattr(importlib.import_module(module), class_name))
                    defaults = [None] * len(dc_types)

                for i, (dc_type, default) in enumerate(zip(dc_types, defaults)):
                    root_dcs = pai_node.dcs
                    root_dcs[str(i)] = PAINodeDataClass(name=str(i),
                                                        arg_name=f"{prefix}{param_name}{sep}",
                                                        value=PAINode(
                                                            type=dc_type,
                                                            default=default,
                                                            name=str(i), arg_name=f"{prefix}{param_name}{sep}")
                                                        )
                    _handle_data_class(parser, root_dcs[str(i)].value, f"{prefix}{param_name}{sep}", str(i), root_dcs, None, dc_type)

        class DataClassAction(Action):
            def __call__(self, parser: 'PAIArgumentParser', args, values, option_string=None):
                _handle_data_class(parser, pai_node, prefix, param_name, root, values)

        flag = f'{prefix}{param_name}'

        default = DefaultArg(
            dc_type,
            pai_node.default,
        )

        self._default_data_classes_to_set_after_next_run[flag] = default
        self.add_argument('--' + flag,
                          action=DataClassAction if nargs is None else ListDataClassAction,
                          type=str,
                          nargs=nargs
                          )

    def parse_known_args(self, args=None, namespace=None):
        args = sys.argv[1:] if args is None else list(args)
        if namespace is None:
            namespace = Namespace()

        orig_args = args[:]
        prev_args = args
        while len(args) > 0 or len(self._default_data_classes_to_set_after_next_run) > 0:
            if len(args) > 0 and args[0] in {'-h', '--help'}:
                break
            for k, v in list(self._default_data_classes_to_set_after_next_run.items()):
                if f'--{k}' not in orig_args:
                    args += ['--' + k, k]
                else:
                    del self._default_data_classes_to_set_after_next_run[k]
            namespace, args = super(PAIArgumentParser, self).parse_known_args(args, namespace)
            if args == prev_args:
                # No changes, stop parsing
                break
            prev_args = args

        # add help as last
        self.add_argument(
            '-h', '--help',
            action='help', default=SUPPRESS,
            help='show this help message and exit')
        return super(PAIArgumentParser, self).parse_known_args(args, namespace)

    def parse_args(self, args=None, namespace=None):
        args = super(PAIArgumentParser, self).parse_args(args, namespace)

        for name, v in self._params_tree.dcs.items():
            setattr(args, name, self._tree_to_data_class(v.value))
        return args
