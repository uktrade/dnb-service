import os

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk

from .serialisers import CompanySerialiser

COMPANY_INDEX = 'companies'
COMPANY_MAPPING_PATH = os.path.join(os.path.dirname(__file__), 'companies_mapping.json')


def get_client():
    return Elasticsearch(hosts=settings.ES_URL)


def create_index(delete_existing=False):
    """Create a companies index.  Set delete_existing to True to recreate the index."""

    with open(COMPANY_MAPPING_PATH) as f:
        mapping = f.read()

    es = get_client()

    if delete_existing:
        es.indices.delete(COMPANY_INDEX)

    es.indices.create(COMPANY_INDEX)
    es.indices.put_mapping(index=COMPANY_INDEX, body=mapping)


def _bulk_insert_format(data):
    """Format company data for ES bulk insert"""

    return {
        '_id': data['duns_number'],
        '_index': COMPANY_INDEX,
        '_source': data,
    }


def bulk_insert_companies(company_queryset):
    """Insert company data into elasticsearch using the ES bulk API"""

    es = get_client()

    for ok, item in streaming_bulk(
        es,
        (_bulk_insert_format(CompanySerialiser(company).data) for company in company_queryset),
        chunk_size=settings.ES_BULK_INSERT_CHUNK_SIZE,
    ):
        yield ok, item

    es.indices.refresh(COMPANY_INDEX)


def es_update_company(company_instance):
    """insert or update a company entry in elasticsearch"""
    es = get_client()

    body = CompanySerialiser(company_instance).data

    return es.index(
        index=COMPANY_INDEX,
        body=body,
        id=body['duns_number'],
        refresh=settings.ES_REFRESH_AFTER_AUTO_SYNC,
    )
