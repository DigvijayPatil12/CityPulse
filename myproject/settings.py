import os
import dj_database_url
from pathlib import Path

# settings.py (Quick Fix - Option B)

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'citypulse-production-73fb.up.railway.app' # <-- Allows the public domain
]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# 🔑 SECURITY & HOSTS 🔑
# SECURITY WARNING: keep the secret key used in production secret!
# Fetches key from the Render Environment Variable (SECRET_KEY) for production.
# The hardcoded value is only a fallback for local development.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-8%n*vah1@k7onuf3zcvjbx70ri1rz%vc&l^f%0^uyp_u8ugvyu')

# SECURITY WARNING: don't run with debug turned on in production!
# Checks if the RENDER environment variable is set (meaning we are on Render)
# and sets DEBUG=False for security.
DEBUG = 'RENDER' not in os.environ 

# ALLOWED_HOSTS is essential when DEBUG=False. Fetches host from Render variable.
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')



# Set to True to enable Django's time zone support
USE_TZ = True 

# Set this to your desired local timezone.
TIME_ZONE = 'Asia/Kolkata' # <--- CHANGE THIS TO YOUR LOCAL TIME ZONE


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]


# 🛡️ MIDDLEWARE 🛡️
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ⭐️ ADDED: WhiteNoise Middleware for serving static files in production.
    # It MUST be listed directly after SecurityMiddleware.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'


# 💾 DATABASE (PostgreSQL for Render/Production) 💾
# ⭐️ CORRECTED: Removed 'conn_health_check=True' to fix the TypeError.
DATABASES = {
    'default': dj_database_url.config(
        # Fallback to local SQLite if DATABASE_URL is not set and DEBUG is True.
        default=os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR}/db.sqlite3') if DEBUG else None,
        conn_max_age=600,
    )
}

# ⭐️ ADDED: A check to handle the case where DEBUG is False (production)
# but DATABASE_URL is missing, which is highly unlikely on Render but a good guardrail.
if not DATABASES['default']:
    # Fallback for production (DEBUG=False) if environment variable is missing.
    # This block should ideally not be reached on Render with a linked PostgreSQL database.
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# 🖼️ STATIC FILES (CSS, JavaScript, Images) 🖼️
STATIC_URL = 'static/'

# ⭐️ ADDED: The required setting for collectstatic to know where to save files.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ⭐️ ADDED: Tells Django/WhiteNoise to use compressed/cached static files for production.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_URL = 'login' 
LOGIN_REDIRECT_URL = 'role_redirect'

# Media files (uploaded files like images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'