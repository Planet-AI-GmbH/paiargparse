import sys
from argparse import ArgumentParser, Action, SUPPRESS, ArgumentDefaultsHelpFormatter, Namespace
from dataclasses import MISSING
from typing import Any, Dict
import importlib

from paiargparse.dataclass_meta import DEFAULT_SEPARATOR
from paiargparse.dataclass_parser import extract_args_of_dataclass, ArgumentField, str_to_enum, enum_choices
from paiargparse.param_tree import PAINode, PAINodeParam, PAINodeDataClass


class RequiredArgumentError(Exception):
    pass


class PAIArgumentParser(ArgumentParser):
    """
    Argument parser based on hierarchical dataclasses
    """
    def __init__(self,
                 formatter_class=ArgumentDefaultsHelpFormatter,
                 *args, **kwargs):
        super(PAIArgumentParser, self).__init__(add_help=False, formatter_class=formatter_class, *args, **kwargs)

        self._default_data_classes_to_set_after_next_run = {}
        self._params_tree = PAINode(None, name='', arg_name='')  # Root

    def _tree_to_data_class(self, node: PAINode):
        for k, v in node.dcs.items():
            node.dcs[k].value = self._tree_to_data_class(v.value)

        # construct actual dataclass
        param_values = node.all_param_values()
        if node.default:
            # set defaults
            for arg in extract_args_of_dataclass(node.default.__class__):
                name = arg.name
                if name in param_values:
                    # already set from cmd
                    continue
                if name not in node.type.__dataclass_fields__:
                    # target data class does not have this field
                    continue
                param_values[name] = getattr(node.default, name)

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

    def add_dc_argument(self, param_name: str, dc_type: Any, root: dict, prefix: str, parent: Dict[str, PAINodeDataClass]):
        pai_node = parent[param_name].value
        if pai_node.default is not None:
            dc_type = pai_node.default.__class__

        class DataClassAction(Action):
            def __call__(self, parser: 'PAIArgumentParser', args, values, option_string=None):
                # Add new args for this argument
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
                                                                  type=arg.type,
                                                                  default=default,
                                                                  name=arg.name, arg_name=f"{prefix}{param_name}{sep}")
                                                              )
                        parser.add_dc_argument(arg.name, arg.type, root_dcs[arg.name].value.dcs, f"{prefix}{param_name}{sep}", parent=root)
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
                                            action=setter_action(root_params[arg.name], arg),
                                            nargs='*' if arg.list else None)

        def setter_action(arg: PAINodeParam, field: ArgumentField):
            class FieldSetterAction(Action):
                def __call__(self, parser, args, values, option_string=None):
                    if field.enum:
                        arg.value = str_to_enum(values, field.enum, field.type)
                    else:
                        arg.value = values
            return FieldSetterAction

        flag = f'--{prefix}{param_name}'
        self._default_data_classes_to_set_after_next_run[flag] = f"{dc_type.__module__}:{dc_type.__name__}"
        self.add_argument(flag, action=DataClassAction, type=str,
                          default=self._default_data_classes_to_set_after_next_run[flag])

    def parse_known_args(self, args=None, namespace=None):
        args = sys.argv[1:] if args is None else list(args)
        if namespace is None:
            namespace = Namespace()

        prev_args = args
        while len(args) > 0 or len(self._default_data_classes_to_set_after_next_run) > 0:
            if len(args) > 0 and args[0] in {'-h', '--help'}:
                break
            for k, v in self._default_data_classes_to_set_after_next_run.items():
                if k not in args:
                    args += [k, v]
            self._default_data_classes_to_set_after_next_run = {}
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
