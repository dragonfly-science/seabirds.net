from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.translation import ugettext as _

from seabirds.license.models import License

class AdminImageWidget(AdminFileWidget):
    """
    From http://djangosnippets.org/snippets/934/
    and  http://www.psychicorigami.com/2009/06/20/django-simple-admin-imagefield-thumbnail/
    """
    def render(self, name, value, attrs=None):
        output = []
        if value and getattr(value, "url", None):
            file_name=str(value)
            output.append(u' <a href="%s" target="_blank"><img src="%s" alt="%s" /></a> %s ' % \
                (value.url, value.url, file_name, _('Change:')))
        output.append(super(AdminFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))

class LicenseAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'symbol':
            request = kwargs.pop("request", None)
            kwargs['widget'] = AdminImageWidget
            return db_field.formfield(**kwargs)
        return super(LicenseAdmin,self).formfield_for_dbfield(db_field, **kwargs)
    list_display = ('name', 'description', 'text', 'url', 'symbol')
admin.site.register(License, LicenseAdmin)
