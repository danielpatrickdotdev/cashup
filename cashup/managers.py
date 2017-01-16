from django.db import models

class AuditTrailManager(models.Manager):
    def get_queryset(self):
        return super(AuditTrailManager, self).get_queryset().filter(
            version_superseded_time=None)
