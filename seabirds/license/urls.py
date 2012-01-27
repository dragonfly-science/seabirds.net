from django.conf.urls.defaults import *

from seabirds.cms.views import *

urlpatterns = patterns('',
    (r'^(?P<name>[a-zA-Z0-9_\-]+)/readme.html', readme),
    (r'^(?P<name>[a-zA-Z0-9_\-]+)\.html?$',  page),
    (r'^$',  page, dict(name = 'index')),
)

