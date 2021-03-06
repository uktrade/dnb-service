# Generated by Django 2.2.4 on 2019-12-10 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MonitoringFileRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('file_name', models.CharField(max_length=255, unique=True)),
                ('total', models.PositiveIntegerField()),
                ('failed', models.PositiveIntegerField()),
            ],
        ),
    ]
