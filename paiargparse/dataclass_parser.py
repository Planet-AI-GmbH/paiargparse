import importlib
import sys
from argparse import ArgumentParser, Action, SUPPRESS, ArgumentDefaultsHelpFormatter, Namespace
from dataclasses import MISSING, is_dataclass
from typing import Any, Dict, NamedTuple, Optional, List, Union

from paiargparse.dataclass_extractor import extract_args_of_dataclass, ArgumentField, str_to_enum, enum_choices, \
    str_to_bool
from paiargparse.dataclass_meta import DEFAULT_SEPARATOR
from paiargparse.param_tree import PAINode, PAINodeDataClass


class RequiredArgumentError(Exception):
    pass


class InvalidChoiceError(Exception):
    pass

def is_none(v: Union[List[str], str]) -> bool:
    if isinstance(v, list):
        v = v[0]
    return v.lower() in {'none', 'null'}


def type_to_str(t, separator=':'):
    return f"{t.__module__}{separator}{t.__name__}"


def default_dict_key_value(arg: 'DefaultArg'):
    return arg.arg_name


def generate_field_action(pai_node: PAINodeDataClass, arg: PAINode, field: ArgumentField, ignore: List[str]):
    if field.dict_type and field.dataclass:
        # if the value type is again a dataclass, handle this differently
        # The values of the key/value pairs are the type of the dataclass
        # Create an action that adds new sub files based on the key to allow to set the parameters hierarchically

        sep = field.meta.get('separator', DEFAULT_SEPARATOR)

        class DictParserDataclassAction(Action):
            def __call__(self, parser: PAIDataClassArgumentParser, args, values, option_string=None):
                if len(values) == 1 and values[0] in parser._default_data_classes_to_set_after_next_run:
                    # Parse default (if set)
                    values = values[0]
                    defaults = parser._default_data_classes_to_set_after_next_run[values]
                    del parser._default_data_classes_to_set_after_next_run[values]
                    if defaults.value:
                        defaults = defaults.value
                        dict_values = {k: v.__class__ for k, v in defaults.items()}
                    else:
                        defaults = {}
                        dict_values = {}
                else:
                    # Parse values
                    dict_values = {}
                    defaults = {}
                    for value in values:
                        if '=' not in value:
                            k, v = value, field.dict_type
                        else:
                            k, v = value.split('=')
                            module, class_name = v.split(":")
                            v = getattr(importlib.import_module(module), class_name)

                        defaults[k] = None
                        dict_values[k] = v

                # Add new root args for this argument in the params tree,
                # this is basically another 'dataclass' (key to value mapping)
                # However, to not register as dataclass to the arguments (since it already exists = self)
                pai_node.dcs[arg.name] = PAINodeDataClass(name=arg.name,
                                                          arg_name=f"{arg.arg_name}{sep}",
                                                          parsed_type=dict,
                                                          default_value=MISSING,
                                                          value=MISSING,
                                                          )
                root_dcs = pai_node.dcs[arg.name].dcs

                for k, v in dict_values.items():
                    # Add the sub data classes (key k) and add them as parameters (p1, ..., pn)
                    # ...root.k.p1 = ...
                    # ...root.k.p2 = ...
                    dc_type = v
                    root_dcs[k] = PAINodeDataClass(name=k,
                                                   arg_name=f"{arg.arg_name}{sep}",
                                                   parsed_type=dc_type,
                                                   default_value=defaults[k],
                                                   value=None,
                                                   )
                    add_dataclass_field(parser, root_dcs[k], f"{arg.arg_name}{sep}",
                                        root_dcs[k].dcs, values=None, dc_type=dc_type, ignore=ignore)

        return DictParserDataclassAction
    elif field.dict_type:
        class DictParserAction(Action):
            def __call__(self, parser: PAIDataClassArgumentParser, args, values, option_string=None):
                # Handle as normal parameter, but split key value pairs at '='
                arg.value = {}
                for value in values:
                    k, v = value.split('=')
                    k = field.type(k)
                    v = field.dict_type(v)
                    arg.value[k] = v

        return DictParserAction
    else:
        class FieldSetterAction(Action):
            def __call__(self, parser, args, values, option_string=None):
                if field.optional:
                    if is_none(values):
                        arg.value = None
                        return

                is_str_type = field.enum or field.dict_type or field.type == bool or field.type == str

                if field.type == bool:
                    if isinstance(values, list):
                        values = list(map(str_to_bool, values))
                    else:
                        values = str_to_bool(values)
                # Simple field, but handle enumerations separately
                if field.list:
                    if field.enum:
                        arg.value = field.list([str_to_enum(v, field.enum, field.type) for v in values])
                    else:
                        if not is_str_type:
                            values = map(field.type, values)
                        arg.value = field.list(values)
                else:
                    if field.enum:
                        arg.value = str_to_enum(values, field.enum, field.type)
                    else:
                        if not is_str_type:
                            values = field.type(values)
                        arg.value = values

        return FieldSetterAction


