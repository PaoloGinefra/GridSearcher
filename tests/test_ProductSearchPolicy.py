from GridSearcher.GridSearcher import GridSearcher


def test_ProductSearchPolicy_len_expectedProduct():
    gs = GridSearcher({'A': [1, 2], 'B': ['a', 'b']})
    assert len(gs.searchPolicy) == 4
    assert len(gs) == 4


def test_ProductSearchPolicy_sequence_expectedOrder():
    gs = GridSearcher({'A': [1, 2], 'B': ['a', 'b']})
    results = list(gs)
    expected = [
        {'A': 1, 'B': 'a'},
        {'A': 2, 'B': 'a'},
        {'A': 1, 'B': 'b'},
        {'A': 2, 'B': 'b'},
    ]
    assert results == expected


def test_ProductSearchPolicy_emptyField_expectedStopIterationAndLenZero():
    gs = GridSearcher({'A': [], 'B': [1]})
    assert len(gs) == 0
    assert list(gs) == []
