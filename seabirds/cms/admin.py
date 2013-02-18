from django import forms
from django.db import models
from django.contrib import admin
from cms.models import Page, Image, File, Post, Navigation, Listing
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
    #fieldsets = ((None, {'fields':(('title', 'name', 'parent'), ('order', 'published'), 'text', 'sidebar')}),)
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
    #fieldsets = ((None, {'fields':(('title', 'name', 'author'), ('date_published', 'published'), 'text')}),)
    formfield_overrides = {
        models.TextField: {'widget': 
            forms.Textarea(attrs={'size':15, 'class':'vTextfield', 'style':'height: 400px'})
            #forms.Textarea(attrs={'size':15, 'style':'width: 100%; font-size:1.3em'})
        },
    }
admin.site.register(Post, PostAdmin)

class ImageAdmin(admin.ModelAdmin):
    prepopulated_fields = {"key": ("title",)}
    list_display = ('key', 'tag', 'title', 'date_created', 'uploaded_by', 'thumbnail')
    list_filter = ('date_created', 'uploaded_by', 'owner')
admin.site.register(Image, ImageAdmin)

class FileAdmin(admin.ModelAdmin):
    list_display = ('title','file')
admin.site.register(File, FileAdmin)

class ListingAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'read_permission', 'post_permission', 
        'allow_comments', 'optional_list')
admin.site.register(Listing, ListingAdmin)
    

