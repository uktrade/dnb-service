from django_elasticsearch_dsl_drf.constants import (
    LOOKUP_FILTER_PREFIX,
    LOOKUP_FILTER_RANGE,
    LOOKUP_FILTER_TERMS,
    LOOKUP_FILTER_WILDCARD,
    LOOKUP_QUERY_EXCLUDE,
    LOOKUP_QUERY_GT,
    LOOKUP_QUERY_GTE,
    LOOKUP_QUERY_IN,
    LOOKUP_QUERY_LT,
    LOOKUP_QUERY_LTE,
    SUGGESTER_COMPLETION,
)
from django_elasticsearch_dsl_drf.filter_backends import (
    DefaultOrderingFilterBackend,
    FilteringFilterBackend,
    IdsFilterBackend,
    SearchFilterBackend,
    SuggesterFilterBackend,
)
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from rest_framework.permissions import IsAuthenticated

from .documents import CompanyDocument
from .serialisers import CompanyDocumentSerialiser


class CompanyDocumentViewSet(DocumentViewSet):

    permission_classes = (IsAuthenticated,)

    document = CompanyDocument
    serializer_class = CompanyDocumentSerialiser

    lookup_field = 'duns_number'

    filter_backends = [
        IdsFilterBackend,
        DefaultOrderingFilterBackend,
        SearchFilterBackend,
        SuggesterFilterBackend,
        FilteringFilterBackend,
    ]

    search_fields = (
        'duns_number',
        'business_name',
        'secondary_name',
        'street_address',
        'street_address2',
        'city',
        'state',
        'country_name',
    )

    filter_fields = {
        'id': {
            'field': 'id',
            'lookups': [
                LOOKUP_FILTER_RANGE,
                LOOKUP_QUERY_IN,
                LOOKUP_QUERY_GT,
                LOOKUP_QUERY_GTE,
                LOOKUP_QUERY_LT,
                LOOKUP_QUERY_LTE,
                LOOKUP_FILTER_TERMS,
            ],
        },
        'duns_number': {
            'field': 'duns_number',
            'lookups': [
                LOOKUP_FILTER_TERMS,
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_EXCLUDE,
                LOOKUP_QUERY_IN,
            ],
        },
        'business_name': {
            'field': 'business_name',
            'lookups': [
                LOOKUP_FILTER_TERMS,
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_EXCLUDE,
                LOOKUP_QUERY_IN,
            ],
        },
        'city': {
            'field': 'city',
            'lookups': [
                LOOKUP_FILTER_TERMS,
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_EXCLUDE,
                LOOKUP_QUERY_IN,
            ],
        },
        'state': {
            'field': 'state',
            'lookups': [
                LOOKUP_FILTER_TERMS,
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_EXCLUDE,
                LOOKUP_QUERY_IN,
            ],
        },
        'country_name': {
            'field': 'country_name',
            'lookups': [
                LOOKUP_FILTER_TERMS,
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_EXCLUDE,
                LOOKUP_QUERY_IN,
            ],
        }
    }

    suggester_fields = {
        'business': {
            'field': 'business_name.completion',
            'default_suggester': SUGGESTER_COMPLETION,
        },
    }

    # ordering = ('business_name.raw',)
