import logging
import os

logging.basicConfig(level = logging.WARN,)

# These settings may be overridden in sitesettings
SITE_ROOT = os.path.dirname(__file__)
SITE_NAME = 'Seabirds.net development'
SITE_URL = 'http://localhost:8000'
SITE_ID = 1
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ADMINS = (('Seabirds Admin', 'admin@seabirds.net'),)
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'seabirds',
        'USER': 'seabirds',
    }
}

try:
    # Site settings are private data for the production server
    # TODO: Why not place it all in secrets.py or place secrets
    # in sitesettings?
    from sitesettings import *
except ImportError, e:
    print "WARNING: While loading sitesettings, '%s'" % str(e) 

TIME_ZONE = 'Pacific/Auckland'
LANGUAGE_CODE = 'en-nz'
USE_I18N = True
MEDIA_ROOT = os.path.join(SITE_ROOT, 'media/')
MEDIA_URL = '/'

AVATAR_CROP_MIN_SIZE = 20
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(SITE_ROOT, 'static/')
ADMIN_MEDIA_PREFIX = STATIC_URL + "grappelli/"

TEMPLATE_DEBUG = DEBUG
# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    'seabirds.cms.views.get_base_navigation',
    'seabirds.cms.context_processors.site',
    'seabirds.admin.context_processors.whereami',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'seabirds.urls'

TEMPLATE_DIRS = (
    os.path.join(SITE_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.markup',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'cms',
    'comments',
    #'bibliography',
    'grappelli',
    'django.contrib.admin',
    'profiles', # Django profiles
    'profile', # App for storing user info
    'taggit',
    'mptt',
    'disqus',
    'reversion',
    'license',
    'django_countries',
    'registration',
    'captcha',
    'categories',
    'form_utils',
    'sorl.thumbnail',
    'cuckoo',
    'pigeonpost',
    'django.contrib.comments',
    'longerusername',

    'django_nose',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--with-cov', '--cov-report', 'html', '--cov-report', 'xml', '--cover-package=seabirds',
    '--logging-clear-handlers', '--with-xunit',
    ]

COMMENTS_APP = 'comments'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'profile.custom_registration.EmailAuthBackend',
)

AUTH_PROFILE_MODULE = 'profile.UserProfile'
ACCOUNT_ACTIVATION_DAYS = 7

RECAPTCHA_PUBLIC_KEY = '6Le9Ms0SAAAAAMEtTQWyP-Pn93SUE3FeYC2LoVcw'

FROM_ADDRESS = 'web@seabirds.net'

INTERNAL_IPS = ('127.0.0.1',)
DISQUS_WEBSITE_SHORTNAME = 'seabirds'

# Get API Keys 
from secrets import RECAPTCHA_PRIVATE_KEY, DISQUS_API_KEY, SECRET_KEY

#EMAIL_USE_TLS = True
try:
    from secrets import EMAIL_HOST_PASSWORD, EMAIL_HOST, EMAIL_HOST_USER
except ImportError:
    # Should we really nuke these? What if they are already setup in
    # sitesettings?
    EMAIL_HOST_PASSWORD = ''
    EMAIL_HOST = ''
    EMAIL_HOST_USER = ''
SERVER_EMAIL = 'Seabirds.net <noreply@seabirds.net>'
DEFAULT_FROM_EMAIL = 'Seabirds.net <noreply@seabirds.net>'
SUPPORT_EMAIL = 'Edward Abraham <edward@dragonfly.co.nz>'

COVERAGE_REPORT_HTML_OUTPUT_DIR = 'htmlcov'

# All delays are in seconds
COMMENT_EDIT_GRACE_PERIOD = 10*60
PIGEONPOST_DELAYS = {
        'cms.Post': {
            'moderator': 10*60,
            'subscriber': 12*60*60, # 12 hours
            'author': 10*60,
            },
        'cms.Comment': {
            'post_author': COMMENT_EDIT_GRACE_PERIOD + 5*60,
            'post_other_commenters': COMMENT_EDIT_GRACE_PERIOD + 5*60,
            },
}

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: "/petrel/%s/" % u.username,
    }

# TODO: Seems like this could be worked out by inspecting the models?
# max of "first_name(30)-last_name(30)-int" combination or email(75)
MAX_USERNAME_LENGTH = 75

import sys
#if manage.py test was called, use test settings
if 'test' in sys.argv:
    try:
        from test_settings import *
    except ImportError:
        pass
