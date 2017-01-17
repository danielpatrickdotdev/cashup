import operator
from functools import reduce

from django.db import models
from django.db.models import Q

class AuditTrailManager(models.Manager):
    def get_queryset(self):
        return super(AuditTrailManager, self).get_queryset().filter(
            version_superseded_time=None)


class OutletQuerySet(models.QuerySet):
    def for_personnel(self, personnel, is_manager=False):
        """
        Gets all Outlets which personnel object is associated with.
        For business owners this always includes all the Outlets in their
        business.
        Optional `is_manager` determines wether (for non-owners) the returned
        queryset will include Outlets they are staff of or just ones they
        manage.
        """
        filters = [
            Q(business__personnel=personnel) &
                Q(business__personnel__is_owner=True),
            Q(staff__is_manager=True) & Q(staff__personnel=personnel)
        ]
        if not is_manager:
            filters.append(
                Q(staff__is_staff=True) & Q(staff__personnel=personnel))
        q_obj = reduce(operator.or_, filters)
        return self.filter(q_obj).distinct().order_by('name')
