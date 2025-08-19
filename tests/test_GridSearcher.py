from GridSearcher.GridSearcher import GridSearcher


def test_GridSearcher_parseConfig_tupleHandledAsFixed_expectedBehavior():
    sp, base = GridSearcher.parseConfig({'a': (1, 2), 'b': [3]})
    # Current implementation treats tuple as fixed (only list and range are considered iterables)
    assert 'a' in base
    assert base['a'] == (1, 2)
    # 'b' should be a search field inside the policy
    assert len(sp.searchFields) == 1
    assert sp.searchFields[0].name == 'b'


def test_GridSearcher_iteration_deepcopyReturnedConfigsAreIndependent_expectedBehavior():
    grid = {'A': [1, 2], 'fixed': {'nested': 0}}
    gs = GridSearcher(grid)
    it = iter(gs)
    first = next(it)
    # mutate returned dict deeply
    first['fixed']['nested'] = 999

    # get next config and ensure the change to the returned object did not affect subsequent outputs
    second = next(it)
    assert second['fixed']['nested'] == 0


def test_GridSearcher_fullCoverage_expectedAllCombinations():
    gs = GridSearcher({'x': [0, 1], 'y': ['L', 'R']})
    results = list(GridSearcher({'x': [0, 1], 'y': ['L', 'R']}))
    expected = [
        {'x': 0, 'y': 'L'},
        {'x': 1, 'y': 'L'},
        {'x': 0, 'y': 'R'},
        {'x': 1, 'y': 'R'},
    ]
    assert results == expected
