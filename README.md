[![Python package](https://github.com/Planet-AI-GmbH/paiargparse/actions/workflows/python-package.yml/badge.svg)](https://github.com/Planet-AI-GmbH/paiargparse/actions/workflows/python-package.yml)
[![Upload Python Package](https://github.com/Planet-AI-GmbH/paiargparse/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Planet-AI-GmbH/paiargparse/actions/workflows/python-publish.yml)

# PAI Argument Parser

The PAI Argument Parser extends the common python argument parser by allowing to automatically parse and add arguments 
based on dataclasses.

See the following example for usage:

```python
from typing import List
from paiargparse import pai_dataclass, pai_meta, PAIArgumentParser
from dataclasses import dataclass, field

@pai_dataclass
@dataclass
class SubmoduleParams:
    required_float_arg: float
    list_arg: List[int] = field(default_factory=lambda: [1, 2])
    arg_with_custom_help: str = field(default="You can specify a custom help string", metadata=pai_meta(
        help="Custom help string."
    ))

@pai_dataclass
@dataclass
class MyArguments:
    required_int_arg: int
    optional_str_arg: str = "This is cool stuff"
    sub_params: SubmoduleParams = field(default_factory=lambda: SubmoduleParams(required_float_arg=2))


if __name__ == "__main__":
    parser = PAIArgumentParser()
    parser.add_root_argument("myArgs", MyArguments)
    args = parser.parse_args()
```

Call with
```shell
python my_program.py --myArgs.required_int_arg 1 --myArgs.sub_params.required_float_arg 0.1
```

Since the parsing is performed dynamically, the help (`-h`) always shows the current state of parsing.

## Supported Types

The following is a list of supported types, and how to access/write their values via the command line

| Type | (example) Name | Cmd Line |
| --- | --- | --- |
| `int`, `str`, `float`, `bool` | `my_primitive` | `--my_primitive 4` |
| `Enum(str)` | `my_enum` | `--my_enum value` |
| `List[int/str/float/bool/Enum(str)]` or `Set[...]` | `my_primitive_list` | `--my_primitive_list 4 2 1` |
| `Dict[str/int, int/str/float/bool/Enum]` | `my_primitive_dict` | `--my_primitive_dict first=1 second=2` |
| `dataclass` | `my_sub_class` | `--my_subclass ClassName --my_subclass.PARAMETER` |
| `List[dataclass]` | `my_list` | `--my_list ClassName ClassName --my_list.0.PARAMETER --my_list.1.PARAMETER` |
| `Dict[str, dataclass]` | `my_dict` | `--my_dict first=ClassName second=ClassName --my_dict.first.PARAMETER --my_dict.second.PARAMETER` |

### Examples

The following shows some examples for the different types

#### Primitive Types
```python
@pai_dataclass
@dataclass
class MyArguments:
    required_int_arg: int
    optional_str_arg: str = "This is cool stuff"

if __name__ == "__main__":
    parser = PAIArgumentParser()
    # If passing flat, the root arg name is not passed in the shell (see below)
    parser.add_root_argument("myArgs", MyArguments, flat=True)
    args = parser.parse_args()
```

Call with
```shell
python my_program.py --required_int_arg 1
```

#### Enumerations
```python

class MyEnum(Enum(str)):
    Tree = 'tree'
    Leaf = 'leaf'

@pai_dataclass
@dataclass
class MyArguments:
    enum: MyEnum = MyEnum.Tree
    enum2: MyEnum = MyEnum.Tree

if __name__ == "__main__":
    parser = PAIArgumentParser()
    parser.add_root_argument("myArgs", MyArguments)
    args = parser.parse_args()
```

Call with
```shell
python my_program.py --myArgs.enum leaf
```

#### Lists and Sets of Primitives
```python
@pai_dataclass
@dataclass
class MyArguments:
    int_list: List[int]
    str_set: Set[str]

if __name__ == "__main__":
    parser = PAIArgumentParser()
    parser.add_root_argument("myArgs", MyArguments)
    args = parser.parse_args()
```

Call with
```shell
python my_program.py --myArgs.int_list 1 2 3 4 --myArgs.str_set Bert Susi Donald
```

#### Dictionaries of Primitives
```python
@pai_dataclass
@dataclass
class MyArguments:
    dict1: Dict[int, str]
    dict2: Dict[str, str]

if __name__ == "__main__":
    parser = PAIArgumentParser()
    parser.add_root_argument("myArgs", MyArguments)
    args = parser.parse_args()
```

Call with
```shell
python my_program.py --myArgs.dict1 1=one 2=two 3=three --myArgs.dict2 one=one two=two three=three
```

#### Child dataclass
```python
@pai_dataclass
@dataclass
class MySubArgs:
    any_arg: int = 0

@pai_dataclass
@dataclass
class MySubArgsAlt(MySubArgs):
    any_other_arg: int = 0
    
@pai_dataclass
@dataclass
class MyArguments:
    sub: MySubArgs

if __name__ == "__main__":
    parser = PAIArgumentParser()
    parser.add_root_argument("myArgs", MyArguments)
    args = parser.parse_args()
```

Call with
```shell
python my_program.py --myArgs.sub.any_arg 2
python my_program.py --myArgs.sub MySubArgsAlt --myArgs.sub.any_other_arg 2
```

#### Lists of dataclasses
```python
@pai_dataclass
@dataclass
class MySubArgs:
    any_arg: int = 0

@pai_dataclass
@dataclass
class MySubArgsAlt(MySubArgs):
    any_other_arg: int = 0
    
@pai_dataclass
@dataclass
class MyArguments:
    sub: List[MySubArgs]

if __name__ == "__main__":
    parser = PAIArgumentParser()
    parser.add_root_argument("myArgs", MyArguments)
    args = parser.parse_args()
```

Call with
```shell
python my_program.py --myArgs.sub MySubArgs MySubArgs MySubArgsAlt --myArgs.sub.0.any_arg 1 --myArgs.sub.2.any_other_arg 3
```

#### Dicts of dataclasses
```python
@pai_dataclass
@dataclass
class MySubArgs:
    any_arg: int = 0

@pai_dataclass
@dataclass
class MySubArgsAlt(MySubArgs):
    any_other_arg: int = 0
    
@pai_dataclass
@dataclass
class MyArguments:
    sub: dict[str, MySubArgs]

if __name__ == "__main__":
    parser = PAIArgumentParser()
    parser.add_root_argument("myArgs", MyArguments)
    args = parser.parse_args()
```

Call with
```shell
python my_program.py --myArgs.sub one=MySubArgs two=MySubArgs three=MySubArgsAlt --myArgs.sub.one.any_arg 1 --myArgs.sub.three.any_other_arg 3
```

### Further examples

Have a look at the various [tests](test) for additional examples.

## Exporting/Importing to dict/json

Since a `pai_dataclass` inherits `dataclass_json`, a dataclass can be writting into a dict and json and read back while preserving the actual types of dataclasses.
This is achieved by an additional `__cls__` field which is added to each `pai_dataclass`. For example:
```python
@pai_dataclass
@dataclass
class SubmoduleParams:
    required_float_arg: float
    list_arg: List[int] = field(default_factory=lambda: [1, 2])
    arg_with_custom_help: str = field(default="You can specify a custom help string", metadata=pai_meta(
        help="Custom help string."
    ))

@pai_dataclass
@dataclass
class MyArguments:
    required_int_arg: int
    optional_str_arg: str = "This is cool stuff"
    sub_params: SubmoduleParams = field(default_factory=lambda: SubmoduleParams(required_float_arg=2))

args = MyArguments(required_int_arg=0, sub_params=SubmoduleParams(required_float_arg=1))
print(args.to_dict()) # {'required_int_arg': 0, 'optional_str_arg': 'This is cool stuff', 'sub_params': {'required_float_arg': 1, 'list_arg': [1, 2], 'arg_with_custom_help': 'You can specify a custom help string', '__cls__': '__main__:SubmoduleParams'}, '__cls__': '__main__:MyArguments'}
assert(MyArguments.from_dict(args.to_dict()) == args)  # True
assert(MyArguments.from_json(args.to_json()) == args)  # True
```

## Meta-Data

Set the `metadata`-argument of `field` to `pai_meta` to enrich the information for the argument parser:

| argname | default | description | example |
| --- | --- | --- | --- |
| help | `None` | The helpstring to print when calling -h | `pai_meta(help="Show the help")` |
| separator | `"."` | The separator for concatenating hierarchial args, e.g. `/` to use `parent/sub` | `pai_meta(separator="/")` |
| mode | `"snake"` | Use `"ignore"` to ignore this field from the command line, use `"flat"` to add the argument as a new root argument, i.e. no prefixes will be added, use `"snake"` for the default mode of snaking all arguments with the separator, use `"ssnake"` to drop only the parent prefix of one hierachy` | `pai_meta(mode="ignore")` |
| required | `None` | Set to `True` or `False` to force if this parameter must be set from the command line even though a default value is given | `pai_meta(required=True)` | 
| nargs | `*` | Override the default `nargs` field for list, set, or dict fields. The alternative `+` forces to add at least one element to the list. | `pai_meta(nargs="+")` |
| choices | `None` | A list of choices the select from when using lists, sets or subdataclasses. Only the class name must be set in the command line if the class is present in choices (instead of the full path) | `pai_meta(choices=[SubClass1, SubClass2])`
| disable_subclass_check | `False` | By default changing the type of a class via the command line requires that the new class is a subclass of the type of the dataclass field. Use this flag to disable this check. | `pai_meta(disable_subclass_check=True` |
| enforce_choices | `None` | Override the default choices checking. For dataclasses, it is permitted to select dataclasses that are not in choices, for primitive types they must be within choices | `pai_meta(enforce_choices=True)` |
| fix_dc | `False` | Set to true to forbit overriding of a dataclass via the command line | `pai_meta(fix_dc=True)` | 
