import pytest

from health_check.checks import database_check, redis_check


@pytest.mark.django_db
def test_database_check():
    assert database_check() == ('Database', True)


def test_database_check_fail(mocker):
    mocker.patch('health_check.checks.get_user_model', side_effect=Exception('Error!'))

    assert database_check() == ('Database', False)


def test_redis_check():
    assert redis_check() == ('Redis', True)


def test_redis_check_fail(mocker):
    mocker.patch('health_check.checks.redis_client.ping', side_effect=Exception('Error!'))

    assert redis_check() == ('Redis', False)
