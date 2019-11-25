import io

import pytest

from company.constants import MonitoringStatusChoices
from company.models import Company, Country
from dnb_direct_plus.monitoring import add_companies_to_dnb_monitoring_registration, DNBApiError, process_exception_file


def _build_test_company(**fields):

    data = {
        'duns_number': '123456789',
        'is_out_of_business': False,
        'year_started': 2000,
        'address_country': Country.objects.first(),
        'monitoring_status': MonitoringStatusChoices.not_enabled.name
    }

    data.update(**fields)

    return Company.objects.create(**data)


class TestAddCompaniesToMonitoringRegistration:
    @pytest.mark.django_db
    def test_non_202_response_leaves_companies_in_pending_state(self, mocker):

        company = _build_test_company(monitoring_status=MonitoringStatusChoices.pending.name)

        mocked = mocker.patch('dnb_direct_plus.monitoring.api_request')
        mocked.return_value.json.return_value = {'error': 'an unknown error occured'}
        mocked.return_value.status_code = 500

        with pytest.raises(DNBApiError):
            add_companies_to_dnb_monitoring_registration()

        company.refresh_from_db()

        assert company.monitoring_status == MonitoringStatusChoices.pending.name

    @pytest.mark.django_db
    def test_company_status_set_to_submitted_on_success(self, mocker):
        company = _build_test_company(monitoring_status=MonitoringStatusChoices.pending.name)

        mocked = mocker.patch('dnb_direct_plus.monitoring.api_request')
        mocked.return_value.status_code = 202

        add_companies_to_dnb_monitoring_registration()

        company.refresh_from_db()

        assert company.monitoring_status == MonitoringStatusChoices.enabled.name


class TestProcessExceptionsFile:
    def test_invalid_header_raises_exception(self, mocker):

        header = io.BytesIO('INVALID\tHEADER\nanother line\netc\n'.encode('utf-8'))

        mocked = mocker.patch('dnb_direct_plus.monitoring.open_zip_file')
        mocked.return_value.__enter__.return_value = header
        mocked.return_value.__exit__.return_value = False

        with pytest.raises(ValueError):
            process_exception_file('dummy_file.zip')

    @pytest.mark.django_db
    def test_company_status_is_updated_to_failure(self, mocker):

        duns_number = '12345678'

        company = _build_test_company(duns_number=duns_number)

        header = io.BytesIO('DUNS\tCode\tInformation\n12345678\t110110\terror\n'.encode('utf-8'))

        mocked = mocker.patch('dnb_direct_plus.monitoring.open_zip_file')
        mocked.return_value.__enter__.return_value = header
        mocked.return_value.__exit__.return_value = False

        process_exception_file('dummy_file.zip')

        company.refresh_from_db()

        assert company.monitoring_status == MonitoringStatusChoices.failed.name
        assert company.monitoring_status_detail == '110110 error'
