# GridSearcher

Simple utility to perform deterministic grid searches over parameter spaces.

## Overview

GridSearcher generates concrete configuration dictionaries from a nested
parameter specification. The top-level input must be a mapping with exactly
one run name (a string) whose value is the parameter tree. Fixed parameters
are kept as-is; parameters you want to vary must be written using the
project's reserved-key descriptors (see "Reserved Keys").

Key points:

- Input may be provided as a Python dict or as a YAML file (use
  `GridSearcher.fromYAML(path)`).
- The top-level object must contain a single run name, for example
  `{'experiment1': {...}}`.
- Varying parameters are declared with reserved keys such as
  `__list__` and `__range__`. Nested parameters are supported and their
  search keys are applied into the nested output dicts.

Minimal YAML-like example:

```yaml
my_run:
  learning_rate:
    __list__:
      values: [0.1, 0.01]
  batch: 32 # fixed value
  model:
    layers:
      __range__:
        from: 2
        to: 5
```

This will yield configurations where `learning_rate` and `model.layers`
are varied and `batch` stays fixed.

## Installation

Clone the repository and install in editable mode:

```cmd
git clone https://github.com/PaoloGinefra/GridSearcher.git
cd GridSearcher
pip install -e .
```

Or install directly from Git:

```cmd
pip install git+https://github.com/PaoloGinefra/GridSearcher.git
```

## Reserved Keys

- `__list__`: Iterate over its values, passed in the `values` parameter.

```YAML
NameOfTheParam:
	__list__:
		values:
			- value1
			- value2
			- ...
```

- `__range__`: Iterate over a given range of values. It expects a `from` and `to` parameters and optionally a `step` one.

```YAML
NameOfTheParam:
	__range__:
		from: start [Included]
		to: end [Excluded]
		[optional]
		step: step
```

## Quick example

Create a GridSearcher and iterate results:

```python
from GridSearcher import GridSearcher
from alive_progress import alive_it
import time

gridConfig = {
    'test': {
        'category': ['electronics', 'books', 'clothing'],
        'price': range(1, 5),
        'yolo': ['yes', 'no'],
        'sus': {
            '__range__': {
                'from': 1,
                'to': 3,
            }
        },
        'Listed': {
            '__list__': {
                'values': ['first', 'second']
            }
        },
        'nested': {
            'range': {
                '__range__': {
                    'from': 1,
                    'to': 4,
                }
            }
        }
    }
}
searcher = GridSearcher(gridConfig)
print(searcher)

print(len(searcher))

for i in alive_it(list(searcher)):
    time.sleep(0.5)
    print(i)
```

## Logging

GridSearcher optionally writes logs and the parsed grid configuration when a `GridSearcher` instance is created.

- Where logs are created: the `loggingPath` parameter passed to `GridSearcher` (default `./`) is used as the base. Inside it the logger creates `GridSearcherLogs/<runName>/vN/` where `vN` is an incrementing version to avoid collisions.
- Files created:
  - `logs.txt` — a plain text file with DEBUG-level file logging.
  - `grid_config.yaml` — a YAML dump of the original grid configuration saved at construction time.
- Log format and handlers: the package uses Python's `logging` module. Console output is INFO-level, file output is DEBUG-level. The formatter is:

```
%(asctime)s | %(levelname)s | %(name)s | %(message)s
```

with timestamps formatted as `YYYY-MM-DD HH:MM:SS`.

How to control logging:

- Pass `loggingPath` to the `GridSearcher` constructor to change where logs are written, e.g. `GridSearcher(grid, loggingPath='my_logs')`.
- If you need different logging behaviour (handlers, levels, rotation, etc.), get the `Logger` instance from the `GridSearcher` object (`searcher.logger`) and reconfigure it using the standard `logging` APIs.
