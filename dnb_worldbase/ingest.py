import csv
import logging
from pathlib import Path

from smart_open import open

from django.db import transaction
from django.utils import timezone

from .constants import WB_HEADER_FIELDS
from company.models import Company, Country, PrimaryIndustryCode, RegistrationNumber

from .mapping import extract_company_data


logger = logging.getLogger(__name__)


@transaction.atomic
def update_company(wb_data, creation_date):
    """
    Update company with worldbase data
    """
    foreign_key_fields = ['registration_numbers', 'primary_industry_codes', 'industry_codes']

    company_data = extract_company_data(wb_data)

    try:
        company = Company.objects.get(duns_number=company_data['duns_number'])
    except Company.DoesNotExist:
        company = Company()

    created = company.pk is None

    overwrite_fields = created or not company.source

    company.worldbase_source_updated_timestamp = creation_date
    company.worldbase_source = wb_data

    if overwrite_fields:
        company.registration_numbers.all().delete()
        company.primary_industry_codes.all().delete()

        for field, value in company_data.items():
            if field.endswith('country'):
                setattr(company, field, Country.objects.get(iso_alpha2=value))
            elif field not in foreign_key_fields:
                setattr(company, field, value)

    company.save()

    if overwrite_fields:
        for registration_number in company_data['registration_numbers']:
            RegistrationNumber.objects.create(
                company=company,
                registration_type=registration_number['registration_type'],
                registration_number=registration_number['registration_number'],
            )
        for primary_industry_code in company_data['primary_industry_codes']:
            PrimaryIndustryCode.objects.create(
                company=company,
                code=primary_industry_code['code'],
                description=primary_industry_code['description'],
            )

    return created


def process_csv_data(csv_data, creation_date=None):
    """
    Iterates over each row of a company csv file and ingests the data.
    """

    stats = {
        'created': 0,
        'updated': 0,
        'failed': 0,
    }

    _creation_date = timezone.now() if not creation_date else timezone.make_aware(creation_date)

    for row_number, row_data in enumerate(csv_data, 1):

        wb_data = dict(zip(WB_HEADER_FIELDS, row_data))

        try:
            created = update_company(wb_data, _creation_date)

        except(KeyboardInterrupt, SystemExit):
            raise

        except BaseException as ex:

            logger.warning(f'row {row_number} failed {ex}')

            stats['failed'] += 1
            continue
        else:
            if created:
                stats['created'] += 1
            else:
                stats['updated'] += 1

    return stats


class WBIntlCsvProcessor:
    COLUMN_COUNT = 108

    def __init__(self, csvfile):
        self.csv_reader = csv.reader(csvfile, quotechar='^', delimiter='\t')

    def __iter__(self):
        for i, row in enumerate(self.csv_reader):
            if i == 0:
                if row[:3] == ['FILLER1', 'DUNS NO', 'NAME']:
                    # Only the first international file has a header row, which we skip
                    continue

            if len(row) != self.COLUMN_COUNT:
                raise IndexError('row {} has {} columns; expected: {}'.format(i, len(row), self.COLUMN_COUNT))

            yield row[1:]


class WBUKCsvProcessor:
    COLUMN_COUNT = 112

    def __init__(self, csvfile):
        self.csv_reader = csv.reader(csvfile, quotechar='"', delimiter=',')

    def __iter__(self):
        for i, row in enumerate(self.csv_reader):
            if i == 0:
                # UK data files always have a header row so we skip it
                continue

            if len(row) != self.COLUMN_COUNT:
                raise IndexError('row {} has {} columns; expected: {}'.format(i, len(row), self.COLUMN_COUNT))

            yield row[5:]


def process_wb_file(file_path, creation_date=None):
    """
    Attempt to process a DNB CSV file in international or UK format. The file is used to determine which type of file
    is being ingested.

    NOTE: because we are using smart open file data can be streamed in from s3
    """
    base_name = Path(file_path).parts[-1]

    if base_name.startswith('deptrde'):
        csv_class = WBIntlCsvProcessor
    elif base_name.startswith('UK'):
        csv_class = WBUKCsvProcessor
    else:
        raise ValueError(f'File name does not match expected format: {file_path}')

    with open(file_path, 'rt', encoding='iso-8859-1') as wb_file:
        stats = process_csv_data(csv_class(wb_file), creation_date)

    return stats
