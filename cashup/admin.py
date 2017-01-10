from django.contrib import admin

from rules.contrib.admin import ObjectPermissionsModelAdmin

from .models import Business, Outlet, TillClosure, NotesHelpText


class OutletAdmin(ObjectPermissionsModelAdmin):
    pass

admin.site.register(Outlet, OutletAdmin)

class TillClosureAdmin(ObjectPermissionsModelAdmin):
    pass

admin.site.register(TillClosure, TillClosureAdmin)

admin.site.register(Business)

admin.site.register(NotesHelpText)
