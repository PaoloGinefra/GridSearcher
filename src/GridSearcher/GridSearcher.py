from typing import Dict, Tuple, Any
from .SearchField import SearchField
from .SearchPolicy import SearchPolicy
from .ProductSearchPolicy import ProductSearchPolicy
from .ReservedKeys import ReservedKeys
from copy import deepcopy
import yaml
from typing import List
from .Logger import Logger


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
                'model': {'layers': {'__list__': {'values': ['MLP', 'CNN]}}}
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
        encoded keys (joined by `KEY_SEPARATOR`) to values. This method splits
        those keys, applies updates to the mutable `currentConfig`, and
        returns a deepcopy snapshot so callers receive an independent copy.
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
    def __setFromKey(keyList: List[str], target: Dict | List, value: Any):
        """Recursive helper to set a value into a nested dict by key path.

        Creates intermediate dicts when missing. If an intermediate path exists
        but is not a dict, a TypeError may occur when indexing into it.
        """
        # Handle list targets safely: ensure the list is large enough,
        # create a dict for the element if necessary, and recurse into it.
        if isinstance(target, list):
            # Expect a list-key like '>0'
            index = int(keyList[0][1:])
            # Extend list if index out of range
            if index >= len(target):
                target.extend([None] * (index - len(target) + 1))

            # If this is the final key for the list element, assign directly
            if len(keyList) == 1:
                target[index] = value
                return

            # Ensure the list element is a dict we can recurse into
            if target[index] is None or not isinstance(target[index], (dict, list)):
                # when next key is a list-key we need a list, else a dict
                next_key = keyList[1]
                if next_key and next_key[0] == GridSearcher.LIST_KEY_SEPARATOR:
                    target[index] = []
                else:
                    target[index] = {}

            # Recurse into the element
            GridSearcher.__setFromKey(keyList[1:], target[index], value)
            return
        elif len(keyList) == 1:
            target[keyList[0]] = value
        else:
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
        assert len(gridConfig) == 1, (
            f"Grid configuration must contain exactly one key with the run name, got {list(gridConfig.keys())}"
        )

        # Extract the run-level mapping
        configName = list(gridConfig.keys())[0]
        gridConfig = gridConfig[configName]

        searchFields: List[SearchField] = []
        baseConfig: Dict = {}

        # Populate searchFields and baseConfig by walking the nested dict
        GridSearcher.__recursiveParse(gridConfig, baseConfig, searchFields)

        print(searchFields)

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
    def __recursiveParse(data: Dict, baseConfig: Dict, searchFields: List, currentKey: str = ''):
        """Recursively split `data` into `baseConfig` (fixed) and `searchFields` (varying).

        If a dict value is recognized by `ReservedKeys.shouldBeParsed`, it is
        parsed with `ReservedKeys.parseDict` to produce an iterable of values
        and converted into a `SearchField` whose key is `currentKey` +
        `KEY_SEPARATOR` + `key` (when nested). Otherwise the dict is treated
        as a nested fixed mapping and recursion continues.
        """
        for key, value in data.items():
            # Validate user key doesn't misuse reserved separators
            GridSearcher.__validate_user_key(key, currentKey)
            if isinstance(value, dict):
                newKey = currentKey + GridSearcher.DICT_KEY_SEPARATOR if currentKey else ''
                newKey += key

                if ReservedKeys.shouldBeParsed(value):
                    iterable = ReservedKeys.parseDict(value)
                    newSearchField = SearchField(newKey, iterable)
                    searchFields.append(newSearchField)
                else:
                    baseConfig[key] = {}
                    GridSearcher.__recursiveParse(
                        value, baseConfig[key], searchFields, newKey)
            elif isinstance(value, list):
                newKey = currentKey + \
                    GridSearcher.DICT_KEY_SEPARATOR if currentKey else ''
                newKey += key
                listMembersDict = {}
                for idx, item in enumerate(value):
                    itemKey = f"{GridSearcher.LIST_KEY_SEPARATOR}{idx}"
                    GridSearcher.__recursiveParse(
                        {itemKey: item}, listMembersDict, searchFields, newKey)
                parsedList = [''] * len(value)
                for k, v in listMembersDict.items():
                    index = int(k[1:])
                    parsedList[index] = v
                baseConfig[key] = parsedList
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
        # Write the provided config to the given filepath.
        if not path:
            raise ValueError("toYAML requires a filepath to write to")
        with open(path, 'w') as f:
            yaml.dump(config, f)
