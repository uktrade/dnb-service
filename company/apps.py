from django.apps import AppConfig


class CompanyAppConfig(AppConfig):
    name = 'company'

    def ready(self):
        from . import signals  # noqa

