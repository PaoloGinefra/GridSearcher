# GridSearcher

Simple utility to perform deterministic grid searches over parameter spaces.

## Overview

Build a grid by providing a mapping of parameter names to lists or ranges.
`GridSearcher` iterates configurations by combining `SearchField` values using a `ProductSearchPolicy`.
Fixed parameters (non-list and non-range) are kept constant across the search.

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

## Quick example

Create a GridSearcher and iterate results:

```python
from GridSearcher import GridSearcher

grid = { 'x': [0,1], 'fixed': True }
gs = GridSearcher(grid)
for cfg in gs:
	print(cfg)
```
