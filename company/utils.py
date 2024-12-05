import io
import codecs
import csv
from copy import deepcopy

from django.conf import settings
from django.utils.timezone import now

from company.constants import ADDRESS_FIELDS
from core.notify import notify_by_email, TEMPLATE_IDS


FIELD_LABELS = {
    'primary_name': 'Business Name',
    'trading_names': 'Trading Name(s)',
    'domain': 'Website Domain',
    'trading_address': 'Trading Address',
    'registered_address': 'Registered Address',
    'employee_number': 'Employee Number',
    'annual_sales': 'Annual Sales',
    'annual_sales_currency': 'Annual Sales Currency',
}


def _pop_address_string(prefix, changes, *default_value):
    address_components = [changes.pop(f'{prefix}_{field}', *default_value) for field in ADDRESS_FIELDS]

    if f'{prefix}_area' in changes and 'name' in changes[f'{prefix}_area']:
        address_components.insert(-1, changes[f'{prefix}_area'].pop('name'))
    if f'{prefix}_area' in changes and 'abbrev_name' in changes[f'{prefix}_area']:
        address_components.insert(-1, changes[f'{prefix}_area'].pop('abbrev_name'))

    return ', '.join(address_components)


def _get_change_request_row(change_request):
    changes = deepcopy(change_request.changes)
    if 'address_line_1' in changes:
        changes['trading_address'] = _pop_address_string('address', changes)
    if 'registered_address_line_1' in changes:
        changes['registered_address'] = _pop_address_string('registered_address', changes)
    readable_changes = {
        field_label: changes[field_name] for field_name, field_label in FIELD_LABELS.items() if field_name in changes
    }
    flat_readable_changes = [f'{key}: {value}' for key, value in readable_changes.items()]
    return {
        'duns_number': change_request.duns_number,
        'changes': '; '.join(flat_readable_changes),
    }


def _convert_stringio_to_bytesio(stringio_file):
    stringio_file.seek(0)
    bytesio_file = io.BytesIO(codecs.BOM_UTF8 + stringio_file.read().encode('utf-8'))
    return bytesio_file


def generate_change_request_csv(change_requests):
    """
    Given an iterable of ChangeRequest records, generate a CSV of changes which is readable by D&B
    support staff. The returned CSV content is a BytesIO file object, ready for sending by email.

    The CSV file is in the following example format:
    "duns_number","changes"
    "123456789","Address: 123 Fake Street, Burgess Hill, RH15 0TN, Sussex, New York, NY, GB; Business Name: BSmitty LTD;"
    """
    if not change_requests:
        raise IndexError("Cannot generate a change request CSV for an empty list of change requests.")
    writer_file = io.StringIO()
    field_names = ['duns_number', 'changes']
    writer = csv.DictWriter(writer_file, fieldnames=field_names, dialect='excel', delimiter=',')
    writer.writeheader()
    for change_request in change_requests:
        writer.writerow(_get_change_request_row(change_request))
    return _convert_stringio_to_bytesio(writer_file)


def send_change_request_batch(change_requests, batch_identifier):
    """
    Send a batch of change requests in a formatted CSV by email to settings.CHANGE_REQUESTS_RECIPIENTS.
    """
    context = {
        'batch_identifier': batch_identifier,
        'link_to_file': generate_change_request_csv(change_requests),
    }
    for email_address in settings.CHANGE_REQUESTS_RECIPIENTS:
        notify_by_email(email_address, TEMPLATE_IDS['change-request'], context)
    submitted_on = now()
    for change_request in change_requests:
        change_request.mark_as_submitted(submitted_on)


def _get_investigation_request_row(investigation_request):
    company_details = deepcopy(investigation_request.company_details)
    return {
        'ID': str(investigation_request.id),
        'Name': company_details.get('primary_name'),
        'Address': _pop_address_string('address', company_details, ''),
        'Domain': company_details.get('domain'),
        'Telephone Number': company_details.get('telephone_number'),
        'DUNS Number': '',
    }


def generate_investigation_request_csv(investigation_requests):
    """
    Given a list of InvestigationRequest records, generate a CSV which is readable by D&B
    support staff. The returned CSV content is a StringIO object.
    """
    if not investigation_requests:
        raise IndexError(
            'Cannot generate a CSV from an empty list of investigation requests.'
        )

    field_names = _get_investigation_request_row(
        investigation_requests[0]
    ).keys()

    csv_file = io.StringIO()
    writer = csv.DictWriter(
        csv_file,
        fieldnames=field_names,
        dialect='excel',
        delimiter=',',
    )

    writer.writeheader()
    for investigation_request in investigation_requests:
        writer.writerow(
            _get_investigation_request_row(investigation_request)
        )

    csv_file.seek(0)
    return csv_file


def send_investigation_request_batch(investigation_requests, batch_identifier):
    """
    Send a batch of investigation requests in a CSV by email to
    settings.INVESTIGATION_REQUESTS_RECIPIENTS.
    """
    context = {
        'batch_identifier': batch_identifier,
        'link_to_file': _convert_stringio_to_bytesio(
            generate_investigation_request_csv(investigation_requests),
        ),
    }

    for email_address in settings.INVESTIGATION_REQUESTS_RECIPIENTS:
        notify_by_email(
            email_address,
            TEMPLATE_IDS['investigation-request'],
            context,
        )

    submitted_on = now()
    for investigation_request in investigation_requests:
        investigation_request.mark_as_submitted(submitted_on=submitted_on)