def add_dataclass_field(
        parser: 'PAIDataClassArgumentParser',
        pai_node: PAINodeDataClass,
        prefix: str,
        parent_pcs: dict,
        values: Any,
        ignore: List[str],
        dc_type=None,
        arg_field: Optional[ArgumentField] = None,
):
    """
    Add a new sub group to the parser based on the values of a data class
    """
    assert (isinstance(pai_node, PAINodeDataClass))
    if arg_field and arg_field.optional and is_none(values):
        pai_node.parsed_type = None
        pai_node.value = None
        return
    param_name = pai_node.name
    meta = arg_field.meta if arg_field and arg_field.meta else {}
    data_class_choices = None
    if meta.get('choices', None) is not None:
        data_class_choices = list(
            filter(lambda x: x, sum([parser.alt_names_of_choice(cls) for cls in arg_field.meta['choices']], [])))

    # Add new args for this argument
    if dc_type is None:
        if values in parser._default_data_classes_to_set_after_next_run:
            v = parser._default_data_classes_to_set_after_next_run[values]
            del parser._default_data_classes_to_set_after_next_run[values]
            if v.value == MISSING:
                if v.override_missing:
                    dc_type = v.parsed_type  # Type is given
                else:
                    raise RequiredArgumentError(f'The following argument is required: {v.arg_name}')
            elif v.value is not None:
                dc_type = v.value.__class__
            else:
                if not arg_field.optional:
                    raise ValueError("Only optional fields can be None")
                else:
                    return  # Optional field, with default None
        else:
            choices = {}
            if arg_field is not None and meta.get('choices', None) is not None:
                for choice in meta['choices']:
                    for name in parser.alt_names_of_choice(choice):
                        choices[name] = choice
            if values in choices:
                dc_type = choices[values]
            else:
                try:
                    module, class_name = values.split(":")
                except ValueError:
                    if choices:
                        raise ValueError(
                            f"Invalid module and class name {values}. Must be 'path.to.module:class_name' or in {list(choices.keys())}")
                    raise ValueError(f"Invalid module and class name {values}. Must be 'path.to.module:class_name'")
                dc_type = getattr(importlib.import_module(module), class_name)

        if not is_dataclass(dc_type):
            raise TypeError(f"The type of the default value ({dc_type}) is not a dataclass. "
                            f"Maybe you passed the class instead of an instance, i.e., Params instead of Params().")
        if not meta.get('disable_subclass_check', False) and not issubclass(dc_type, pai_node.parsed_type):
            raise TypeError(f"Data class {dc_type} must inherit {pai_node.parsed_type} to allow usage as replacement.")
        pai_node.parsed_type = dc_type
    else:
        assert (dc_type == pai_node.parsed_type)

    pai_node.value = pai_node.parsed_type.__module__ + ":" + dc_type.__name__

    if meta.get('enforce_choices', False) and data_class_choices is not None:
        if dc_type.__name__ not in data_class_choices:
            raise InvalidChoiceError(f"invalid choice: {dc_type.__name__} (chose from {', '.join(data_class_choices)})")

    root_dcs = pai_node.dcs
    root_params = pai_node.params
    for arg in extract_args_of_dataclass(dc_type):
        sep = arg.meta.get('separator', DEFAULT_SEPARATOR)
        mode = arg.meta.get('mode', 'snake')
        assert (mode != 'ignore')
        if mode == 'snake':
            full_arg_name = f"{prefix}{param_name}{sep}"
        elif mode == 'flat':
            full_arg_name = ''
        elif mode == 'ssnake':
            full_arg_name = prefix  # ignore previous param name and separator
        else:
            raise ValueError(f"unsupported mode {mode}.")

        if not arg.dict_type and arg.dataclass:
            root_dcs[arg.name] = PAINodeDataClass(name=arg.name,
                                                  arg_name=full_arg_name,
                                                  parsed_type=arg.list if arg.list else arg.type,
                                                  default_value=getattr(pai_node.default_value, arg.name, arg.default),
                                                  value=MISSING,
                                                  )
            parser.add_dc_argument(root_dcs[arg.name].dcs,
                                   full_arg_name,
                                   parent=parent_pcs,
                                   arg_field=arg,
                                   ignore=ignore,
                                   )
        else:
            full_arg_name += arg.name
            if any(full_arg_name.startswith(ignore_prefixes) for ignore_prefixes in ignore):
                continue

            root_params[arg.name] = PAINode(name=arg.name, arg_name=full_arg_name, value=MISSING)
            choices = enum_choices(arg.enum) if arg.enum else None
            if arg.meta.get('enforce_choices', True) and arg.meta.get('choices', None) is not None:
                choices = arg.meta.get('choices')
            if choices is not None:
                choices = list(map(str, choices))  # always string
            parser.add_argument(f"--{full_arg_name}",
                                default=None if isinstance(arg.default, MISSING.__class__) else arg.default,
                                help=arg.meta.get('help', "Missing help string"),
                                type=str,  # always str, parse type in actual handler
                                choices=choices,
                                action=generate_field_action(pai_node, root_params[arg.name], arg, ignore=ignore),
                                nargs=arg.meta.get('nargs', '*') if arg.list or arg.dict_type else None)

            if arg.dict_type and arg.dataclass:
                default = DefaultArg(
                    dict,
                    getattr(pai_node.default_value, arg.name, arg.default),
                    full_arg_name,
                )
                parser._default_data_classes_to_set_after_next_run[default_dict_key_value(default)] = default


