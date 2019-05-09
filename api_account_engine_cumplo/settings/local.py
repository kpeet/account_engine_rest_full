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









