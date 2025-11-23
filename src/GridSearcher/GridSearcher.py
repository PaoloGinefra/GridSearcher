"""GridSearcher — quick overview for new contributors.

This module implements a small grid-search engine that takes a single
top-level run mapping and expands "reserved-key" descriptors into concrete
configurations. Parsing separates fixed data (baseConfig) from varying
parameters (SearchField objects) and produces a ProductSearchPolicy that
yields the Cartesian product of all discovered iterables.

Key points:
- Input: a dict with exactly one top-level run name mapping to nested data.
- Reserved descriptors: currently `__range__` and `__list__`; they are
    recognized only when a dict has exactly one key equal to a reserved name.
- Lists are parsed per element; each element may be fixed or a reserved
    descriptor (or contain nested descriptors). List element positions are
    preserved and emitted using internal tokens like `>0` when building keys.
- SearchField keys are encoded using '|' between nested dict keys and
    list-member tokens (`>N`) for indices. The ProductSearchPolicy combines
    all SearchFields by Cartesian product. Iteration applies partial updates
    (encoded_key -> value) to a mutable config via `__setFromKey` and
    returns deep-copied concrete configs.

Error modes: top-level must be one key; user-supplied keys cannot contain
the internal separators ('|' or stray '>'). Malformed reserved descriptors
raise from the ReservedKeys parsers.

Example (how keys are encoded and placeholders used):

    Input:
        {
            'run': {
                'category': [
                    {'__range__': {'from': 1, 'to': 3}},   # list element 0 is a range
                    'books',                               # list element 1 fixed
                    {'var': {'__list__': {'values': ['clothing','accessories']}}}  # element 2 has nested reserved
                ]
            }
        }

    After parsing:
        baseConfig = {
            'category': ['', 'books', {'var': ''}]
        }

        SearchFields (examples of encoded keys):
            - 'category|>0'         -> iterable(range(1, 3))           # expands to 1,2
            - 'category|>2|var'     -> ['clothing', 'accessories']

    During iteration the ProductSearchPolicy will emit partial updates like
    {'category|>0': 1, 'category|>2|var': 'clothing'} which are applied to
    the baseConfig via the encoded keys to produce a concrete config.

"""

from typing import Dict, Tuple, Any, List, Union
from .SearchField import SearchField
from .SearchPolicy import SearchPolicy
from .ProductSearchPolicy import ProductSearchPolicy
from .ReservedKeys import ReservedKeys
from copy import deepcopy
import yaml
from .Logger import Logger
import os


