# Generated by Django 2.2.10 on 2020-03-12 17:20

from django.db.models import JSONField
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0010_auto_20191202_2140'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='worldbase_source_updated_timestamp',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='worldbase_source',
            field=JSONField(null=True),
        ),
    ]
