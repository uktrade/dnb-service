import pytest

from company.models import Company, Country


@pytest.mark.parametrize('es_auto_sync', [
    True,
    False
])
@pytest.mark.django_db
def test_signal_is_fired(es_auto_sync, mocker, settings):

    settings.ES_AUTO_SYNC_ON_SAVE = es_auto_sync
    mocked = mocker.patch('company.signals.es_update_company')

    Company.objects.create(
        duns_number='12345678',
        primary_name='test ltd',
        address_line_1='primary street',
        address_town='town',
        address_county='county',
        address_country=Country.objects.create(name='UK', iso_alpha2='GB', iso_numeric=790),
        address_postcode='postcode',
        legal_status='Corporation',
        year_started='2000',
        is_out_of_business=True,
    )

    assert mocked.called == es_auto_sync
