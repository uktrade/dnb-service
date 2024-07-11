import os

import dj_database_url
import environ

import sentry_sdk
from celery.schedules import crontab
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
    'django_prometheus',
    'elasticapm.contrib.django',
    'api',
    'company',
    'core',
    'dnb_direct_plus',
    'dnb_worldbase',
    'health_check',
    'user',
    'workspace',
    'drf_spectacular',
]

if DEBUG:
    INSTALLED_APPS.append('django_extensions')

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.IpRestrictionMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
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
    'core.backends.CustomAuthbrokerBackend',
]

LOGIN_REDIRECT_URL = 'admin:index'

AUTH_USER_MODEL = 'user.User'

ENABLE_STAFF_SSO = env.bool('ENABLE_STAFF_SSO', True)

# IP restriction

IP_RESTRICT = env.bool('IP_RESTRICT')
IP_RESTRICT_APPS = ['admin']
IP_RESTRICT_PATH_NAMES = ['prometheus-django-metrics']
ALLOWED_IPS = env.list('ALLOWED_IPS')
ALLOWED_IP_RANGES = env.list('ALLOWED_IP_RANGES', default=[])

# DNB API

DNB_API_USERNAME = env('DNB_API_USERNAME')
DNB_API_PASSWORD = env('DNB_API_PASSWORD')
DNB_API_RENEW_ACCESS_TOKEN_SECONDS_REMAINING = 300
DNB_MONITORING_REGISTRATION_REFERENCE = env('DNB_MONITORING_REGISTRATION_REFERENCE')
DNB_MONITORING_S3_BUCKET = env('DNB_S3_MONITORING_BUCKET')
DNB_ARCHIVE_PROCESSED_FILES = env.bool('DNB_ARCHIVE_PROCESSED_FILES')
DNB_ARCHIVE_PATH = env('DNB_ARCHIVE_PATH', default='archive/')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')

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
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)

sentry_sdk.init(
    env('SENTRY_DSN'),
    environment=env('SENTRY_ENVIRONMENT'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration()
    ],
    enable_tracing=True,
    sample_rate=0.01,
    traces_sample_rate=0.01, # reduce the number of performance traces
    enable_backpressure_handling=True, # ensure that when sentry is overloaded, we back off and wait
)

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
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'PAGE_SIZE': 100,
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.CustomCursorPagination',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# GOVUK notify

GOVUK_NOTIFICATIONS_API_KEY = env('GOVUK_NOTIFICATIONS_API_KEY')

# Change requests

CHANGE_REQUESTS_BATCH_SIZE = env.int('CHANGE_REQUESTS_BATCH_SIZE', 20)
CHANGE_REQUESTS_RECIPIENTS = env.list('CHANGE_REQUESTS_RECIPIENTS', default=[])

# Investigation requests

INVESTIGATION_REQUESTS_BATCH_SIZE = env.int('INVESTIGATION_REQUESTS_BATCH_SIZE', 20)
INVESTIGATION_REQUESTS_RECIPIENTS = env.list('INVESTIGATION_REQUESTS_RECIPIENTS', default=[])


# Celery beat

CELERY_BEAT_SCHEDULE = {}

if env.bool('ENABLE_CHANGE_REQUESTS_SUBMISSION', False):
    CELERY_BEAT_SCHEDULE['change_requests_submission'] = {
        'task': 'company.tasks.send_pending_change_requests',
        'schedule': crontab(minute=0, hour=1,),
    }

if env.bool('ENABLE_INVESTIGATION_REQUESTS_SUBMISSION', False):
    CELERY_BEAT_SCHEDULE['investigation_requests_submission'] = {
        'task': 'company.tasks.send_pending_investigation_requests',
        'schedule': crontab(minute=0, hour=2,),
    }


# Elastic APM settings

ELASTIC_APM_ENVIRONMENT = env('SENTRY_ENVIRONMENT')

ELASTIC_APM = {
  'SERVICE_NAME': 'dnb-service',
  'SECRET_TOKEN': env('ELASTIC_APM_SECRET_TOKEN'),
  'SERVER_URL' : env('ELASTIC_APM_URL'),
  'ENVIRONMENT': ELASTIC_APM_ENVIRONMENT,
}
