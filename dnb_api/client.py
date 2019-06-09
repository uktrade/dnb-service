import datetime
import logging
import time

from contextlib import contextmanager

import redis
import requests

from django.conf import settings


DNB_AUTH_ENDPOINT = 'https://plus.dnb.com/v2/token'

ACCESS_TOKEN_KEY = '_access_token'
ACCESS_TOKEN_EXPIRES_KEY = '_access_token_expires'
ACCESS_TOKEN_LOCK_KEY = '_access_token_write_lock'
ACCESS_TOKEN_LOCK_EXPIRY_SECONDS = 5
ACCESS_TOKEN_EXPIRES_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
RENEW_ACCESS_TOKEN_MAX_ATTEMPTS = 5
RENEW_ACCESS_TOKEN_RETRY_DELAY_SECONDS = 1

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


class DNBApiError(Exception):
    pass


def get_access_token():
    """Return an access token"""

    for i in range(RENEW_ACCESS_TOKEN_MAX_ATTEMPTS):
        if is_token_valid():
            break

        if _renew_token():
            break

        time.sleep(RENEW_ACCESS_TOKEN_RETRY_DELAY_SECONDS)
    else:
        raise DNBApiError('Failed to retrieve an access token')

    return redis_client.get(ACCESS_TOKEN_KEY)


def is_token_valid():
    """Check if there is a valid access token"""

    if not redis_client.exists(ACCESS_TOKEN_KEY):
        return False

    expires_time = datetime.datetime.strptime(
        redis_client.get(ACCESS_TOKEN_EXPIRES_KEY),
        ACCESS_TOKEN_EXPIRES_DATETIME_FORMAT
    )

    return expires_time > datetime.datetime.utcnow()


def renew_dnb_token_if_close_to_expiring():
    """Renew the DNB access token if there is less than `settings.DNB_API_RENEW_ACCESS_TOKEN_MINUTES_REMAINING`
    remaining"""

    expires = datetime.datetime.strptime(
        redis_client.get(ACCESS_TOKEN_EXPIRES_KEY),
        ACCESS_TOKEN_EXPIRES_DATETIME_FORMAT
    )

    time_near_expiry = expires - datetime.timedelta(
        minutes=settings.DNB_API_RENEW_ACCESS_TOKEN_MINUTES_REMAINING)

    if datetime.datetime.utcnow() > time_near_expiry:
        logger.debug('token is due to expire; attempting to renew')
        _renew_token()


def _get_dnb_access_token():
    """Get a new Direct+ access token."""

    response = requests.post(
        DNB_AUTH_ENDPOINT,
        auth=(settings.DNB_API_USERNAME, settings.DNB_API_PASSWORD),
        headers={
            'Content-Type': 'application/json',
        },
        json={'grant_type': 'client_credentials'},
    )

    response_body = response.json()

    if response.status_code != 200:
        logger.error('Unauthorised response from DNB API: %s', response_body)

        raise DNBApiError(
            f'Unable to get access token: {response_body["error"]["errorMessages"]}; '
            f'error code: {response_body["error"]["errorCode"]}'
        )

    expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=response_body['expiresIn'])

    return {
        'access_token': response_body['access_token'],
        'expires': expires,
    }


def _renew_token():
    """ Attempt to renew the access token.

    :returns: boolean indicating whether the operation was successful

    NOTE: this function won't retry if it is unable to acquire a lock.
    Retrying is done upstream in `get_access_token`."""

    @contextmanager
    def _acquire_lock():
        locked = redis_client.set(
            ACCESS_TOKEN_LOCK_KEY, 'locked', ex=ACCESS_TOKEN_LOCK_EXPIRY_SECONDS, nx=True) is not None
        try:
            yield locked
        finally:
            if locked:
                redis_client.delete(ACCESS_TOKEN_LOCK_KEY)

    logger.debug('attempting to renew token')

    with _acquire_lock() as locked:
        if locked:
            try:
                token = _get_dnb_access_token()
                redis_client.set(ACCESS_TOKEN_KEY, token['access_token'])
                redis_client.set(ACCESS_TOKEN_EXPIRES_KEY, token['expires'].strftime(
                    ACCESS_TOKEN_EXPIRES_DATETIME_FORMAT))

                return True
            except DNBApiError:
                logger.exception()
        else:
            logger.debug('renew token failed - cannot acquire lock')

    return False
