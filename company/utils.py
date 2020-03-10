import io
import csv
from copy import deepcopy


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


def _flatten_address(prefix, changes):
    try:
        address_components = [
            changes.pop(f'{prefix}_{field}')
            for field in ['line_1', 'line_2', 'town', 'county', 'postcode', 'country']
        ]
    except KeyError:
        raise IncompleteAddressException(
            f'Some {prefix} field(s) were missing. ChangeRequests for addresses must be all or nothing.'
        )
    changes[prefix] = ', '.join(address_components)
    return changes


def _get_change_request_row(change_request):
    row = [change_request.duns_number]
    changes = deepcopy(change_request.changes)
    if 'address_line_1' in changes:
        changes = _flatten_address('address', changes)
    if 'registered_address_line_1' in changes:
        changes = _flatten_address('registered_address', changes)
    readable_changes = {
        field_label: changes[field_name] for field_name, field_label in FIELD_LABELS.items() if field_name in changes
    }
    flat_readable_changes = [f'{key}: {value}' for key, value in readable_changes.items()]
    row.append('; '.join(flat_readable_changes))
    return row


def generate_change_request_csv(change_requests):
    """
    Given an iterable of ChangeRequest records, generate a CSV of changes which is readable by D&B
    support staff. The returned CSV content is a bytes object, ready for sending by email.
    """
    if not change_requests:
        raise IndexError("Cannot generate a change request CSV for an empty list of change requests.")
    writer_file = io.StringIO()
    writer = csv.writer(writer_file, dialect='excel', delimiter=',')
    for change_request in change_requests:
        writer.writerow(_get_change_request_row(change_request))
    content = writer_file.getvalue().encode('utf-8')
    return content
