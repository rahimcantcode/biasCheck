from backend.nli_model import assess

def scores(**kwargs):
    return dict(politics=1., policy=1., LEFT=.01, CENTER=.01, RIGHT=.01, **{}) | kwargs

def test_nonpolitical_is_not_center():
    assert assess(scores(politics=.01, policy=.01, CENTER=.99), 30) == ('nonpolitical', None)

def test_short_input_withholds_even_strong_prediction():
    assert assess(scores(LEFT=.99), 1) == ('insufficient_context', None)

def test_conflicting_support_abstains():
    assert assess(scores(LEFT=.99, RIGHT=.98), 30) == ('uncertain', None)

def test_clear_support_is_only_tentative():
    assert assess(scores(RIGHT=.99), 30) == ('tentative', 'RIGHT')


def test_mixed_guard_prevents_one_sided_tentative_result():
    assert assess(scores(RIGHT=.99, mixed=.95), 30) == ('mixed_or_conflicting', None)

def test_mixed_guard_does_not_override_nonpolitical_or_short_text():
    assert assess(scores(politics=.01, policy=.01, mixed=.99), 30) == ('nonpolitical', None)
    assert assess(scores(RIGHT=.99, mixed=.99), 2) == ('insufficient_context', None)
