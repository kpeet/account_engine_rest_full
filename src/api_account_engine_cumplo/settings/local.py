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
        'NAME': 'api_account_engine_common',
        'USER': 'root',
        'PASSWORD': 'dummypass',
        'HOST': 'localhost',
        'PORT': '3307',
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











