from rest_framework import serializers


class CompanySearchInputSerialiser(serializers.Serializer):

    STANDALONE_FIELDS = ['duns_numbers', 'search_term']

    duns_number = serializers.RegexField(regex=r'\d{9}', required=False)
    search_term = serializers.CharField(min_length=2, max_length=60, required=False)
    address_country = serializers.RegexField(regex='[A-Za-z]{2}', required=False)
    postal_code = serializers.CharField(min_length=1, max_length=20, required=False)
    page_size = serializers.IntegerField(min_value=1, default=10, required=False)
    page_number = serializers.IntegerField(min_value=1, default=1, required=False)

    def validate(self, data):
        """
        Check that at least one standalone field has been provided.
        """
        if not any(field in data for field in self.STANDALONE_FIELDS):
            raise serializers.ValidationError(f'At least one standalone field required: {self.STANDALONE_FIELDS}.')

        return data
