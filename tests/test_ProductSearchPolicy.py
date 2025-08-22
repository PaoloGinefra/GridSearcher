from GridSearcher.GridSearcher import GridSearcher


def test_ProductSearchPolicy_len_expectedProduct():
    gs = GridSearcher({'run1': {'A': {'__list__': {'values': [1, 2]}}, 'B': {
                      '__list__': {'values': ['a', 'b']}}}})
    assert len(gs.searchPolicy) == 4
    assert len(gs) == 4


def test_ProductSearchPolicy_sequence_expectedOrder():
    gs = GridSearcher({'run1': {'A': {'__list__': {'values': [1, 2]}}, 'B': {
                      '__list__': {'values': ['a', 'b']}}}})
    results = list(gs)
    expected = [
        {'A': 1, 'B': 'a'},
        {'A': 2, 'B': 'a'},
        {'A': 1, 'B': 'b'},
        {'A': 2, 'B': 'b'},
    ]
    assert results == expected


def test_ProductSearchPolicy_emptyField_expectedStopIterationAndLenZero():
    gs = GridSearcher(
        {'run1': {'A': {'__list__': {'values': []}}, 'B': {'__list__': {'values': [1]}}}})
    assert len(gs) == 0
    assert list(gs) == []
