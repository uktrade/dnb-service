from rest_framework import serializers


class CommentSerializer(serializers.Serializer):
    search_term = serializers.CharField()
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()
