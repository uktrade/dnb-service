from django.conf import settings

from django_elasticsearch_dsl import DocType, fields, Index

from .models import Company


company_index = Index('company')

company_index.settings(
    **settings.ELASTICSEARCH_INDEX_SETTINGS
)


@company_index.doc_type
class CompanyDocument(DocType):
    duns_number = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
        }
    )

    country_name = fields.TextField(
        fields={
            'raw': fields.KeywordField()
        }
    )

    business_name = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
            'completion': fields.CompletionField(),
        }
    )

    class Meta:
        model = Company

        fields = [
            'secondary_name',
            'street_address',
            'street_address2',
            'city',
            'state',
            'country_code',
            'postal_code',
            # 'national_id_number',
            # 'national_id_code_type',
            # 'line_of_business',
            # 'is_out_of_business',
            # 'year_started',
            # 'global_ultimate_duns_number',
            # 'employee_number',
            # 'is_employees_number_estimated',
            # 'annual_sales',
            # 'is_annual_sales_estimated',
            # 'legal_status',
            # 'status_code',
        ]
