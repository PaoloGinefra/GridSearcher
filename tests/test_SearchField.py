import pytest

from GridSearcher.SearchField import SearchField


def test_SearchField_iterationResetAndLen_expectedValues():
    sf = SearchField("f", [1, 2, 3])
    assert list(sf) == [1, 2, 3]
    sf.reset()
    assert list(sf) == [1, 2, 3]
    assert len(sf) == 3


def test_SearchField_emptyIterable_raisesStopIterationAndLenZero():
    sf = SearchField("empty", [])
    assert len(sf) == 0
    with pytest.raises(StopIteration):
        next(sf)


def test_SearchField_generatorIsSnapshot_expectedValues():
    gen = (i for i in range(3))
    sf = SearchField("g", gen)
    assert list(sf) == [0, 1, 2]

    # if generator already partially consumed before passing, snapshot starts from remaining items
    gen2 = (i for i in range(4))
    next(gen2)  # consume first element (0)
    sf2 = SearchField("h", gen2)
    assert list(sf2) == [1, 2, 3]


def test_SearchField_nonIterable_raisesTypeError():
    with pytest.raises(TypeError):
        SearchField("bad", 5)  # type: ignore
