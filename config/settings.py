import os

import dj_database_url
import environ

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(
    DEBUG=(bool, False),
    RESTRICT_ADMIN=(bool, False),
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

VCAP_SERVICES = env.json('VCAP_SERVICES', {})

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_results',
    'django_celery_beat',
    'rest_framework',
    'rest_framework.authtoken',
    'api',
    'company',
    'core',
    'dnb_direct_plus',
    'dnb_worldbase',
    'health_check',
    'user',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AdminIpRestrictionMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config()
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Staff-sso config

AUTHBROKER_URL = env('AUTHBROKER_URL')
AUTHBROKER_CLIENT_ID = env('AUTHBROKER_CLIENT_ID')
AUTHBROKER_CLIENT_SECRET = env('AUTHBROKER_CLIENT_SECRET')

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'authbroker_client.backends.AuthbrokerBackend',
]

LOGIN_REDIRECT_URL = 'admin:index'

AUTH_USER_MODEL = 'user.User'

# IP restriction

RESTRICT_ADMIN = env('RESTRICT_ADMIN')
ALLOWED_ADMIN_IPS = env.list('ALLOWED_ADMIN_IPS')
ALLOWED_ADMIN_IP_RANGES = env.list('ALLOWED_ADMIN_IP_RANGES', default=[])

# DNB API

DNB_API_USERNAME = env('DNB_API_USERNAME')
DNB_API_PASSWORD = env('DNB_API_PASSWORD')
DNB_API_RENEW_ACCESS_TOKEN_SECONDS_REMAINING = 300

# Redis

if 'redis' in VCAP_SERVICES:
    REDIS_URL = VCAP_SERVICES['redis'][0]['credentials']['uri']
    REDIS_CELERY_URL = f'{REDIS_URL}?ssl_cert_reqs=CERT_REQUIRED'
else:
    REDIS_URL = env.str('REDIS_URL', '')
    REDIS_CELERY_URL = REDIS_URL

# Celery
CELERY_BROKER_URL = REDIS_CELERY_URL
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

sentry_sdk.init(
    env('SENTRY_DSN'),
    environment=env('SENTRY_ENVIRONMENT'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration()
    ]
)

# Elasticsearch

if 'elasticsearch' in VCAP_SERVICES:
    ES_URL = VCAP_SERVICES['elasticsearch'][0]['credentials']['uri']
else:
    ES_URL = env('ES_URL')

ES_SHARD_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 0
}
ES_BULK_INSERT_CHUNK_SIZE = 1000
ES_AUTO_SYNC_ON_SAVE = True
ES_REFRESH_AFTER_AUTO_SYNC = True

# DRF config

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}
