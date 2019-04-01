import pytest

from dnb.ingest import dnb_indicator_to_bool, to_bool, to_int, ValidationError


def test_to_int_required():
    with pytest.raises(ValidationError):
        to_int(0, required=True)([''])


def test_to_int_not_required():
    try:
        to_int(0, required=False)([''])
    except ValidationError:
        pytest.fail('Should not raise an exception')


def test_to_int_integer():
    assert to_int(0)(['1234']) == 1234


@pytest.mark.parametrize('test_input,expected', [
    ('Y', True),
    ('N', False),
    ('X', None),
])
def test_to_bool_true_value(test_input, expected):
    assert to_bool(0, 'Y', 'N')([test_input]) == expected


@pytest.mark.parametrize('test_input,expected', [
    ('0', True),
    ('1', True),
    ('2', False),
    ('3', False),
])
def test_dnb_indicator_to_bool(test_input, expected):
    assert dnb_indicator_to_bool(0)([test_input]) == expected
