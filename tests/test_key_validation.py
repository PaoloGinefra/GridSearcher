from GridSearcher.GridSearcher import GridSearcher
import pytest


def test_parseConfig_rejects_pipe_in_user_key():
    # user key contains '|' which is reserved
    bad = {'run1': {'a|b': 1}}
    with pytest.raises(ValueError) as exc:
        GridSearcher.parseConfig(bad)
    assert "contains reserved separator '|'" in str(exc.value)


def test_parseConfig_rejects_bad_gt_in_user_key():
    # user key contains '>' but not as internal token '>N'
    bad = {'run1': {'weird>key': 1}}
    with pytest.raises(ValueError) as exc:
        GridSearcher.parseConfig(bad)
    assert "contains reserved separator '>'" in str(exc.value)
