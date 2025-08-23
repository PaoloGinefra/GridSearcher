import pytest
from GridSearcher.GridSearcher import GridSearcher


def test_list_with_range_and_nested_list_product(tmp_path):
    # category[0] is a range -> 1,2  ; category[2].var is a list -> 2 values
    grid = {
        'run': {
            'category': [
                {'__range__': {'from': 1, 'to': 3}},
                'books',
                {
                    'other': 'stuff',
                    'var': {'__list__': {'values': ['clothing', 'accessories']}}
                }
            ]
        }
    }

    gs = GridSearcher(grid, loggingPath=str(tmp_path))
    configs = list(gs)

    # Cartesian product: 2 (range) * 2 (list) = 4
    assert len(configs) == 4

    seen = set()
    for c in configs:
        # fixed element preserved
        assert c['category'][1] == 'books'
        assert c['category'][2]['other'] == 'stuff'
        seen.add((c['category'][0], c['category'][2]['var']))

    assert seen == {(1, 'clothing'), (1, 'accessories'),
                    (2, 'clothing'), (2, 'accessories')}


def test_single_list_item_with_multiple_nested_iterators(tmp_path):
    # single list element is a dict with two reserved descriptors -> product within that element
    grid = {
        'run': {
            'items': [
                {
                    'a': {'__range__': {'from': 1, 'to': 3}},
                    'b': {'__list__': {'values': ['x', 'y']}}
                }
            ]
        }
    }

    gs = GridSearcher(grid, loggingPath=str(tmp_path))
    configs = list(gs)

    # 2 * 2 = 4 combinations
    assert len(configs) == 4
    expected = {(1, 'x'), (1, 'y'), (2, 'x'), (2, 'y')}
    got = {(c['items'][0]['a'], c['items'][0]['b']) for c in configs}
    assert got == expected


def test_multiple_list_positions_with_iterators(tmp_path):
    # two separate list members are iterators -> product across positions
    grid = {
        'run': {
            'pair': [
                {'__range__': {'from': 0, 'to': 2}},
                {'__list__': {'values': ['L', 'R']}}
            ]
        }
    }

    gs = GridSearcher(grid, loggingPath=str(tmp_path))
    configs = list(gs)
    # 2 * 2 = 4
    assert len(configs) == 4
    got = {(c['pair'][0], c['pair'][1]) for c in configs}
    assert got == {(0, 'L'), (0, 'R'), (1, 'L'), (1, 'R')}


def test_order_and_fixed_elements_preserved(tmp_path):
    # ensure fixed elements keep position and nested dict keys preserved
    grid = {
        'run': {
            'mixed': [
                'fixed0',
                {'__list__': {'values': ['a', 'b']}},
                {'meta': {'inner': {'__range__': {'from': 5, 'to': 7}}}}
            ]
        }
    }

    gs = GridSearcher(grid, loggingPath=str(tmp_path))
    configs = list(gs)

    # product: 2 (middle) * 2 (inner range 5,6) = 4
    assert len(configs) == 4
    for c in configs:
        assert c['mixed'][0] == 'fixed0'
        assert c['mixed'][2]['meta']['inner'] in (5, 6)
