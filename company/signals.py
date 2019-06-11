from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .elasticsearch import es_update_company
from .models import Company


@receiver(post_save, sender=Company)
def sync_with_es(sender, instance, **kwargs):
    if settings.ES_AUTO_SYNC_ON_SAVE:
        es_update_company(instance)
