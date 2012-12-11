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


def edit_user_field(self):
    return '<a href="/admin/auth/user/%s/">User</a>' % (
            self.user.id,
        )
edit_user_field.allow_tags = True
edit_user_field.short_description = 'Edit user'

def first_name(self):
    return self.user.first_name
first_name.short_description = 'First name'

def last_name(self):
    return self.user.last_name
last_name.short_description = 'Last name'

def email(self):
    return self.user.email
email.short_description = 'Email'

def last_login(self):
    return self.user.last_login.strftime("%h. %d, %Y")
last_login.short_description = 'Last login'

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', first_name, last_name, email, 'institution', 'country', 'is_valid_seabirder', 
        'date_created', last_login, google_search_field, edit_user_field)
    list_filter = ('institution','country', 'is_valid_seabirder', 'date_created')
    actions = [mark_as_valid, mark_as_invalid]
admin.site.register(UserProfile, UserProfileAdmin)

class CollaborationChoiceAdmin(admin.ModelAdmin):
    list_display = ('label',)
admin.site.register(CollaborationChoice, CollaborationChoiceAdmin)
