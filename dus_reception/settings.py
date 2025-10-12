from corsheaders.defaults import default_headers, default_methods
from decouple import config
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = True

# ALLOWED_HOSTS SETTING
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",    
]

# CSRF TRUSTED_ORIGINS SETTING
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",    
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # LOCAL APPS
    'authapp',
    'managementapp',

    # 3RD PARTY APPS
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist', 
]

#SIMPLE JWT SETTINGS
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'ISSUER': 'dus_reception',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# JAZZMIN CONFIGURATION
JAZZMIN_SETTINGS = {
    # TITLE & BRANDING
    "site_title": "MSS Admin",
    "site_header": "MSS Admin Dashboard",
    "site_brand": "MSS Admin",
    "welcome_sign": "Welcome to MSS Admin",

    # UI/UX
    "show_sidebar": True,
    "navigation_expanded": True,
    "show_ui_builder": True,       
    "changeform_format": "horizontal_tabs",

    # TOP MENU LINKS
    "topmenu_links": [
        {"name": "Home", "url": "/", "permissions": ["auth.view_user"]},
        {"name": "Support", "url": "https://www.megaminds.com.np/", "new_window": True},
        {"name": "Developer", "url": "https://www.omkumarpandey.com.np/", "new_window": True},
    ],

    # SIDEBAR CONFIGURATION
    "show_sidebar_icons": False,     
    "related_modal_active": True,    
}


# CORS SETTINGS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ['*']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dus_reception.urls'

# TEMPLATES SETTING
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'Frontend'],
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

WSGI_APPLICATION = 'dus_reception.wsgi.application'

# DATABASE CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
        'AUTOCOMMIT': True,
    }
}



AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# INTERNATIONALIZATION & TIMEZONE
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

# STATIC & MEDIA FILES
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AUTHENTICATION SETTINGS
LOGIN_URL = 'login_page_view'
LOGIN_REDIRECT_URL = 'company_list_view'

# LARGE FILE UPLOAD SETTINGS
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024 * 1024

FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
]

FILE_UPLOAD_TEMP_DIR = None  



# CACHE SETTINGS
# ----------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Optional: Database connection optimization
DATABASES['default']['CONN_MAX_AGE'] = 60



# EMAIL CONFIGURATION
# ----------------------------------------
EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# COMPANY EMAIL SETTINGS
DEFAULT_FROM_EMAIL = f'MEGA MINDS PVT LTD <{config("EMAIL_HOST_USER")}>'
SERVER_EMAIL = f'MEGA MINDS PVT LTD <{config("EMAIL_HOST_USER")}>'
EMAIL_USE_LOCALTIME = True
ADMINS = [('MEGA MINDS PVT LTD', config('EMAIL_HOST_USER'))]
MANAGERS = ADMINS
SUPPORT_EMAIL = config('EMAIL_HOST_USER')
COMPANY_WEBSITE = 'https://www.megaminds.com.np/'
LOGIN_URL = 'https://www.megaminds.com.np/login'
