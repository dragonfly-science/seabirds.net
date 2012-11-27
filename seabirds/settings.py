
import logging, os
logging.basicConfig(level = logging.WARN,)

# These settings may be overridden in sitesettings
SITE_ROOT = os.path.dirname(__file__)
SITE_NAME = 'Seabirds.net development'
SITE_URL = 'http://localhost:8000'
SITE_ID = 1
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ADMINS = ()
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
    'django_coverage',
    'django.contrib.comments',
    'longerusername',
)

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
    from secrets import EMAIL_HOST_PASSWORD, EMAIL_HOST, EMAIL_HOST_USER, SERVER_EMAIL, DEFAULT_FROM_EMAIL
except ImportError:
    # Should we really nuke these? What if they are already setup in
    # sitesettings?
    EMAIL_HOST_PASSWORD = ''
    EMAIL_HOST = ''
    EMAIL_HOST_USER = ''
    SERVER_EMAIL = ''
    DEFAULT_FROM_EMAIL = ''
EMAIL_NOREPLY = 'noreply@seabirds.net'
SUPPORT_EMAIL = 'Edward Abraham <edward@dragonfly.co.nz>'


# Required for enforcing a global login during testing
LOGIN_URL = '/accounts/login/'

COVERAGE_REPORT_HTML_OUTPUT_DIR = 'htmlcov'

PIGEONPOST_DEFER_POST_MODERATOR = 30*60 #10 minutes

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: "/petrel/%s/" % u.username,
    }

# TODO: Seems like this could be worked out by inspecting the models?
# max of "first_name(30)-last_name(30)-int" combination or email(75)
MAX_USERNAME_LENGTH = 75
