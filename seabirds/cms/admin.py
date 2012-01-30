from django import forms
from django.db import models
from django.contrib import admin
from cms.models import Page, Image, File, Post, Navigation
from reversion.admin import VersionAdmin
from django.contrib.auth.models import User
from mptt.admin import MPTTModelAdmin



class NavigationAdmin(MPTTModelAdmin):
    list_display = ('name', 'order', 'url', 'parent')
    list_filter = ('parent',)
    #fieldsets = ((None, {'fields':(('order', 'name', 'url'), ('title', 'parent'),)}),)
admin.site.register(Navigation, NavigationAdmin)


class PageAdmin(admin.ModelAdmin):
    prepopulated_fields = {"name": ("title",)}
    list_display = ('title', 'name', 'parent', 'published')
    list_filter = ('parent', 'published')
<<<<<<< HEAD
    #fieldsets = ((None, {'fields':(('title', 'name', 'parent'), ('order', 'published'), 'text', 'sidebar')}),)
=======
    fieldsets = ((None, {'fields':(('title', 'name', 'parent'), ('order', 'published'), 'text', 'sidebar')}),)
>>>>>>> faac0b7... Working with the image model
    save_on_top = True
    formfield_overrides = {
        models.TextField: {'widget': 
            forms.Textarea(attrs={'rows':15, 'style':'width: 100%; font-size:1.1em'})
        },
    }
admin.site.register(Page, PageAdmin)

class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"name": ("title",)}
    list_display = ('title', 'name', 'author', 'date_published', 'published')
    list_filter = ('author', 'published')
<<<<<<< HEAD
    #fieldsets = ((None, {'fields':(('title', 'name', 'author'), ('date_published', 'published'), 'teaser', 'text')}),)
=======
    fieldsets = ((None, {'fields':(('title', 'name', 'author'), ('date_published', 'published'), 'teaser', 'text')}),)
>>>>>>> faac0b7... Working with the image model
    formfield_overrides = {
        models.TextField: {'widget': 
            forms.Textarea(attrs={'rows':15, 'style':'width: 100%; font-size:1.3em'})
        },
    }
admin.site.register(Post, PostAdmin)

class ImageAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    prepopulated_fields = {"key": ("title",)}
=======
>>>>>>> faac0b7... Working with the image model
    list_display = ('key', 'tag', 'title', 'date_created', 'uploaded_by', 'thumbnail')
    list_filter = ('date_created', 'uploaded_by', 'owner')
admin.site.register(Image, ImageAdmin)

class FileAdmin(admin.ModelAdmin):
	list_display = ('title','file')
admin.site.register(File, FileAdmin)

