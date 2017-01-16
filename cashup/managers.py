from django.db import models
from django.db.models import Q

class AuditTrailManager(models.Manager):
    def get_queryset(self):
        return super(AuditTrailManager, self).get_queryset().filter(
            version_superseded_time=None)


class OutletQuerySet(models.QuerySet):
    def for_personnel(self, personnel, is_manager=False):
        if is_manager:
            return self.filter(staff__is_manager=True,
                               staff__personnel=personnel)
        else:
            return self.filter(staff__personnel=personnel)
