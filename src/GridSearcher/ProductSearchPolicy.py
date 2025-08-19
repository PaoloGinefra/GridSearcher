from typing import Any, List, Dict
from GridSearcher.SearchField import SearchField
from .SearchPolicy import SearchPolicy
import math


class ProductSearchPolicy(SearchPolicy):
    """A search policy that explores the product search space. Meaning that it will try all combinations of the search fields.

    This is an Iterator that yields a dictionary of updates to be performed to the current configuration.
    """

    def __init__(self, searchFields: List[SearchField]):
        """Initialize the ProductSearchPolicy with the given search fields.

        Args:
            searchFields (List[SearchField]): The search fields to be used in the policy.
        """
        super().__init__(searchFields)

        # Flag to indicate if this is the first iteration, used to produce the first global update
        self.FirstTime = True

    def __next__(self) -> Dict[str, Any]:
        if self.FirstTime:
            # Produce the first global update by obtaining the first value from each search field
            self.FirstTime = False
            updates = {}
            for searchField in self.searchFields:
                updates[searchField.name] = next(searchField)
            return updates

        # Produce the next update, it will keep iterating until a search field that can produce a new value is found
        updates = {}
        for searchField in self.searchFields:
            try:
                # If a search field can produce a new value, update the dictionary and return it
                updates[searchField.name] = next(searchField)
                return updates
            except StopIteration:
                # If a search field is exhausted, reset it, get the first value and continue
                searchField.reset()
                updates[searchField.name] = next(searchField)
                continue
        raise StopIteration

    def __len__(self) -> int:
        """Computes the length of the search space.

        Returns:
            int: The total number of configurations in the search space.
        """
        lengths = [len(searchField) for searchField in self.searchFields]
        return math.prod(lengths)
