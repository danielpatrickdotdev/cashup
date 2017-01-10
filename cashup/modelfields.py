from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _


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
