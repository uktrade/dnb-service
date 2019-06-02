from django.db.models.signals import post_save
from django.dispatch import receiver

from django.conf import settings

from .models import Company
from .elasticsearch import es_update_company


@receiver(post_save, sender=Company)
def sync_with_es(sender, **kwargs):
    if settings.ES_AUTO_SYNC_ON_SAVE:
        es_update_company(sender)
