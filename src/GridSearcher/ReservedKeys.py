"""Helpers to detect and parse special "reserved-key" descriptors used in
grid configuration files.

This module supports small, explicit descriptor shapes (currently a
range and a list) that appear in place of parameter values. For example:

    {'lr': {'__range__': {'from': 1, 'to': 10, 'step': 2}}}
    {'batch': {'__list__': {'values': [16, 32, 64]}}}

The public API is the `ReservedKeys` enum which provides `shouldBeParsed`
(predicate) and `parseDict` (extract iterable of concrete values).
"""

from enum import Enum
from typing import Callable, Dict, Iterable


def parseRange(data: Dict) -> Iterable:
    """Parse a range descriptor into an iterable (Python range).

    Expected keys:
        - 'from' (inclusive start)
        - 'to' (exclusive end)
        - optional 'step'

    Raises AssertionError for malformed input.
    """
    if not (2 <= len(data) <= 3):
        raise ValueError(
            f"Range must have 2 or 3 keys, got: {list(data.keys())}")
    if not all(k in data for k in ['from', 'to']):
        raise ValueError(
            f"Range must have 'from' and 'to' keys, got: {list(data.keys())}")
    if data['from'] >= data['to']:
        raise ValueError(
            f"'from' must be less than 'to', got: from={data['from']}, to={data['to']}")
    try:
        if 'step' in data:
            return range(data['from'], data['to'], data['step'])
        return range(data['from'], data['to'])
    except TypeError as e:
        raise TypeError(f"Invalid type for range boundaries/step: {e}") from e


def parseList(data: Dict) -> Iterable:
    """Parse a list descriptor and return the contained list.

    Expected shape: {'values': [...]}
    Raises AssertionError if 'values' is missing or not a list.
    """
    if 'values' not in data:
        raise ValueError(
            f"List must have 'values' key, got: {list(data.keys())}")
    if not isinstance(data['values'], list):
        raise TypeError(
            f"'values' must be a list, got: {type(data['values'])}")
    return data['values']


class ReservedKeys(Enum):
    """Enum mapping reserved keyword names to parser callables.

    Members hold a tuple of (key_name, parser_callable). Use
    `ReservedKeys.shouldBeParsed(data)` to test whether a dict value is a
    reserved-key descriptor, and `ReservedKeys.parseDict(data)` to obtain the
    iterable of concrete values.
    """

    def __init__(self, key: str, parser: Callable[[Dict], Iterable]) -> None:
        self.key = key
        self.parser = parser

    @staticmethod
    def parseDict(data: Dict) -> Iterable:
        """Return the iterable described by a reserved-key descriptor.

        Scans the enum members for the reserved key present in `data` and
        dispatches to the corresponding parser. Raises ValueError if no
        known reserved key is found.
        """
        for reservedKey in ReservedKeys:
            if reservedKey.key in data:
                return reservedKey.parser(data[reservedKey.key])
        raise ValueError("Invalid reserved key")

    @staticmethod
    def shouldBeParsed(data: Dict) -> bool:
        """Return True if `data` is exactly one reserved-key descriptor.

        Contract:
            - `data` must be a dict with exactly one key.
            - that single key must equal one of the enum member keys.
        """
        # The data should have only one key
        if len(data) != 1:
            return False

        # The key must be one of the reserved keys
        key = next(iter(data))
        return any(key == member.key for member in ReservedKeys)

    # Enum members map reserved-key strings to parser functions
    RANGE = '__range__', parseRange
    LIST = '__list__', parseList
