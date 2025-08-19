from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .SearchField import SearchField


class SearchPolicy(ABC):
    """This is an abstract class for defining search policies.
    A search policy determines how to explore the search space defined by the search fields.

    A search policy is an Iterator that yields a dictionary of updates to be performed to the current configuration.
    """

    def __init__(self, searchFields: List[SearchField]):
        """Initialize the SearchPolicy with the given search fields.

        Args:
            searchFields (List[SearchField]): The search fields to be used in the policy.
        """
        self.searchFields = searchFields

    def __iter__(self):
        return self

    @abstractmethod
    def __next__(self) -> Dict[str, Any]:
        """Get the next configuration to be evaluated.

        Returns:
            Dict[str, Any]: The next configuration.
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    def __repr__(self) -> str:
        return f"SearchPolicy(searchFields={self.searchFields})"
