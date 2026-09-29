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
