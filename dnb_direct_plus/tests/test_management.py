from io import StringIO
import json

import pytest
from django.conf import settings
from django.core.management import call_command

from company.tests.factories import CompanyFactory
from ..models import MonitoringFileRecord


pytestmark = pytest.mark.django_db


class TestProcessMonitoringData:
    @pytest.mark.parametrize('file_name', [
        'invalid-file-name.txt',
        f'{settings.DNB_MONITORING_REGISTRATION_REFERENCE}_20191025205213_NOTIFICATION_HEADER.json',
        f'{settings.DNB_ARCHIVE_PATH}/{settings.DNB_MONITORING_REGISTRATION_REFERENCE}_20191025205213_NOTIFICATION_1.zip',
        f'{settings.DNB_ARCHIVE_PATH}/{settings.DNB_MONITORING_REGISTRATION_REFERENCE}_20191025205213_UNEXPECTED_1.zip',
    ])
    def test_skipped_files(self, file_name, mocker):

        mocked = mocker.patch('dnb_direct_plus.management.commands.process_monitoring_data.Command._list_files')
        mocked.return_value = [file_name]

        out = StringIO()
        call_command('process_monitoring_data', stdout=out)

        assert MonitoringFileRecord.objects.count() == 0
        assert out.getvalue() == ''

    def test_processed_files_are_not_reprocessed(self, mocker):
        file_name = f'{settings.DNB_MONITORING_REGISTRATION_REFERENCE}_20191025205213_NOTIFICATION_1.zip'

        MonitoringFileRecord.objects.create(file_name=file_name, total=2, failed=1)

        mocked = mocker.patch('dnb_direct_plus.management.commands.process_monitoring_data.Command._list_files')
        mocked.return_value = [file_name]

        out = StringIO()
        call_command('process_monitoring_data', stdout=out)

        assert MonitoringFileRecord.objects.count() == 1
        assert out.getvalue() == f'{file_name} already processed; skipping\n'

    def test_processed_files_are_recorded(self, mocker):
        file_name = f'{settings.DNB_MONITORING_REGISTRATION_REFERENCE}_20191025205213_NOTIFICATION_1.zip'

        mocked = mocker.patch('dnb_direct_plus.management.commands.process_monitoring_data.Command._list_files')
        mocked.return_value = [file_name]
        mocked_handler = mocker.patch('dnb_direct_plus.management.commands.process_monitoring_data.process_notification_file')
        mocked_handler.return_value = (100, 10,)

        out = StringIO()
        call_command('process_monitoring_data', stdout=out)

        assert MonitoringFileRecord.objects.count() == 1
        record = MonitoringFileRecord.objects.first()
        assert record.file_name == file_name
        assert record.total == 100
        assert record.failed == 90
        assert out.getvalue() == f'Processing: {file_name}\n{file_name}\t\tTotal: 100\tFailed: 90\n'

    def test_exceptions_kill_the_ingest_pipeline(self, mocker):
        assert MonitoringFileRecord.objects.count() == 0
        file_name = f'{settings.DNB_MONITORING_REGISTRATION_REFERENCE}_20191025205213_NOTIFICATION_1.zip'
        file_name2 = f'{settings.DNB_MONITORING_REGISTRATION_REFERENCE}_20191025205213_Exceptions.zip'

        mocked = mocker.patch('dnb_direct_plus.management.commands.process_monitoring_data.Command._list_files')
        mocked.return_value = [file_name, file_name2]
        mocked_handler = mocker.patch(
            'dnb_direct_plus.management.commands.process_monitoring_data.process_notification_file')
        mocked_handler.side_effect = Exception('Something has gone wrong.')

        out = StringIO()

        with pytest.raises(Exception):
            call_command('process_monitoring_data', stdout=out)

        assert MonitoringFileRecord.objects.count() == 0

    @pytest.mark.parametrize('archive_file',[
        True,
        False
    ])
    def test_files_are_archived(self, archive_file, mocker, settings):

        settings.DNB_ARCHIVE_PROCESSED_FILES = archive_file

        assert MonitoringFileRecord.objects.count() == 0

        file_name = f'{settings.DNB_MONITORING_REGISTRATION_REFERENCE}_20191025205213_NOTIFICATION_1.zip'

        mocked = mocker.patch('dnb_direct_plus.management.commands.process_monitoring_data.Command._list_files')

        mocked.return_value = [file_name]
        mocked_handler = mocker.patch(
            'dnb_direct_plus.management.commands.process_monitoring_data.process_notification_file')
        mocked_handler.return_value = (100, 10,)

        mocked_archive_file = mocker.patch(
            'dnb_direct_plus.management.commands.process_monitoring_data.Command._archive_file')

        out = StringIO()

        call_command('process_monitoring_data', stdout=out)

        assert mocked_archive_file.called == archive_file

        if archive_file:
            mocked_archive_file.assert_called_once_with(file_name)

    def test_processed_file_success(self, mocker, cmpelk_api_response_json):
        company = CompanyFactory()

        update_data = [{
                'type': 'UPDATE',
                'organization': {
                    'duns': company.duns_number
                },
                'elements': [
                    {
                        'element': 'organization.primaryName',
                        'previous': '',
                        'current': 'Acme Corp',
                        'timestamp': '2019-06-25T01:00:17Z"'
                    },
                ]
            },
            json.loads(cmpelk_api_response_json),
        ]

        mocked = mocker.patch('dnb_direct_plus.monitoring.open_zip_file')
        mocked.return_value.__enter__.return_value = [json.dumps(line) for line in update_data]
        mocked.return_value.__exit__.return_value = False

        assert MonitoringFileRecord.objects.count() == 0
        file_name = f'{settings.DNB_MONITORING_REGISTRATION_REFERENCE}_20191025205213_NOTIFICATION_1.zip'

        mocked_list_files = mocker.patch(
            'dnb_direct_plus.management.commands.process_monitoring_data.Command._list_files')
        mocked_list_files.return_value = [file_name]

        out = StringIO()

        call_command('process_monitoring_data', stdout=out)

        assert out.getvalue() == f'Processing: {file_name}\n{file_name}\t\tTotal: 2\tFailed: 1\n'
        assert MonitoringFileRecord.objects.count() == 1
        record = MonitoringFileRecord.objects.first()
        assert record.file_name == file_name
        assert record.total == 2
        assert record.failed == 1

