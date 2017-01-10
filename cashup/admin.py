from django.contrib import admin

from rules.contrib.admin import ObjectPermissionsModelAdmin

from .models import Business, Outlet, TillClosure, NotesHelpText


class OutletAdmin(ObjectPermissionsModelAdmin):
    #fields = ('user', 'name', 'default_float')
    pass

admin.site.register(Outlet, OutletAdmin)

class TillClosureAdmin(ObjectPermissionsModelAdmin):
    #fields = ['outlet', 'closed_by', 'close_time',
    #          'cash_takings', 'card_takings', 'total_takings',
    #          'note_50GBP', 'note_20GBP', 'note_10GBP', 'note_5GBP',
    #          'coin_2GBP', 'coin_1GBP', 'coin_50p', 'coin_20p',
    #          'coin_10p', 'coin_5p', 'coin_2p', 'coin_1p',
    #          'till_total', 'till_float', 'till_difference', 'notes']
    #
    #readonly_fields = ['total_takings', 'till_total', 'till_difference']
    pass

admin.site.register(TillClosure, TillClosureAdmin)

admin.site.register(Business)

admin.site.register(NotesHelpText)
