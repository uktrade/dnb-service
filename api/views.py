import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from company.elasticsearch import get_client, COMPANY_INDEX


class CompanySearchApiView(APIView):
    """A generic API view that proxies requests to elasticsearch."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        es = get_client()

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return Response('Missing request body', status.HTTP_400_BAD_REQUEST)

        response = es.search(index=COMPANY_INDEX, body=body)

        return Response(response)
