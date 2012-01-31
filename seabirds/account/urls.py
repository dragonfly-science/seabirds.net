from django.conf.urls.defaults import *

from account.views import *

urlpatterns = patterns('',
    (r'^profile/$',                  profile),
    (r'^password-reset/$',           password_reset),
    (r'^password-reset-submitted/$', password_reset_submitted),
    (r'^password-reset-confirm/$',   password_reset_confirm),
)

