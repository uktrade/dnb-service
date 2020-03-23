import io
import csv
from copy import deepcopy

from company.constants import ADDRESS_FIELDS


FIELD_LABELS = {
    'primary_name': 'Business Name',
    'trading_names': 'Trading Name(s)',
    'domain': 'Website Domain',
    'address': 'Address',
    'registered_address': 'Registered Address',
    'employee_number': 'Employee Number',
    'annual_sales': 'Annual Sales',
    'annual_sales_currency': 'Annual Sales Currency',
}


class IncompleteAddressException(Exception):
    """
    An error to explain that some address fields were missing for a particular ChangeRequest
    record.  ChangeRequests for addresses must be all or nothing.
    """


def _get_address_string(prefix, changes):
    address_components = [changes.pop(f'{prefix}_{field}') for field in ADDRESS_FIELDS]
    changes[prefix] = ', '.join(address_components)
    return changes


def _get_change_request_row(change_request):
    changes = deepcopy(change_request.changes)
    if 'address_line_1' in changes:
        changes = _get_address_string('address', changes)
    if 'registered_address_line_1' in changes:
        changes = _get_address_string('registered_address', changes)
    readable_changes = {
        field_label: changes[field_name] for field_name, field_label in FIELD_LABELS.items() if field_name in changes
    }
    flat_readable_changes = [f'{key}: {value}' for key, value in readable_changes.items()]
    return {
        'duns_number': change_request.duns_number,
        'changes': '; '.join(flat_readable_changes),
    }


def generate_change_request_csv(change_requests):
    """
    Given an iterable of ChangeRequest records, generate a CSV of changes which is readable by D&B
    support staff. The returned CSV content is file object, ready for sending by email.

    The CSV file is in the following example format:
    "duns_number","changes"
    "123456789","Address: 123 Fake Street, Burgess Hill, RH15 0TN, Sussex, GB; Business Name: BSmitty LTD;"
    """
    if not change_requests:
        raise IndexError("Cannot generate a change request CSV for an empty list of change requests.")
    writer_file = io.StringIO()
    field_names = ['duns_number', 'changes']
    writer = csv.DictWriter(writer_file, fieldnames=field_names, dialect='excel', delimiter=',')
    writer.writeheader()
    for change_request in change_requests:
        writer.writerow(_get_change_request_row(change_request))
    writer_file.seek(0)
    bytes_file = io.BytesIO(writer_file.read().encode('utf-8'))
    return bytes_file
