# PAI Argument Parser

The PAI Argument Parser extends the common python argument parser by allowing to automatically parse and add arguments 
based on dataclasses.

See the following example for usage:

## Simple Example

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

## Other Features

* Changing of dataclasses to select different modules
* Default params from initial value

See examples and tests for a bunch of different settings and scenarios.