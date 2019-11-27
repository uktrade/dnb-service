import io

import pytest

from company.constants import MonitoringStatusChoices
from company.tests.factories import CompanyFactory
from dnb_direct_plus.monitoring import add_companies_to_dnb_monitoring_registration, DNBApiError, process_exception_file


class TestAddCompaniesToMonitoringRegistration:
    @pytest.mark.django_db
    def test_non_202_response_leaves_companies_in_pending_state(self, mocker):

        company = CompanyFactory(monitoring_status=MonitoringStatusChoices.pending.name)

        mocked = mocker.patch('dnb_direct_plus.monitoring.api_request')
        mocked.return_value.json.return_value = {'error': 'an unknown error occured'}
        mocked.return_value.status_code = 500

        with pytest.raises(DNBApiError):
            add_companies_to_dnb_monitoring_registration()

        company.refresh_from_db()

        assert company.monitoring_status == MonitoringStatusChoices.pending.name

    @pytest.mark.django_db
    def test_company_status_set_to_submitted_on_success(self, mocker):
        company = CompanyFactory(monitoring_status=MonitoringStatusChoices.pending.name)

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

        with pytest.raises(ValueError) as ex:
            process_exception_file('dummy_file.zip')

        assert str(ex.value) == \
               'Expected header to be: [\'DUNS\', \'Code\', \'Information\'] ' \
               'but got: [\'INVALID\', \'HEADER\'] in dummy_file.zip'

    @pytest.mark.django_db
    def test_company_status_is_updated_to_failure(self, mocker):

        company = CompanyFactory(duns_number='12345678')
        company2 = CompanyFactory(duns_number='87654321')

        header = io.BytesIO(
            'DUNS\tCode\tInformation\n12345678\t110110\terror\n87654321\terror\tfailed\n'.encode('utf-8'))

        mocked = mocker.patch('dnb_direct_plus.monitoring.open_zip_file')
        mocked.return_value.__enter__.return_value = header
        mocked.return_value.__exit__.return_value = False

        process_exception_file('dummy_file.zip')

        company.refresh_from_db()
        company2.refresh_from_db()

        assert company.monitoring_status == MonitoringStatusChoices.failed.name
        assert company.monitoring_status_detail == '110110 error'
        assert company2.monitoring_status == MonitoringStatusChoices.failed.name
        assert company2.monitoring_status_detail == 'error failed'
