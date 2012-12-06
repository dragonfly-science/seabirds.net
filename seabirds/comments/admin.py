from django.contrib import admin
from comments.models import PigeonComment

class PigeonCommentAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Content',
           {'fields': ('user', 'user_name', 'user_email', 'user_url', 'comment')}
        ),
        ('Metadata',
           {'fields': ('submit_date', 'ip_address', 'is_public', 'is_removed')}
        ),
     )

    list_display = ('name', 'ip_address', 'submit_date', 'is_public', 'is_removed')
    list_filter = ('submit_date', 'site', 'is_public', 'is_removed')
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username', 'user_name', 'user_email', 'user_url', 'ip_address')

admin.site.register(PigeonComment, PigeonCommentAdmin)

