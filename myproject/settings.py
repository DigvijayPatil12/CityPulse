import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# 🔑 SECURITY & HOSTS 🔑
# Fetches key from the Render Environment Variable (SECRET_KEY).
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-8%n*vah1@k7onuf3zcvjbx70ri1rz%vc&l^f%0^uyp_u8ugvyu')

# SECURITY WARNING: don't run with debug turned on in production!
# Check the RENDER env var to set DEBUG=False for production, or default to True for local.
DEBUG = 'RENDER' not in os.environ 

# ALLOWED_HOSTS is essential when DEBUG=False.
# We read the host list from the environment variable (Render URL) for security.
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# If the app is running in debug mode (local), accept all hosts for convenience.
if DEBUG:
    ALLOWED_HOSTS = ['*']

# Set to True to enable Django's time zone support
USE_TZ = True 

# Set this to your desired local timezone.
TIME_ZONE = 'Asia/Kolkata' # Ensure this is your desired local time zone


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    # ⭐️ ADDED: Cloudinary for free media storage
    'cloudinary_storage', 
    'cloudinary',
]


# 🛡️ MIDDLEWARE 🛡️
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ⭐️ ADDED: WhiteNoise Middleware MUST be listed directly after SecurityMiddleware.
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


# 💾 DATABASE (Using the Railway DB via Render's Env Var) 💾
# We must use the DATABASE_URL environment variable (set on Render) 
# which points to your external Railway PostgreSQL service.
DATABASES = {
    'default': dj_database_url.config(
        # Fallback to local SQLite only if DEBUG is True and no DATABASE_URL is set.
        default=os.environ.get('DATABASE_URL') if not DEBUG else f'sqlite:///{BASE_DIR}/db.sqlite3',
        conn_max_age=600,
    )
}

# ⭐️ ADDED: A critical guardrail for production environment (DEBUG=False).
# If the DATABASE_URL variable is missing in production, this prevents Django from failing silently.
if not DATABASES['default']:
    raise Exception("DATABASE_URL environment variable is required when DEBUG is False.")


# Password validation... (No changes needed here)
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


# Internationalization... (No changes needed here)
LANGUAGE_CODE = 'en-us'
USE_I18N = True


# 🖼️ MEDIA FILES (User Uploads - CLOUDINARY) 🖼️
# ⭐️ ADDED: Cloudinary configuration for free, permanent media storage.
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# Tell Django to use Cloudinary for all user-uploaded files.
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = '/media/'
# MEDIA_ROOT is not strictly needed when using Cloudinary for storage.


# 📦 STATIC FILES (CSS, JavaScript) 📦
# Standard Django settings for static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ⭐️ ADDED: WhiteNoise Configuration for serving static files in production.
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

# Authentication settings... (No changes needed here)
LOGIN_URL = 'login' 
LOGIN_REDIRECT_URL = 'role_redirect'