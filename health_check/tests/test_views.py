import pytest

from xml.etree import ElementTree as ET

from django.urls import reverse

pytestmark = [pytest.mark.django_db]


@pytest.mark.parametrize('viewname', ['healthcheck:p1', 'pingdom'])
def test_p1_healthcheck(client, viewname):

    response = client.get(reverse(viewname))

    xml_doc = ET.fromstring(response.content)
    status = xml_doc.find('.//status').text

    assert response.status_code == 200
    assert status == 'OK'


@pytest.mark.parametrize('viewname', ['healthcheck:p1', 'pingdom'])
def test_p1_healthcheck_error(client, mocker, viewname):

    mocker.patch('health_check.checks.get_user_model', side_effect=Exception('fatal'))

    response = client.get(reverse(viewname))

    xml_doc = ET.fromstring(response.content)
    status = xml_doc.find('.//status').text

    assert response.status_code == 200
    assert status == 'Database: False\nRedis: True'

