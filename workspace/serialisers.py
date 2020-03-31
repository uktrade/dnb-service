from company.serialisers import CompanySerialiser


class WorkspaceCompanySerialiser(CompanySerialiser):
    class Meta(CompanySerialiser.Meta):

        fields = [
            *CompanySerialiser.Meta.fields,
            'worldbase_source',
            'source',
        ]
