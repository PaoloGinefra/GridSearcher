from GridSearcher.GridSearcher import GridSearcher


def test_GridSearcher_parseConfig_tupleHandledAsFixed_expectedBehavior():
    sp, base = GridSearcher.parseConfig({'run1': {'a': (1, 2), 'b': [3]}})
    # Current implementation treats tuple and plain lists as fixed values
    assert 'a' in base
    assert base['a'] == (1, 2)
    assert 'b' in base
    assert base['b'] == [3]
    # No SearchFields should be discovered from plain lists/tuples
    assert len(sp.searchFields) == 0


def test_GridSearcher_iteration_deepcopyReturnedConfigsAreIndependent_expectedBehavior():
    grid = {
        'run1': {'A': {'__list__': {'values': [1, 2]}}, 'fixed': {'nested': 0}}}
    gs = GridSearcher(grid)
    it = iter(gs)
    first = next(it)
    # mutate returned dict deeply
    first['fixed']['nested'] = 999

    # get next config and ensure the change to the returned object did not affect subsequent outputs
    second = next(it)
    assert second['fixed']['nested'] == 0


def test_GridSearcher_fullCoverage_expectedAllCombinations():
    gs = GridSearcher({'run1': {'x': {'__list__': {'values': [0, 1]}}, 'y': {
                      '__list__': {'values': ['L', 'R']}}}})
    results = list(gs)
    expected = [
        {'x': 0, 'y': 'L'},
        {'x': 1, 'y': 'L'},
        {'x': 0, 'y': 'R'},
        {'x': 1, 'y': 'R'},
    ]
    assert results == expected


def test_parseConfig_requires_single_top_level_key():
    # Passing an unwrapped dict must raise assertion per parseConfig contract
    try:
        GridSearcher.parseConfig({'a': 1, 'b': 2})
        raised = False
    except AssertionError:
        raised = True
    assert raised


def test_fromYAML_and_file_errors(tmp_path):
    # valid YAML
    p = tmp_path / "good.yaml"
    p.write_text("run1:\n  a: 1\n")
    gs = GridSearcher.fromYAML(str(p))
    assert isinstance(gs, GridSearcher)

    # missing file -> FileNotFoundError
    try:
        GridSearcher.fromYAML(str(tmp_path / "nope.yaml"))
        raised = False
    except FileNotFoundError:
        raised = True
    assert raised


def test_nested_key_application():
    gs = GridSearcher(
        {'run1': {'model': {'layers': {'__list__': {'values': [2, 4]}}}}})
    results = list(gs)
    assert results == [{'model': {'layers': 2}}, {'model': {'layers': 4}}]


def test_path_collision_non_dict_intermediate_raises():
    # base has a non-dict at 'a' but a search field tries to set 'a|b' -> TypeError
    config = {'run1': {'a': 1, 'a': {'__list__': {'values': [1]}}}}
    # The above is ambiguous to write; construct via parseConfig components
    sp, base = GridSearcher.parseConfig({'run1': {'a': 1}})
    # Manually craft a searchPolicy that will attempt to set 'a|b'
    from GridSearcher.SearchField import SearchField
    sf = SearchField('a|b', [1])
    from GridSearcher.ProductSearchPolicy import ProductSearchPolicy
    policy = ProductSearchPolicy([sf])
    gs = GridSearcher({'run1': {'a': 1}})
    # inject the policy and baseConfig to simulate collision
    gs.searchPolicy = policy
    gs.baseConfig = {'a': 1}
    gs.currentConfig = {'a': 1}
    try:
        next(gs)
        raised = False
    except TypeError:
        raised = True
    assert raised


def test_no_search_fields_returns_base_once():
    # grid with only fixed values should yield a single base config
    gs = GridSearcher({'run1': {'fixed': 1}})
    results = list(gs)
    assert results == [{'fixed': 1}]