class DefaultArg(NamedTuple):
    parsed_type: Any  # MISSING if not set, else the parsed type (or None)
    value: Any  # MISSING if not set, None and any other value is legitimate
    arg_name: str
    override_missing: bool = False


class PAIDataClassArgumentParser(ArgumentParser):
    """
    Argument parser based on hierarchical dataclasses
    """

    def __init__(self,
                 formatter_class=ArgumentDefaultsHelpFormatter,
                 ignore_required=False,
                 add_help=True,
                 *args, **kwargs):
        super(PAIDataClassArgumentParser, self).__init__(formatter_class=formatter_class, add_help=False, *args,
                                                         **kwargs)

        self._add_help = add_help
        self._default_data_classes_to_set_after_next_run: Dict[str, DefaultArg] = {}
        self._params_tree = PAINodeDataClass(parsed_type=None, default_value=MISSING, name='', arg_name='',
                                             value=None)  # Root
        self.ignore_required = ignore_required

    def _tree_to_data_class(self, node: PAINodeDataClass):
        for k, v in node.dcs.items():
            node.dcs[k].value = self._tree_to_data_class(v)

        # construct actual dataclass
        param_values = node.all_param_values()
        if node.value is None or (node.value == MISSING and node.default_value is None):
            # User set to None and None by default
            return None
        elif node.default_value is not None and node.default_value != MISSING:
            if node.parsed_type is None:
                node.parsed_type = node.default_value.__class__
            if issubclass(node.parsed_type, node.default_value.__class__):
                # set defaults, but only if we are sure that the types are compatible
                if node.parsed_type not in {set, list, tuple}:
                    for arg in extract_args_of_dataclass(node.default_value.__class__, exclude_ignored=False):
                        name = arg.name
                        if name in param_values:
                            # already set from cmd
                            continue
                        if name not in node.parsed_type.__dataclass_fields__:
                            # target data class does not have this field
                            continue
                        param_values[name] = getattr(node.default_value, name)

        if node.parsed_type in {set, list, tuple}:
            dc = node.parsed_type([v for k, v in param_values.items()])
        elif node.parsed_type == dict:
            return param_values
        else:
            # Check for missing required fields (these MUST ALWAYS be set, cause they have no default value in init)
            missing_required = [f"--{node.params[field.name].arg_name}" for field in
                                extract_args_of_dataclass(node.parsed_type) if
                                field.name not in param_values and field.required]
            if len(missing_required) > 0:
                raise RequiredArgumentError(
                    'The following arguments are required: {}'.format(', '.join(missing_required)))
            # These values are required as specified via meta, but they can have a default value.
            # However, this check can be disabled if the 'ignore_required' flag of the parser is set
            if not self.ignore_required:
                missing_meta_required = [f"--{node.params[field.name].arg_name}" for field in
                                         extract_args_of_dataclass(node.parsed_type) if
                                         field.name not in param_values and field.meta and field.meta.get('required')]
                if len(missing_meta_required) > 0:
                    raise RequiredArgumentError(
                        'The following arguments are required: {}'.format(', '.join(missing_meta_required)))

            # Instantiate the real class
            dc = node.parsed_type(**param_values)

        return dc

    def add_root_argument(self, param_name: str, dc_type: Any, default: Any = MISSING, ignore: List[str] = None):
        if ignore is None:
            ignore = []

        if not isinstance(dc_type, type):
            raise TypeError(
                "Not passing a type to dc_type. If you want to pass default values, use the default argument.")
        self._params_tree.dcs[param_name] = PAINodeDataClass(name=param_name,
                                                             arg_name=param_name,
                                                             parsed_type=dc_type,
                                                             default_value=default,
                                                             value=None,
                                                             )
        self.add_dc_argument(
            self._params_tree.dcs[param_name].dcs,
            prefix='',
            parent=self._params_tree.dcs,
            arg_field=ArgumentField(
                param_name,
                dc_type,
                {},
                False,
                [],
                True,
                default,
                required=False,
                enum=None,
                dict_type=None,
            ),
            ignore=ignore,
            override_missing=True,
        )

    def add_dc_argument(self,
                        root: dict,
                        prefix: str,
                        parent: Dict[str, PAINodeDataClass],
                        arg_field: ArgumentField,
                        ignore: List[str],
                        override_missing=False,
                        ):
        param_name = arg_field.name
        dc_type = arg_field.type
        sep = arg_field.meta.get('separator', DEFAULT_SEPARATOR)
        nargs = arg_field.meta.get('nargs', '*')
        pai_node = parent[param_name]

        class ListDataClassAction(Action):
            def __call__(self, parser: 'PAIDataClassArgumentParser', args, values, option_string=None):
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
                                                        parsed_type=dc_type,
                                                        default_value=default,
                                                        value=None,
                                                        )
                    add_dataclass_field(parser, root_dcs[str(i)], f"{prefix}{param_name}{sep}", root_dcs[str(i)].dcs,
                                        values=None, dc_type=dc_type, ignore=ignore)

        class DataClassAction(Action):
            def __call__(self, parser: 'PAIDataClassArgumentParser', args, values, option_string=None):
                add_dataclass_field(parser, pai_node, prefix, root, values, arg_field=arg_field, ignore=ignore)

        flag = f'{prefix}{param_name}'
        if any(flag.startswith(ignore_prefixes) for ignore_prefixes in ignore):
            return

        default = DefaultArg(
            pai_node.parsed_type,
            pai_node.default_value,
            flag,
            override_missing=override_missing,
        )

        def make_action():
            if arg_field.list:
                return ListDataClassAction, nargs
            elif arg_field.dict_type:
                raise NotImplementedError
            else:
                return DataClassAction, None

        self._default_data_classes_to_set_after_next_run[default_dict_key_value(default)] = default

        if arg_field.meta.get('fix_dc', False):
            # if the dataclass is fixed, just add it right away
            if arg_field.list or arg_field.dict_type:
                raise ValueError("Only a standard field can be fixed")
            add_dataclass_field(self, pai_node, prefix, root, default_dict_key_value(default), arg_field=arg_field,
                                ignore=ignore)
        else:
            action, nargs = make_action()
            self.add_argument('--' + flag,
                              action=action,
                              type=str,
                              nargs=nargs,
                              )

    def parse_known_args(self, args=None, namespace=None):
        args = sys.argv[1:] if args is None else list(args)
        if namespace is None:
            namespace = Namespace()

        orig_args = args[:]
        prev_args = args
        while len(args) > 0 or len(self._default_data_classes_to_set_after_next_run) > 0:
            for k, v in list(self._default_data_classes_to_set_after_next_run.items()):
                v: DefaultArg = v
                if f'--{k}' not in orig_args:
                    args += ['--' + k, default_dict_key_value(v)]
                else:
                    del self._default_data_classes_to_set_after_next_run[k]
            namespace, args = super(PAIDataClassArgumentParser, self).parse_known_args(args, namespace)
            if args == prev_args:
                # No changes, stop parsing
                break
            prev_args = args

            # If help string is set, break, but only if nothing is left to process
            if len(args) > 0 and args[0] in {'-h', '--help'} and len(
                    self._default_data_classes_to_set_after_next_run) == 0:
                break

        for name, v in self._params_tree.dcs.items():
            setattr(namespace, name, self._tree_to_data_class(v))

        if self._add_help:
            # add help as last
            self.add_argument(
                '-h', '--help',
                action='help', default=SUPPRESS,
                help='show this help message and exit')
            if len(args) > 0 and args[0] in {'-h', '--help'}:
                return super(PAIDataClassArgumentParser, self).parse_known_args(args, namespace)

        return namespace, args

    def parse_args(self, args=None, namespace=None):
        args = super(PAIDataClassArgumentParser, self).parse_args(args, namespace)
        return args

    def alt_names_of_choice(self, choice) -> List[str]:
        names = [choice.__name__]
        if hasattr(choice, '__alt_name__') and choice.__alt_name__:
            names.append(choice.__alt_name__)

        return names

