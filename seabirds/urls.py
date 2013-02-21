import os

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.sitemaps import Sitemap, GenericSitemap
from django.contrib import admin
from django.views.generic.simple import redirect_to
from django.views.generic import TemplateView

from cms.models import Page
from cms.views import PostArchiveView
from profile.forms import ProfileForm
from registration.views import register
from profile.custom_registration import ProfileRegistrationForm
from longerusername.forms import AuthenticationForm

from cms.feeds import LatestPostsFeed

admin.autodiscover()

# Sitemaps
class PublicationsSitemap(Sitemap):
    def items(self):
        return os.listdir(os.path.join(settings.MEDIA_ROOT, 'publications'))

    def location(self, item):
        return '/publications/' + item
        
    changefreq = 'monthly'
    priority = 0.4


parent_page_dict = {'queryset': Page.objects.filter(published=True, parent=None)}
child_page_dict = {'queryset': Page.objects.filter(published=True, parent__isnull=False)}

sitemaps = {
    'root_pages': GenericSitemap(parent_page_dict, priority=0.7, changefreq='weekly'),
    'content_pages': GenericSitemap(child_page_dict, priority=0.5, changefreq='weekly'),
    # This is disabled until we actually support publications, since
    # the needed media dir does not exist
    #'publications': PublicationsSitemap()
}

# Urls
urlpatterns = []
urlpatterns += patterns('', 
    url(r'^posts/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$', 'cms.views.individual_post', name='individual-post'),
    # This uses the new Generic Class views of Django 1.3+
    # Our custom implementation ensures we don't leak information about staff only discussions
    url(r'^posts/$', PostArchiveView.as_view(date_field='date_published',template_name='cms/list.html'), name='show_posts'),
    (r'^groups/(?P<listing>[a-zA-Z0-9_\-]+)$', PostArchiveView.as_view(date_field='date_published',template_name='cms/list.html')),
    url(r'^feed/rss/posts$', LatestPostsFeed(), name='rssfeed'),
)

urlpatterns += patterns('',
    url(r'^$', 'cms.views.home', name='home'),
    #The top pages
    (r'^grappelli/', include('grappelli.urls')),
    (r'^admin/tagging/(.*)$', 'bibliography.views.tagging'),
    (r'^admin/', include(admin.site.urls)),
    (r'^favicon\.ico$', redirect_to, {'url': settings.STATIC_URL + 'favicon.ico'}),
    url('^petrel/mailinglist$', 'account.views.edit_profile_mailing_list', name='subscription_edit'), 
    url('^petrel/edit', 'profiles.views.edit_profile', {'form_class': ProfileForm,}, name='profile_edit'),
    ('^petrel/create', 'profiles.views.create_profile', {'form_class': ProfileForm,}),
    url('^petrel/delete', 'profile.views.delete_profile', name='profile_delete'),
    # Catch to fix the use of a relative url in the profile edit function ...
    ('^petrel/users/(?P<rest>.*)$', redirect_to, {'url': '/users/%(rest)s'}),
    url(r'^petrel/(?P<username>[\w.@+-]+)/$', 'profiles.views.profile_detail', name='profiles_profile_detail'),
    url(r'^petrel/$', 'profile.views.custom_list', name='profile_custom_list'),
    url(r'^petrel/', include('profiles.urls')),
    url('^edit/post/$', 'cms.views.edit_post', name='new-post'),
    url('^edit/post/(?P<post_id>\d*)/$', 'cms.views.edit_post', name='edit-post'),
    url('^edit/image/$', 'cms.views.edit_image', name='new-image'),
    url('^edit/image/(?P<image_id>\d*)/$', 'cms.views.edit_image', name='edit-image'),

    # Account related urls
    (r'^accounts/logout/',  'django.contrib.auth.views.logout',   {'next_page': '/'}),
    url(r'^accounts/register/$',
        register,
        {
            'backend': 'profile.custom_registration.ProfileBackend',
            'form_class': ProfileRegistrationForm
        },
        name='registration_register'
    ),    
    url(r'^accounts/profile/', 'profile.views.profile'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {
            'template_name': 'registration/login.html',
            'authentication_form': AuthenticationForm,
        }, name='auth_login'),
    (r'^accounts/', include('registration.backends.default.urls')),

    # Used by Axiom system to match seabirds.net theme
    url(r'^_template.html$', TemplateView.as_view(template_name='axiom.html')),

    (r'references/(?P<key>[a-zA-Z0-9_\-]+)\.bib$', 'bibliography.views.get_bib'),
    (r'references/(?P<key>[a-zA-Z0-9_\-]+)\.html$', 'cms.views.reference'),
    url(r'^images/(?P<key>.*).html$', 'cms.views.imagepage', name='image'),
    url(r'^images/(?P<filename>.*)$', 'cms.views.image', name='image'),
    url(r'^comments/', include('django.contrib.comments.urls')),
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),

    ### This should always be last as it will shortcut any other xxxx.html routes,
    # like _template.html etc
    url(r'^(?P<name>[-\w]+)\.html', 'cms.views.page', name='page'),

    url(r'^jobs/$', 'cms.views.jobs', name='jobs'),
    url(r'^gallery/create$', 'cms.views.edit_image', name='new-image'),
    url(r'^gallery/(?P<seabird_family>.*)$', 'cms.views.gallery', name='gallery'),

    # Statically served content..
    # TODO: This should be served directly instead of via Django
    (r'^resources/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'resources')}),
    (r'^cache/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'cache')}),
    (r'^files/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'files')}),
    (r'^css/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'css')}),
    (r'^publications/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'publications')}),
    (r'^js/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'js')}),
    (r'^users/(?P<path>.*)$','django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'users')}),
    (r'^yaml/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.MEDIA_ROOT, 'yaml')}),

)

