import logging

from django.contrib.auth import get_user_model

from dnb_direct_plus.client import redis_client

logger = logging.getLogger(__name__)


def database_check():
    name = 'Database'
    status = True

    try:
        get_user_model().objects.count()
    except:  # noqa: E722
        logger.exception('Database unavailable')
        status = False

    return name, status


def redis_check():
    name = 'Redis'
    status = True

    try:
        redis_client.ping()
    except:  # noqa: E722
        logger.exception('Redis unavailable')
        status = False

    return name, status
