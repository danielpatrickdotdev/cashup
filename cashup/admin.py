from django.contrib import admin

from rules.contrib.admin import ObjectPermissionsModelAdmin

from .models import (Business, Outlet, TillClosure, NotesHelpText, Personnel,
                     StaffPosition)


class OutletAdmin(ObjectPermissionsModelAdmin):
    pass

admin.site.register(Outlet, OutletAdmin)

class TillClosureAdmin(ObjectPermissionsModelAdmin):
    pass

admin.site.register(TillClosure, TillClosureAdmin)

admin.site.register(Business)


class StaffPositionInline(admin.TabularInline):
    extra = 0
    model = StaffPosition

class PersonnelAdmin(admin.ModelAdmin):
    inlines = [
        StaffPositionInline,
    ]

admin.site.register(Personnel, PersonnelAdmin)

admin.site.register(NotesHelpText)
