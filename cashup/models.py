from decimal import Decimal

from django.db import models, transaction
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator

from .modelfields import DenominationCountField

def time():
    return timezone.now().replace(second=0, microsecond=0)


class Personnel(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile',
        on_delete=models.CASCADE)
    business = models.ForeignKey('Business', related_name='personnel',
        on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)

    @property
    def name(self):
        name = self.user.first_name or ''
        if self.user.first_name:
            name = '{} {[0]}'.format(self.user.first_name,
                self.user.last_name or ' ').strip()
        return name or self.user.username


class Business(models.Model):
    name = models.SlugField(max_length=12)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('cashup_business_update')


class Outlet(models.Model):
    business = models.ForeignKey(Business, related_name='outlets',
        on_delete=models.CASCADE)
    personnel = models.ManyToManyField(Personnel, related_name='outlets',
        through='StaffPositions')
    name = models.SlugField(max_length=24, help_text='Enter a shop name or location')
    default_float = models.DecimalField(max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))])

    def __str__(self):
        return "{} Outlet".format(self.name)

    def get_absolute_url(self):
        return reverse('cashup_outlet_detail', kwargs={'name':self.name})

    class Meta:
        unique_together = ('name', 'business')


class StaffPositions(models.Model):
    personnel = models.ForeignKey(Personnel, related_name='positions',
        on_delete=models.CASCADE)
    outlet = models.ForeignKey(Outlet, related_name='staff',
        on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)

    class Meta:
        unique_together = ('outlet', 'personnel')


class AuditTrailManager(models.Manager):
    def get_queryset(self):
        return super(AuditTrailManager, self).get_queryset().filter(
            version_superseded_time=None)


class TillClosure(models.Model):
    outlet = models.ForeignKey(Outlet, related_name='tillclosures')
    closed_by = models.ForeignKey(Personnel, related_name='tillclosures',
        on_delete=models.CASCADE)
    close_time = models.DateTimeField(default=time)

    # takings
    cash_takings = models.DecimalField(max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))])
    card_takings = models.DecimalField(max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))])
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
    till_float = models.DecimalField(max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))])
    till_difference = models.DecimalField(max_digits=12, decimal_places=2)

    # other
    notes = models.TextField(blank=True, help_text="Add any useful info here")

    # versioning
    identity = models.PositiveIntegerField(editable=False, blank=True)
    version_number = models.PositiveIntegerField(editable=False, blank=True)
    object_created_time = models.DateTimeField(editable=False, blank=True)
    version_created_time = models.DateTimeField(editable=False, blank=True)
    version_superseded_time = models.DateTimeField(editable=False, blank=True, null=True)
    updated_by = models.ForeignKey(Personnel, null=True, editable=False, blank=True,
        related_name='updated_tillclosures', on_delete=models.PROTECT)

    objects = AuditTrailManager()
    audit_trail = models.Manager()

    def total(self):
        denominations = [self.note_50GBP, self.note_20GBP, self.note_10GBP,
                         self.note_5GBP, self.coin_2GBP, self.coin_1GBP,
                         self.coin_50p, self.coin_20p, self.coin_10p,
                         self.coin_5p, self.coin_2p, self.coin_1p]
        return sum([d.value for d in denominations])

    @property
    def to_bank(self):
        return self.till_total - self.till_float

    @property
    def is_deleted(self):
        return not TillClosure.objects.filter(
            pk=self.identity, version_superseded_time=None).exists()

    @transaction.atomic
    def save(self, duplicate=True, *args, **kwargs):
        if self.pk and duplicate:
            time = timezone.now()

            tc = TillClosure.objects.get(pk=self.pk)
            tc.pk = None
            tc.version_superseded_time = time
            tc.save(duplicate=False)

            self.version_number = self.version_number + 1
            self.version_created_time = time

        self.total_takings = self.cash_takings + self.card_takings
        self.till_total = self.total()
        self.till_difference = self.till_total - self.cash_takings - self.till_float
        super(TillClosure, self).save(*args, **kwargs)

    def __str__(self):
        return '{0} till closure at {1:%H:%M} on {1:%d/%m/%Y}'.format(
            self.outlet.name, self.close_time)

    def get_absolute_url(self):
        return reverse('cashup_closure_detail',
            kwargs={'pk': str(self.identity)})

    def get_audit_list_url(self):
        return reverse('cashup_closure_audit_trail_list',
            kwargs={'pk': str(self.identity)})

    def get_audit_url(self):
        return reverse('cashup_closure_audit_trail_detail', kwargs={
            'pk': str(self.identity), 'version': str(self.version_number)})

    class Meta:
        get_latest_by = 'close_time'
        ordering = ['close_time', 'version_number']

class NotesHelpText(models.Model):
    text = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.text
