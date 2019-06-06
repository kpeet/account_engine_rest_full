import os
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ['SECRET_KEY_ACCOUNT_ENGINE']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'django_mysql',
    'account_engine',
    'credits',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer', ),
    'DEFAULT_PAGINATION_CLASS': 'core_account_engine.utils.pagination.DynamicPageNumberPagination',
    'PAGE_SIZE': 20,
}

ROOT_URLCONF = 'account_engine.urls'

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

WSGI_APPLICATION = 'api_account_engine_cumplo.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}


#DATABASE_ROUTERS = ['config.database_router.DatabaseRouter']


#DATABASES['default'] = dj_database_url.config()

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'es-es'

LANGUAGES = [
    ('es', 'Spanish'),
    ('en', 'English'),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


# Static PATH
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
STATIC_URL = '/static/'
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

TREASURY_SQS_URL = os.environ.get('TREASURY_SQS_URL')
AWS_REGION_VIRGINIA = os.environ.get('AWS_REGION_VIRGINIA')
AWS_REGION_OHIO = os.environ.get('AWS_REGION_OHIO')

# AWS SNS Topics
SNS_COUNTRY_PREFIX = os.environ.get('SNS_COUNTRY_PREFIX')
SNS_ENV_PREFIX = os.environ.get('SNS_ENV_PREFIX')

SNS_LOAN_PAYMENT = os.environ.get('SNS_LOAN_PAYMENT')
SNS_TREASURY_PAYSHEET = os.environ.get('SNS_TREASURY_PAYSHEET_REGISTRY')
SNS_INVESTMENT_PAYMENT = os.environ.get('SNS_INVESTMENT_PAYMENT')
SNS_INSTALMENT_PAYMENT = os.environ.get('SNS_INSTALMENT_PAYMENT')
SNS_LOAN_INVESTMENT_INSTALMENT_PAYMENT = os.environ.get('SNS_LOAN_INVESTMENT_INSTALMENT_PAYMENT')


