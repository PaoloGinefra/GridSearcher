from GridSearcher.ReservedKeys import ReservedKeys, parseRange, parseList


def test_parseRange_basic():
    it = parseRange({'from': 0, 'to': 3})
    assert list(it) == [0, 1, 2]


def test_parseRange_with_step():
    it = parseRange({'from': 0, 'to': 5, 'step': 2})
    assert list(it) == [0, 2, 4]


def test_parseList_basic():
    it = parseList({'values': [10, 20]})
    assert it == [10, 20]


def test_shouldBeParsed_and_parseDict():
    d = {'__range__': {'from': 0, 'to': 2}}
    assert ReservedKeys.shouldBeParsed(d)
    vals = ReservedKeys.parseDict(d)
    assert list(vals) == [0, 1]

    bad = {'__unknown__': {}}
    assert not ReservedKeys.shouldBeParsed(bad)
    try:
        ReservedKeys.parseDict(bad)
        raised = False
    except ValueError:
        raised = True
    assert raised
