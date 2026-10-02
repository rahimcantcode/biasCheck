import pytest
from backend.json_contract import strict_json_loads

@pytest.mark.parametrize('text',['{"label":0,"label":1}','{"x":{"text":"a","text":"b"}}','{"x":NaN}','{"x":Infinity}','{"x":-Infinity}'])
def test_ambiguous_json_rejected(text):
    with pytest.raises(ValueError):strict_json_loads(text)

def test_valid_nested_json_preserved():
    assert strict_json_loads('{"spans":[],"reason":"NaN is a word here"}')=={'spans':[],'reason':'NaN is a word here'}
