import pytest
from company.tests.factories import CompanyFactory
from django.core.exceptions import ValidationError

# mark the whole module for db use
pytestmark = pytest.mark.django_db

class TestCompany:
    """Tests for the company model."""

    def test_company_with_invalid_parent_duns(self):
        company = CompanyFactory(parent_duns_number='123')
        
        with pytest.raises(ValidationError):
            company.full_clean()

    def test_company_without_parent_duns(self):
        company = CompanyFactory(
            parent_duns_number=None,
            global_ultimate_duns_number='123456789',
            employee_number=1000,
            worldbase_source_updated_timestamp='2020-01-01',
            last_updated_source_timestamp='2020-01-01',
            last_updated='2020-01-01'
        )

        company.full_clean()
        assert company.parent_duns_number is None

    def test_company_with_valid_parent_duns(self):
        company = CompanyFactory(
            parent_duns_number='123456789',
            global_ultimate_duns_number='987654321',
            employee_number=1000,
            worldbase_source_updated_timestamp='2020-01-01',
            last_updated_source_timestamp='2020-01-01',
            last_updated='2020-01-01'
        )

        company.full_clean()
        assert company.parent_duns_number == '123456789'


