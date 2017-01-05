from decimal import Decimal

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


def time():
    return timezone.now().replace(second=0, microsecond=0)

class DenominationCount(object):
    def __init__(self, count, pence_value):
        self.count = count
        self.pence_value = pence_value

    @property
    def value(self):
        return Decimal(self.count * self.pence_value * 0.01)

    @property
    def pretty_value(self):
        return '{:04.2f}'.format(self.value)

    def __str__(self):
        return str(self.count)

class DenominationCountField(models.PositiveIntegerField):

    description = _("The number of notes or coins of a particular denomination")

    def __init__(self, *args, **kwargs):
        self.pence_value = kwargs.pop('pence_value', 1)
        super(DenominationCountField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(
            DenominationCountField, self).deconstruct()
        kwargs['pence_value'] = self.pence_value
        return name, path, args, kwargs

    def get_internal_type(self):
        return 'PositiveIntegerField'

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return DenominationCount(value, self.pence_value)

    def to_python(self, value):
        if isinstance(value, DenominationCount):
            return value

        if value is None:
            return value

        return DenominationCount(value, self.pence_value)

    def get_prep_value(self, value):
        if isinstance(value, DenominationCount):
            value = value.count
        return super(DenominationCountField, self).get_prep_value(value)

    def formfield(self, *args, **kwargs):
        field = super(DenominationCountField, self).formfield(*args, **kwargs)
        field.pence_value = self.pence_value
        return field

class Till(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='till',
        on_delete=models.CASCADE)
    location = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    default_float = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return "{0} at {1}".format(self.name, self.location)

    def get_absolute_url(self):
        return reverse('cashup_till_detail', args=[str(self.pk)])

class TillClosure(models.Model):
    till = models.ForeignKey(Till)
    closed_by = models.CharField(max_length=20, help_text="Staff name/initials")
    close_time = models.DateTimeField(default=time)

    # takings
    cash_takings = models.DecimalField(max_digits=12, decimal_places=2)
    card_takings = models.DecimalField(max_digits=12, decimal_places=2)
    total_takings = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    # cash held
    note_50GBP = DenominationCountField("£50 notes", default=0, pence_value=5000)
    note_20GBP = DenominationCountField("£20 notes", default=0, pence_value=2000)
    note_10GBP = DenominationCountField("£10 notes", default=0, pence_value=1000)
    note_5GBP = DenominationCountField("£5 notes", default=0, pence_value=500)
    coin_2GBP = DenominationCountField("£2 coins", default=0, pence_value=200)
    coin_1GBP = DenominationCountField("£1 coins", default=0, pence_value=100)
    coin_50p = DenominationCountField("50p coins", default=0, pence_value=50)
    coin_20p = DenominationCountField("20p coins", default=0, pence_value=20)
    coin_10p = DenominationCountField("10p coins", default=0, pence_value=10)
    coin_5p = DenominationCountField("5p coins", default=0, pence_value=5)
    coin_2p = DenominationCountField("2p coins", default=0, pence_value=2)
    coin_1p = DenominationCountField("1p coins", default=0, pence_value=1)

    # reconciliation
    till_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    till_float = models.DecimalField(max_digits=12, decimal_places=2)
    till_difference = models.DecimalField(max_digits=12, decimal_places=2)

    # other
    notes = models.TextField(blank=True)

    def total(self):
        denominations = [self.note_50GBP, self.note_20GBP, self.note_10GBP,
                         self.note_5GBP, self.coin_2GBP, self.coin_1GBP,
                         self.coin_50p, self.coin_20p, self.coin_10p,
                         self.coin_5p, self.coin_2p, self.coin_1p]
        return sum([d.value for d in denominations])

    @property
    def to_bank(self):
        return self.till_total - self.till_float

    def save(self, *args, **kwargs):
        self.total_takings = self.cash_takings + self.card_takings
        self.till_total = self.total()
        self.till_difference = self.till_total - self.cash_takings - self.till_float
        super(TillClosure, self).save(*args, **kwargs)

    def __str__(self):
        return '{0} closure at {1:%H:%M} on {1:%d/%m/%Y}'.format(
            self.till.name, self.close_time)

    def get_absolute_url(self):
        return reverse('cashup_closure_detail', args=[str(self.pk)])

