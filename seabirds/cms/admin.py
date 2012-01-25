from django import forms
from django.db import models
from django.contrib import admin
from cms.models import Page, Image, Placement, Person, File, Post, Navigation
from reversion.admin import VersionAdmin
from django.contrib.auth.models import User
from django.contrib.contenttypes.generic import GenericTabularInline
from mptt.admin import MPTTModelAdmin



class NavigationAdmin(MPTTModelAdmin):
    list_display = ('name', 'order', 'url', 'parent')
    list_filter = ('parent',)
    fieldsets = ((None, {'fields':(('order', 'name', 'url'), ('title', 'parent'),)}),)
admin.site.register(Navigation, NavigationAdmin)

class PlacementInline(GenericTabularInline):
    model = Placement
    extra = 1
    formfield_overrides = {
        models.TextField: {'widget': 
            forms.Textarea(attrs={'cols': 50, 'rows':2, })
        },
    }

class PageAdmin(admin.ModelAdmin):
    prepopulated_fields = {"name": ("title",)}
    list_display = ('title', 'name', 'parent', 'published')
    list_filter = ('parent', 'published')
    fieldsets = ((None, {'fields':(('title', 'name', 'parent'), ('order', 'published'), 'text')}),)
    inlines = (PlacementInline,)
    def placements(self, obj):
        return obj.image.count() or ''
    placements.short_description = 'Images'
    formfield_overrides = {
        models.TextField: {'widget': 
            forms.Textarea(attrs={'rows':30, 'style':'width: 100%; font-size:1.3em'})
        },
    }
admin.site.register(Page, PageAdmin)

class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"name": ("title",)}
    list_display = ('title', 'name', 'author', 'date_published', 'published')
    list_filter = ('author', 'published')
    fieldsets = ((None, {'fields':(('title', 'name', 'author'), ('date_published', 'published'), 'teaser', 'text')}),)
    inlines = (PlacementInline,)
    def placements(self, obj):
        return obj.image.count() or ''
    placements.short_description = 'Images'
    formfield_overrides = {
        models.TextField: {'widget': 
            forms.Textarea(attrs={'rows':15, 'style':'width: 100%; font-size:1.3em'})
        },
    }
admin.site.register(Post, PostAdmin)

#
#class PostAdmin(VersionAdmin):
#    list_display = ('author', 'title', 'page_link', 'placements', 'order', 'date_updated')
#    list_filter = ('page', 'date_updated', 'published')
#    inlines = (PlacementInline,)
#    def placements(self, obj):
#        return obj.image.count() or ''
#    placements.short_description = 'Images'
#
#    def page_link(self, obj):
#        return " &gt; ".join([ "<a href='%(href)s'>%(name)s</a>" % bc for bc in obj.page.breadcrumb()])
#    page_link.allow_tags = True
#admin.site.register(Post, PostAdmin)


class ImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'credit', 'image')
admin.site.register(Image, ImageAdmin)

class PersonAdmin(admin.ModelAdmin):
	list_display = ('username', 'firstname', 'lastname', 'order', 'active', 'role')
admin.site.register(Person, PersonAdmin)

class FileAdmin(admin.ModelAdmin):
	list_display = ('title','file')
admin.site.register(File, FileAdmin)

