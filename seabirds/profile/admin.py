from django import forms
from django.db import models
from django.contrib import admin
from profile.models import UserProfile, CollaborationChoice
from reversion.admin import VersionAdmin
from django.contrib.auth.models import User
from mptt.admin import MPTTModelAdmin

def mark_as_valid(modeladmin, request, queryset):
    queryset.update(is_valid_seabirder=True)
mark_as_valid.short_description='Mark selected users as valid seabirders'

def mark_as_invalid(modeladmin, request, queryset):
    queryset.update(is_valid_seabirder=False)
    for profile in queryset:
        profile.user.is_active = False
        profile.user.save()
mark_as_invalid.short_description='Mark selected users as invalid'

def google_search_field(self):
    return '<a href="http://google.com/#q=%s+%s+%s&output=search">Search</a>' % (
            self.user.first_name, self.user.last_name, self.institution
        )
google_search_field.allow_tags = True
google_search_field.short_description = 'Search'

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'country', 'is_valid_seabirder', 
        'date_created', google_search_field)
    list_filter = ('institution','country', 'is_valid_seabirder', 'date_created')
    actions = [mark_as_valid, mark_as_invalid]
admin.site.register(UserProfile, UserProfileAdmin)

class CollaborationChoiceAdmin(admin.ModelAdmin):
    list_display = ('label',)
admin.site.register(CollaborationChoice, CollaborationChoiceAdmin)
