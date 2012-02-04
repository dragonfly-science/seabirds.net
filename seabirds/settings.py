
import logging, os
logging.basicConfig(level = logging.WARN,)

# settings overridden in sitesettings
DEBUG = True
SITE_ROOT = '/usr/local/django/seabirds.net'
SITE_NAME = 'Seabirds.net development'
SITE_URL = 'http://localhost:8000'
SITE_ID = 1

try:
    from sitesettings import *
except ImportError:
    pass

from secrets import RECAPTCHA_PRIVATE_KEY

TEMPLATE_DEBUG = DEBUG

ADMINS = ()
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'seabirds',
    }
}


TIME_ZONE = 'Pacific/Auckland'
LANGUAGE_CODE = 'en-nz'
USE_I18N = True
MEDIA_ROOT = os.path.join(SITE_ROOT, 'media/')
MEDIA_URL = ''

#ADMIN_MEDIA_PREFIX = '/am/'

SECRET_KEY = 'vtc+y0G^ja;p19874356GHbakhhaayaya987'

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
    'seabirds.cms',
    'bibliography',
    'django.contrib.admin',
    'profiles', #Django profiles
    'profile', #App for storing user info
    'taggit',
    'mptt',
    'disqus',
    'reversion',
    'license',
    'django_countries',
    'registration',
    'captcha',
)


AUTH_PROFILE_MODULE = 'profile.UserProfile'
ACCOUNT_ACTIVATION_DAYS = 7

RECAPTCHA_PUBLIC_KEY = '6Le9Ms0SAAAAAMEtTQWyP-Pn93SUE3FeYC2LoVcw'

FROM_ADDRESS = 'web@seabirds.net'

INTERNAL_IPS = ('127.0.0.1',)
DISQUS_API_KEY = 'LZG4ehRCHVeOofUobfHU5TDWhtsC3o4UDnJHkGrwo0OmWtwtHpb46q7A8ebDUUFF'
DISQUS_WEBSITE_SHORTNAME = 'seabirds'

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'edward@dragonfly.co.nz'
EMAIL_PORT = 587
try:
    from secrets import EMAIL_HOST_PASSWORD
except ImportError:
    EMAIL_HOST_PASSWORD = ''
SUPPORT_EMAIL = 'Edward Abraham <edward@dragonfly.co.nz>'



CUCKOO_DIRECTORY = os.path.join(SITE_ROOT, 'patches')

# Required for enforcing a global login during testing
LOGIN_URL = '^login'

AVATAR_CROP_MIN_SIZE = 20
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(SITE_ROOT, 'static/')