class GridSearcher:
    """Perform a grid search over a nested parameter configuration.

    The class expects a mapping with a single top-level run name that maps to
    a nested parameter tree. Varying parameters are expressed using the
    project's ReservedKeys format and are converted into SearchField objects;
    everything else becomes part of the immutable base configuration for each
    generated sample.

    Example input shape:

        {
            'run1': {
                'lr': {'__range__': {
                    'from': 0.01,
                    'to': 0.1,
                    'step': 0.01
                }},
                'batch': 32,
                'model': {'layers': {'__list__': {'values': ['MLP', 'CNN']}}}
            }
        }

    Typical usage:

        gs = GridSearcher(grid_dict_or_loaded_yaml)
        for config in gs:
            # `config` is a full dict combining base values and chosen parameters
            train(config)
    """

    DICT_KEY_SEPARATOR = '|'
    LIST_KEY_SEPARATOR = '>'
    # Separator used to encode nested keys into a single search-field key

    def __init__(self, gridConfig: Dict, loggingPath: str = './'):
        """The constructor for the GridSearcher class. It parses the given grid configuration and prepares the search policy and base configuration.

        ## Args:
            **gridConfig** (Dict): The configuration for the grid search of the form:
            ```python
        {
            'run1': {
                'lr': {'__range__': {
                    'from': 0.01,
                    'to': 0.1,
                    'step': 0.01
                }},
                'batch': 32,
                'model': {'layers': {'__list__': {'values': ['MLP', 'CNN]}}}
            }
        }
            ```
            You can also include fixed parameters that will not be changed during the search.

            **loggingPath** (str): The directory where logs will be saved.
        """
        self.gridConfig = gridConfig
        self.loggingPath = loggingPath
        self.runName, self.searchPolicy, self.baseConfig = self.parseConfig(
            gridConfig)
        self.currentConfig = deepcopy(self.baseConfig)

        self.logger = Logger(self.runName, self.loggingPath)
        self.logger.logGridConfig(self.gridConfig)

    def __iter__(self):
        return self

    def __next__(self) -> Dict[str, Any]:
        """Generate the next concrete configuration dictionary.

        The underlying search policy yields partial updates as mappings from
        encoded keys (joined by the class constant `DICT_KEY_SEPARATOR` ("|"))
        to values. This method splits those keys, applies updates to the
        mutable `currentConfig`, and returns a deepcopy snapshot so callers
        receive an independent copy.
        """
        try:
            update = next(self.searchPolicy)
            # Apply each partial update (encoded_key -> value) to currentConfig
            for key, value in update.items():
                keyList = key.split(self.DICT_KEY_SEPARATOR)
                GridSearcher.__setFromKey(keyList, self.currentConfig, value)

            # Return a defensive deepcopy snapshot for the caller
            return deepcopy(self.currentConfig)
        except StopIteration:
            raise StopIteration

    @staticmethod
    def __setFromKey(keyList: List[str], target: Union[Dict, List], value: Any):
        """Recursive helper to set a value into a nested dict by key path.

        Creates intermediate dicts when missing. If an intermediate path exists
        but is not a dict, a TypeError may occur when indexing into it.
        """
        if isinstance(target, list):
            GridSearcher.__setFromListKey(keyList, target, value)
            return

        if len(keyList) == 1:
            target[keyList[0]] = value
            return

        GridSearcher.__setFromDictKey(keyList, target, value)

    @staticmethod
    def __setFromListKey(keyList: List[str], target: List, value: Any):
        """Handle the case where the current target is a list:
            - ensures the list is large enough for the index
            - creates a dict or list for the element when recursing further
            - assigns the value when at the final key
        """
        # Expect a list-key like '>0'
        index = int(keyList[0][1:])
        # Extend list if index out of range
        if index >= len(target):
            target.extend([None] * (index - len(target) + 1))

        # If this is the final key for the list element, assign directly
        if len(keyList) == 1:
            target[index] = value
            return

        # Ensure the list element is a dict/list we can recurse into
        if target[index] is None or not isinstance(target[index], (dict, list)):
            # when next key is a list-key we need a list, else a dict
            next_key = keyList[1]
            if next_key and next_key[0] == GridSearcher.LIST_KEY_SEPARATOR:
                target[index] = []
            else:
                target[index] = {}

        # Recurse into the element
        GridSearcher.__setFromKey(keyList[1:], target[index], value)

    @staticmethod
    def __setFromDictKey(keyList: List[str], target: Dict, value: Any):
        """Handle the case where the current target is a dict.

        Creates intermediate containers when missing (dict or list depending on token) and recurse.
        """
        if keyList[0] not in target:
            if keyList[0][0] == GridSearcher.LIST_KEY_SEPARATOR:
                target[keyList[0]] = []
            else:
                target[keyList[0]] = {}
        GridSearcher.__setFromKey(keyList[1:], target[keyList[0]], value)

    @staticmethod
    def parseConfig(gridConfig: Dict) -> Tuple[str, SearchPolicy, Dict]:
        """Parse gridConfig into (searchPolicy, baseConfig).

        Expects `gridConfig` to contain exactly one top-level key (the run
        name). Descends one level, splits fixed values into `baseConfig` and
        varying parameters into `searchFields`, then creates a
        `ProductSearchPolicy` from the discovered fields.

        Returns:
            (str, SearchPolicy, Dict): name of the run, policy to iterate combinations, and the base config.
        """
        if len(gridConfig) != 1:
            raise ValueError(
                f"Grid configuration must contain exactly one key with the run name, got {list(gridConfig.keys())}"
            )

        # Extract the run-level mapping
        configName = list(gridConfig.keys())[0]
        gridConfig = gridConfig[configName]

        searchFields: List[SearchField] = []
        baseConfig: Dict = {}

        # Populate searchFields and baseConfig by walking the nested dict
        GridSearcher.__recursiveParse(gridConfig, baseConfig, searchFields)

        searchPolicy = ProductSearchPolicy(searchFields)
        return configName, searchPolicy, baseConfig

    @staticmethod
    def __validate_user_key(key: str, currentKey: str = ''):
        """Validate that a user-provided key does not contain reserved separators.

        Internal list-member tokens like '>0' (used by the parser) are allowed
        when generated internally but are rejected when present in user keys.
        """
        if GridSearcher.DICT_KEY_SEPARATOR in key:
            full = (currentKey + GridSearcher.DICT_KEY_SEPARATOR +
                    key) if currentKey else key
            raise ValueError(
                f"Key '{full}' contains reserved separator '{GridSearcher.DICT_KEY_SEPARATOR}'")
        if GridSearcher.LIST_KEY_SEPARATOR in key:
            if not (key.startswith(GridSearcher.LIST_KEY_SEPARATOR) and key[1:].isdigit()):
                full = (currentKey + GridSearcher.DICT_KEY_SEPARATOR +
                        key) if currentKey else key
                raise ValueError(
                    f"Key '{full}' contains reserved separator '{GridSearcher.LIST_KEY_SEPARATOR}'")

    @staticmethod
    def __join_key(currentKey: str, key: str) -> str:
        """Return the encoded nested key by joining currentKey and key using the dict separator."""
        return (currentKey + GridSearcher.DICT_KEY_SEPARATOR + key) if currentKey else key

    @staticmethod
    def __list_member_key(idx: int) -> str:
        """Return the internal list-member token (e.g. '>0')."""
        return f"{GridSearcher.LIST_KEY_SEPARATOR}{idx}"

    @staticmethod
    def __make_search_field(newKey: str, iterable) -> SearchField:
        """Create a SearchField from an encoded key and an iterable of values."""
        return SearchField(newKey, iterable)

    @staticmethod
    def __parse_mapping(key: str, value: Dict, baseConfig: Dict, searchFields: List, currentKey: str):
        """Handle a dict child: either a reserved-key SearchField or a nested mapping."""
        newKey = GridSearcher.__join_key(currentKey, key)
        if ReservedKeys.shouldBeParsed(value):
            iterable = ReservedKeys.parseDict(value)
            newSearchField = GridSearcher.__make_search_field(newKey, iterable)
            searchFields.append(newSearchField)
        else:
            baseConfig[key] = {}
            GridSearcher.__recursiveParse(
                value, baseConfig[key], searchFields, newKey)

    @staticmethod
    def __parse_list(key: str, value: List, baseConfig: Dict, searchFields: List, currentKey: str):
        """Handle a list child: recurse into each member and assemble the parsed list."""
        newKey = GridSearcher.__join_key(currentKey, key)
        listMembersDict = {}
        for idx, item in enumerate(value):
            itemKey = GridSearcher.__list_member_key(idx)
            GridSearcher.__recursiveParse(
                {itemKey: item}, listMembersDict, searchFields, newKey)
        parsedList = [''] * len(value)
        for k, v in listMembersDict.items():
            index = int(k[1:])
            parsedList[index] = v
        baseConfig[key] = parsedList

    @staticmethod
    def __recursiveParse(data: Dict, baseConfig: Dict, searchFields: List, currentKey: str = ''):
        """Recursively split `data` into `baseConfig` (fixed) and `searchFields` (varying).

        If a dict value is recognized by `ReservedKeys.shouldBeParsed`, it is
        parsed with `ReservedKeys.parseDict` to produce an iterable of values
        and converted into a `SearchField` whose encoded key is formed by
        joining `currentKey` and `key` with the class constant
        `DICT_KEY_SEPARATOR` ("|"). Otherwise the dict is treated as a nested
        fixed mapping and recursion continues.
        """
        for key, value in data.items():
            # Validate user key doesn't misuse reserved separators
            GridSearcher.__validate_user_key(key, currentKey)
            if isinstance(value, dict):
                GridSearcher.__parse_mapping(
                    key, value, baseConfig, searchFields, currentKey)
            elif isinstance(value, list):
                GridSearcher.__parse_list(
                    key, value, baseConfig, searchFields, currentKey)
            else:
                baseConfig[key] = value

    def __len__(self) -> int:
        return len(self.searchPolicy)

    def __repr__(self) -> str:
        return f"GridSearcher(searchPolicy={self.searchPolicy}, baseConfig={self.baseConfig})"

    @staticmethod
    def fromYAML(path: str):
        """Load a YAML file and construct a GridSearcher from its contents.

        Any IO or YAML parsing errors are propagated to the caller.
        """
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        return GridSearcher(config)

    @staticmethod
    def toYAML(config: dict, path: str = './'):
        """Write the provided config to a YAML file.

        Behavior:
        - If `path` is a directory (or ends with a path separator) the file
          `grid_config.yaml` will be created inside that directory.
        - If `path` is a file path, the config will be written to that file.
        - Parent directories are created when they don't exist.

        Args:
            config: Mapping to serialize as YAML.
            path: Destination file path or directory. Must be a non-empty string.
        """
        if not path:
            raise ValueError(
                "toYAML requires a non-empty filepath or directory path")

        dest = path
        # Treat explicit directory paths (existing or ending with separator)
        if os.path.isdir(path) or path.endswith(os.sep) or path.endswith('/') or path.endswith('\\'):
            os.makedirs(path, exist_ok=True)
            dest = os.path.join(path, 'grid_config.yaml')
        else:
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)

        # Use safe_dump and preserve key order where possible
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, sort_keys=False)
