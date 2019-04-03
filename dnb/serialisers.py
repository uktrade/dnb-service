from django_elasticsearch_dsl_drf.serializers import DocumentSerializer

from .documents import CompanyDocument


class CompanyDocumentSerialiser(DocumentSerializer):
    class Meta:
        document = CompanyDocument
        exclude = ('id', )
