from .base import *
from corsheaders.defaults import default_headers
#MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]
#INSTALLED_APPS += ['debug_toolbar', ]
#DEBUG_TOOLBAR_CONFIG = {
#  'DISABLE_PANELS': ['debug_toolbar.panels.redirects.RedirectsPanel', ],
#  'SHOW_TEMPLATE_CONTEXT': True,
#}
#INTERNAL_IPS = ['127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'account_engine_cumplo',
        'USER': 'root',
        'PASSWORD': 'pa55w0rd',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
                    'charset': 'utf8mb4',
                },
            }
}

INSTALLED_APPS += ['corsheaders']#https://pypi.org/project/django-cors-headers/

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware'] + MIDDLEWARE

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = default_headers + (
    'Content-Disposition',
)

LOGGING = {
    'version': 1,
    'formatters': {
        'large': {
            'format': '%(asctime)s  %(levelname)s  %(process)d  %(pathname)s  %(funcName)s  %(lineno)d  %(message)s  '
        }
    },
    'handlers': {
        'errors_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'filename': 'api_account_engine_cumplo/logs/InfoLoggers.log',
            'formatter': 'large',
        },
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'filename': 'api_account_engine_cumplo/logs/InfoLoggers.log',
            'formatter': 'large',
        }


    },
    'loggers': {
        'error_logger': {
            'handlers': ['errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'info_logger': {
            'handlers': ['info_file'],
            'level': 'INFO',
            'propagate': False,
                }
    },
}
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID_TREASURY')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY_TREASURY')
TREASURY_SQS_URL = os.environ.get('TREASURY_SQS_URL')
AWS_REGION_VIRGINIA = os.environ.get('AWS_REGION_VIRGINIA')
AWS_REGION_OHIO = os.environ.get('AWS_REGION_OHIO')

# AWS SNS Topics
SNS_COUNTRY_PREFIX = os.environ.get('SNS_COUNTRY_PREFIX')
SNS_ENV_PREFIX = os.environ.get('SNS_ENV_PREFIX')
SNS_LOAN_PAYMENT = os.environ.get('SNS_LOAN_PAYMENT')
SNS_TREASURY_PAYSHEET = os.environ.get('SNS_TREASURY_PAYSHEET_REGISTRY')









