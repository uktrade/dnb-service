from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class CustomCursorPagination(CursorPagination):
    page_size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        """
        Override paginate_queryset() to ensure that a count is set on the CustomCursorPagination instance.
        """
        self.count = queryset.count()
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        """
        Respond with a custom response format which includes a count of the total records in the queryset.
        """
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.count,
            'results': data,
        })
