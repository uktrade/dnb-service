import pytest

from freezegun import freeze_time
from requests_mock import ANY

from ..client import (
    _get_dnb_access_token,
    _renew_token,
    ACCESS_TOKEN_KEY,
    ACCESS_TOKEN_LOCK_KEY,
    DNBApiError,
    get_access_token,
    is_token_valid,
    redis_client as _redis_client,
    RENEW_ACCESS_TOKEN_MAX_ATTEMPTS,
    renew_dnb_token_if_close_to_expiring,
)


@pytest.fixture(scope='function')
def redis_client():
    try:
        yield _redis_client
    finally:
        _redis_client.flushall()


class TestGetAccessToken:
    def test_eventually_throws_exception(self, mocker):
        mock_is_token_valid = mocker.patch('dnb_api.client.is_token_valid', return_value=False)
        mock_renew_token = mocker.patch('dnb_api.client._renew_token', return_value=False)
        mocker.patch('dnb_api.client.time.sleep')

        with pytest.raises(DNBApiError):
            get_access_token()

        assert mock_renew_token.call_count == RENEW_ACCESS_TOKEN_MAX_ATTEMPTS
        assert mock_is_token_valid.call_count == RENEW_ACCESS_TOKEN_MAX_ATTEMPTS

    @freeze_time('2019-05-01 12:00:00')
    def test_success(self, redis_client, requests_mock):

        token_data = {
            ACCESS_TOKEN_KEY: 'an-access-token',
        }

        redis_client.set(ACCESS_TOKEN_KEY, 'an-access-token', ex=100)

        assert get_access_token() == token_data[ACCESS_TOKEN_KEY]


@freeze_time('2019-05-01 12:00:00')
class TestRenewToken:
    def test_is_locked(self, redis_client):
        redis_client.set(ACCESS_TOKEN_LOCK_KEY, 'locked')

        assert not _renew_token()

    def test_success(self, redis_client, mocker):
        fake_token = {
            'access_token': 'an-access-token',
            'expiresIn': 1000,
        }

        mocker.patch('dnb_api.client._get_dnb_access_token', return_value=fake_token)
        assert _renew_token()

        assert redis_client.get(ACCESS_TOKEN_KEY) == fake_token['access_token']
        assert redis_client.ttl(ACCESS_TOKEN_KEY) == 1000


@pytest.mark.parametrize('token, ttl, expected', [
    (
        None,
        None,
        False,
    ),
    (
        'test-key',
        1000,
        True,
    ),
])
@freeze_time('2019-05-01 12:00:00')
def test_is_token_valid(redis_client, token, ttl, expected):

    if token:
        redis_client.set(ACCESS_TOKEN_KEY, token, ex=ttl)

    assert is_token_valid() == expected


@pytest.mark.parametrize('ttl, expected', [
    (
        350,
        False,
    ),
    (
        100,
        True,
    ),
])
@freeze_time('2019-05-01 12:00:00')
def test_renew_dnb_token_if_close_to_expiring(settings, redis_client, mocker, ttl, expected):

    redis_client.set(ACCESS_TOKEN_KEY, 'a-key', ex=ttl)

    settings.DNB_API_RENEW_ACCESS_TOKEN_SECONDS_REMAINING = 300

    mock_renew_token = mocker.patch('dnb_api.client._renew_token')

    renew_dnb_token_if_close_to_expiring()

    assert mock_renew_token.called == expected


@freeze_time('2019-05-01 12:00:00')
class TestGetDnbAccessToken:

    def test_success(self, requests_mock):

        fake_token = {
            'access_token': 'an-access-token',
            'expiresIn': 86400,
        }

        requests_mock.post(ANY, status_code=200, json=fake_token)

        token = _get_dnb_access_token()

        assert token['access_token'] == fake_token['access_token']
        assert token['expiresIn'] == 86400

    def test_invalid_response(self, requests_mock):
        response_body = {
            'error': {
                'errorMessage': 'You are not currently authorised to access this product.',
                'errorCode': '00041'
            }
        }
        requests_mock.post(ANY, status_code=401, json=response_body)

        with pytest.raises(Exception):
            _get_dnb_access_token()
