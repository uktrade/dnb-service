import os

import pytest
from django.core.management import call_command


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'company/fixtures/countries.yaml')


@pytest.fixture(scope='module')
def cmpelk_api_response_json():
    with open(os.path.join(os.path.dirname(__file__), 'dnb_direct_plus/tests/api_data/cmpelk_test_response.json')) as f:
        return f.read()


@pytest.fixture(scope='module')
def company_list_api_response_json():
    with open(os.path.join(os.path.dirname(__file__), 'dnb_direct_plus/tests/api_data/company_list_test_response.json')) as f:
        return f.read()
