from typing import Iterable


class SearchField:
    """
    A reusable search field that iterates over a fixed set of values.
    """

    def __init__(self, name: str, values: Iterable):
        """The constructor for the SearchField class.

        Args:
            name (str): The name of the search field.
            values (Iterable): The values to be used in the search field.
        """
        self.name = name
        self.initialValues = list(values)
        self.reset()

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.valuesIterable)

    def reset(self):
        """Resets the state of the search field to the initial configuration
        """
        self.valuesIterable = iter(self.initialValues)

    def __repr__(self):
        return f"SearchField(name={self.name}, values={list(self.initialValues)})"

    def __len__(self) -> int:
        """Compute the length of the search field.

        Returns:
            int: The number of values in the search field.
        """
        return len(self.initialValues)
