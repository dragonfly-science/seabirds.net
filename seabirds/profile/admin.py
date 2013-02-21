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

def mark_as_researcher(modeladmin, request, queryset):
    queryset.update(is_researcher=True)
mark_as_researcher.short_description='Mark selected users as researchers'

def mark_as_not_researcher(modeladmin, request, queryset):
    queryset.update(is_researcher=False)
mark_as_not_researcher.short_description='Mark selected users as not researchers'

def mark_as_inactive(modeladmin, request, queryset):
    for profile in queryset:
        profile.user.is_active = False
        profile.user.save()
mark_as_inactive.short_description='Mark selected users as inactive'

def mark_as_active(modeladmin, request, queryset):
    for profile in queryset:
        profile.user.is_active = True
        profile.user.save()
mark_as_active.short_description='Mark selected users as active'

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

def is_active(self):
    if self.user.is_active:
        return '<img src="/static/admin/img/icon-yes.gif" alt="True">'
    else:
        return '<img src="/static/admin/img/icon-no.gif" alt="False">'
is_active.allow_tags = True
is_active.short_description = 'Is active'

def last_login(self):
    return self.user.last_login.strftime("%h. %d, %Y")
last_login.short_description = 'Last login'

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', first_name, last_name, email, 'institution', 'country',  
        is_active, 'is_valid_seabirder', 'is_researcher',
        'date_created', last_login, google_search_field, edit_user_field)
    list_filter = ('institution','country', 'is_valid_seabirder', 'date_created')
    fields = ('user',
            ('title', 'is_valid_seabirder', 'is_researcher'),
            'webpage', 'display_email',
            'institution', 'institution_type', 'institution_website',
            'country',
            'research', 'research_field',
            'photograph',
            'seabirds',
            'collaboration_choices',
            'subscriptions',
            'twitter', 'display_twitter',
            'accept_terms')
    actions = [mark_as_active, mark_as_inactive, mark_as_valid, mark_as_invalid,
            mark_as_researcher, mark_as_not_researcher]
admin.site.register(UserProfile, UserProfileAdmin)

class CollaborationChoiceAdmin(admin.ModelAdmin):
    list_display = ('label',)
admin.site.register(CollaborationChoice, CollaborationChoiceAdmin)
