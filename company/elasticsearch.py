from django.conf import settings

from elasticsearch.helpers import streaming_bulk
from elasticsearch_dsl import Boolean, Completion, Date, Document, Index, Keyword, Text
from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=settings.ES_URL)

company_index = Index('companies')

DATE_FORMAT_STRING = 'yyyy-MM-dd HH:mm:ss.XX||yyyy-MM-dd HH:mm:ss.SSSSSSXXX||strict_date_optional_time||epoch_millis'


@company_index.document
class CompanyDocument(Document):

    created = Date(format=DATE_FORMAT_STRING)
    last_updated = Date(format=DATE_FORMAT_STRING)
    last_updated_source = Keyword()

    duns_number = Keyword()
    primary_name = Text(
        fields={'complete': Completion()}
    )

    address_line_1 = Text()
    address_line_2 = Text()
    address_town = Text()
    address_county = Text()
    address_country = Text()
    address_postcode = Text()

    registered_address_line_1 = Text()
    registered_address_line_2 = Text()
    registered_address_town = Text()
    registered_address_county = Text()
    registered_address_country = Text()
    registered_address_postcode = Text()

    is_out_of_business = Boolean()

    global_ultimate_duns_number = Keyword()

    def bulk_insert_dict(self):
        """Fix some issues with the data to make it suitable to use with the es client's bulk insert helper"""
        data = self.to_dict(True)

        data['_source']['is_out_of_business'] = data['_source']['is_out_of_business'].lower()

        return data

    class Meta:
        index = 'companies'

    @classmethod
    def from_company_model(cls, instance):
        """Return an es-dsl CompanyDocument containing a subset of fields
        relevant to the company search results"""

        # TODO: could this be built dynamically without having to maintain a list of fields?

        es_fields = [
            'created', 'last_updated', 'last_updated_source', 'duns_number', 'primary_name',
            'address_line_1', 'address_line_2', 'address_town', 'address_county', 'address_country',
            'address_postcode', 'registered_address_line_1', 'registered_address_line_2', 'registered_address_town',
            'registered_address_county', 'registered_address_country', 'registered_address_postcode',
            'is_out_of_business', 'global_ultimate_duns_number',
        ]

        return CompanyDocument(**{
            field: str(getattr(instance, field)) for field in es_fields
            }, meta={'id': instance.duns_number})


def es_index_company_data(company_queryset):
    """Insert company data into elasticsearch using ES's bulk API"""

    CompanyDocument.init()

    for ok, item in streaming_bulk(
        connections.get_connection(),
        (CompanyDocument.from_company_model(company).bulk_insert_dict() for company in company_queryset),
        chunk_size=settings.ES_BULK_INSERT_CHUNK_SIZE
    ):
        yield ok, item

    company_index.refresh()
