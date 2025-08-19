from typing import Dict, Tuple, Any
from .SearchField import SearchField
from .SearchPolicy import SearchPolicy
from .ProductSearchPolicy import ProductSearchPolicy
from copy import deepcopy


class GridSearcher:
    """ With this class you can perform a grid search over a set of parameters.
    It requires a grid configuration dictionary of the form:
    ```python
    {
        'param1': [value1, value2, ...],
        'param2': [value1, value2, ...],
        ...
        'fixed_param1': fixed_value1,
        'fixed_param2': fixed_value2,
        ...
    }
    ```
    You can also include fixed parameters that will not be changed during the search.
    """

    def __init__(self, gridConfig: Dict):
        """The constructor for the GridSearcher class. It parses the given grid configuration and prepares the search policy and base configuration.

        ## Args:
            **gridConfig** (Dict): The configuration for the grid search of the form:
            ```python
            {
                'param1': [value1, value2, ...],
                'param2': [value1, value2, ...],
                ...
                'fixed_param1': fixed_value1,
                'fixed_param2': fixed_value2,
                ...
            }
            ```
            You can also include fixed parameters that will not be changed during the search.
        """
        self.gridConfig = gridConfig
        self.searchPolicy, self.baseConfig = self.parseConfig(gridConfig)
        self.currentConfig = deepcopy(self.baseConfig)

    def __iter__(self):
        return self

    def __next__(self) -> Dict[str, Any]:
        """Generates the next configuration

        Returns:
            Dict[str, Any]: The next configuration.
        """
        try:
            update = next(self.searchPolicy)
            for key, value in update.items():
                self.currentConfig[key] = value
            return deepcopy(self.currentConfig)
        except StopIteration:
            raise StopIteration

    @staticmethod
    def parseConfig(gridConfig: Dict) -> Tuple[SearchPolicy, Dict]:
        """Given a grid configuration dictionary, this method parses it and returns a search policy and a base configuration containing all the fixed parameters.

        Args:
            gridConfig (Dict): The configuration for the grid search.

        Returns:
            Tuple[SearchPolicy, Dict]: The search policy and the base configuration.
        """
        searchFields = []
        baseConfig = {}
        for fieldName, fieldValues in gridConfig.items():
            if type(fieldValues) is not list and type(fieldValues) is not range:
                baseConfig[fieldName] = fieldValues
                continue

            searchFields.append(SearchField(fieldName, iter(fieldValues)))
        searchPolicy = ProductSearchPolicy(searchFields)
        return searchPolicy, baseConfig

    def __len__(self) -> int:
        return len(self.searchPolicy)

    def __repr__(self) -> str:
        return f"GridSearcher(searchPolicy={self.searchPolicy}, baseConfig={self.baseConfig})"
