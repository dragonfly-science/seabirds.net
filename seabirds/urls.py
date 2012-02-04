import os

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.sitemaps import Sitemap, GenericSitemap
from django.contrib import admin

from cms.models import Page, Post
from profile.forms import ProfileForm
from registration.views import register
from profile.custom_registration import ProfileRegistrationForm

admin.autodiscover()

#from django.contrib.auth.models import User, Group
#from django.contrib.sites.models import Site
#for model in (Group, Site, User):
#    try:
#        admin.site.unregister(model)
#    except:
#        pass

#Sitemaps
class PublicationsSitemap(Sitemap):
    def items(self):
        return os.listdir(os.path.join(settings.MEDIA_ROOT, 'publications'))

    def location(self, item):
        return '/publications/' + item
        
    changefreq = 'monthly'
    priority = 0.4


page_dict = {'queryset': Page.objects.all()}

sitemaps = {
    'pages': GenericSitemap(page_dict, priority=0.6, changefreq='weekly'),
    'publications': PublicationsSitemap()
}

# Urls
urlpatterns = []



## Date based views for posts
info_dict = {
    'queryset': Post.objects.all(),
    'date_field': 'date_published',
}
urlpatterns += patterns('django.views.generic.date_based',
    url(r'^posts/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$', 'object_detail', 
        dict(info_dict, slug_field='name',template_name='cms/post.html',month_format='%m'), name='individual-post'),
    (r'^posts/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$','archive_day',dict(info_dict,template_name='cms/list.html')),
    (r'^posts/(?P<year>\d{4})/(?P<month>\d{1,2})/$','archive_month', dict(info_dict, template_name='cms/list.html')),
    (r'^posts/(?P<year>\d{4})/$','archive_year', dict(info_dict, template_name='cms/list.html')),
    (r'^posts/$','archive_index', dict(info_dict, template_name='cms/list.html')),
)

urlpatterns += patterns('',
    #The top pages
    (r'^admin/tagging/(.*)$', 'bibliography.views.tagging'),
    (r'^admin/', include(admin.site.urls)),
    #(r'^login',   'django.contrib.auth.views.login',    {'template_name': 'account/login.html'}),
    #(r'^logout',  'django.contrib.auth.views.logout',   {'next_page': '/'}),
    ('^profiles/edit', 'profiles.views.edit_profile', {'form_class': ProfileForm,}),
    ('^profiles/create', 'profiles.views.create_profile', {'form_class': ProfileForm,}),
    url(r'^profiles/', include('profiles.urls')),
    url(r'^accounts/register/$',
        register,
        {'backend': 'profile.custom_registration.ProfileBackend', 'form_class': ProfileRegistrationForm},        
        name='registration_register'
    ),    
    (r'^accounts/', include('registration.urls')),
    (r'references/(?P<key>[a-zA-Z0-9_\-]+)\.bib$', 'bibliography.views.get_bib'),
    (r'references/(?P<key>[a-zA-Z0-9_\-]+)\.html$',   'cms.views.reference'),
    (r'^$',                                         'cms.views.home'),
    (r'^images/(?P<filename>.*)$',                      'cms.views.image'),
    (r'^resources/(?P<path>.*)$',   'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'resources')}),
    (r'^files/(?P<path>.*)$',       'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'files')}),
    (r'^css/(?P<path>.*)$',          'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'css')}),
    (r'^publications/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'publications')}),
    (r'^js/(?P<path>.*)$',           'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'js')}),
    (r'^yaml/(?P<path>.*)$',           'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'yaml')}),
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    (r'^static/(?P<path>.*)$',   'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    url(r'^(?P<name>[-\w]+)\.html',           'cms.views.page', name='page'),
)

