import io

import pytest

from company.utils import generate_investigation_request_csv


@pytest.fixture()
def get_csv_bytes():
    """
    Returns bytes of CSV given InvestigationRequest objects.
    """
    def _get_csv_bytes(investigation):
        return io.BytesIO(
            generate_investigation_request_csv(
                investigation,
            ).getvalue().encode('utf-8')
        ).getvalue()
    return _get_csv_bytes
