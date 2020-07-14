import django.contrib.postgres.fields.jsonb
from django.db import migrations

def update_company_details_telephone(apps, schema_editor):
    faulty_string = '\u0003'
    InvestigationRequest = apps.get_model('company', 'InvestigationRequest')
    records = InvestigationRequest.objects.all()

    for record in records:
        if 'telephone_number' in record.company_details:
            if faulty_string in record.company_details['telephone_number']:
                details = record.company_details
                details['telephone_number'] = details['telephone_number'].replace(faulty_string, '')

                record.company_details = details
                record.save()

class Migration(migrations.Migration):

    dependencies = [
        ('company', '0016_auto_20200430_1332'),
    ]

    operations = [
        migrations.RunPython(update_company_details_telephone),
    ]
