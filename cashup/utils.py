import datetime

from django.conf import settings
from django.utils import timezone


def in_editable_period(time):
    time_limit = getattr(settings, "CASHUP_EDITABLE_PERIOD", 86400)
    return timezone.now() < (time + datetime.timedelta(seconds=time_limit))
