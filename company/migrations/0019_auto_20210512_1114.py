# Generated by Django 2.2.20 on 2021-05-12 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0018_update_company_details'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='address_area_abbrev_name',
            field=models.CharField(blank=True, max_length=3, verbose_name='State (Abbreviated)'),
        ),
        migrations.AddField(
            model_name='company',
            name='address_area_name',
            field=models.CharField(blank=True, max_length=255, verbose_name='State'),
        ),
        migrations.AddField(
            model_name='company',
            name='registered_address_area_abbrev_name',
            field=models.CharField(blank=True, max_length=3, verbose_name='State (Abbreviated)'),
        ),
        migrations.AddField(
            model_name='company',
            name='registered_address_area_name',
            field=models.CharField(blank=True, max_length=255, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='company',
            name='address_county',
            field=models.CharField(blank=True, max_length=255, verbose_name='County'),
        ),
        migrations.AlterField(
            model_name='company',
            name='registered_address_county',
            field=models.CharField(blank=True, max_length=255, verbose_name='County'),
        ),
    ]
