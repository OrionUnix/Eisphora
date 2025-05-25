from pathlib import Path
import os
import sys
import environ
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import get_language
from .logging_config import setup_logging
from pathlib import Path
import shutil

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(os.path.dirname(__file__))

# Initialize django-environ: default DEBUG to True for development
env = environ.Env(
    DEBUG=(bool, True)
)
from django.core.exceptions import ImproperlyConfigured

# Check the environment variable first, otherwise try to detect it in the PATH
NPM_BIN_PATH = os.getenv("NPM_BIN_PATH_ENV") or shutil.which("npm")

if not NPM_BIN_PATH:
    raise ImproperlyConfigured(
        "npm was not found. Either install it, or define NPM_BIN_PATH_ENV in your .env."
    )

# Load .env from project root
env_file = BASE_DIR.parent / '.env'
if not env_file.exists():
    raise ImproperlyConfigured(f".env file not found at {env_file}")
# read_env will override os.environ
environ.Env.read_env(str(env_file))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=True)  

# Hosts configuration
# Provide sensible defaults for development
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "localhost") 
ALLOWED_HOSTS = [SITE_DOMAIN] if not DEBUG else ["localhost", "127.0.0.1"]
if not SITE_DOMAIN:
    raise ImproperlyConfigured("SITE_DOMAIN must be set in production.")
# security  setting
# # Cookies
CSRF_COOKIE_SECURE = not DEBUG  
SESSION_COOKIE_SECURE = not DEBUG  
SESSION_COOKIE_HTTPONLY = True  
CSRF_COOKIE_HTTPONLY = True  
SESSION_COOKIE_SAMESITE = "Lax"  # or "Strict" for more security
SESSION_COOKIE_AGE = 3600 if not DEBUG else 0

# 🔹 Sécurisation des connexions HTTPS
SECURE_SSL_REDIRECT = not DEBUG  
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG  
SECURE_HSTS_PRELOAD = not DEBUG  
# 🔹 Protection contre les attaques XSS et MIME sniffing
SECURE_BROWSER_XSS_FILTER = True  
SECURE_CONTENT_TYPE_NOSNIFF = True  
# CORS
CORS_ALLOW_ALL_ORIGINS = True 

# 🔹 Renforcement des en-têtes HTTP
SECURE_REFERRER_POLICY = "no-referrer"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_RESOURCE_POLICY = "same-origin"
# 🔹 Restriction du chargement de contenu non sécurisé
SECURE_CONTENT_SECURITY_POLICY = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'"

# 🔹 Désactivation du cache sur les pages sensibles
SECURE_CACHE_CONTROL = "no-store, no-cache, must-revalidate, max-age=0"

# 🔹 Gestion des logs en production
# setup_logging(BASE_DIR, debug=DEBUG)
if not DEBUG:
    setup_logging(BASE_DIR, debug=DEBUG) 
    def setup_logging(base_dir: Path, debug: bool = False):
        if debug:  # Évite l'activation en mode dev
            print("🛠 Mode développement détecté : logging désactivé.")
        return
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'tailwind',
    'theme',
    # 'two_factor', # django-two-factor-auth

]

# 🔹 Protection contre les erreurs en production
if not DEBUG:
    ADMINS_RAW = os.getenv("ADMIN_MAIL", "") 
    ADMINS = [tuple(admin.split(",")) for admin in ADMINS_RAW.split(";") if admin] 
    CURRENT_LANGUAGE = get_language() or "en"
    DEFAULT_ERROR_MESSAGE = {
        "en": os.getenv("ERROR_MESSAGE_EN", "An internal error has occurred."),
        "fr": os.getenv("ERROR_MESSAGE_FR", "Une erreur interne s'est produite."),
        "es": os.getenv("ERROR_MESSAGE_ES", "Se ha producido un error interno."),
    }.get(CURRENT_LANGUAGE, "An error occurred.")

TAILWIND_APP_NAME = 'theme'

#2FA
LOGIN_URL = 'two_factor:login' 
# TWO_FACTOR_PATCH_ADMIN = True # Pour sécuriser l'admin Django avec 2FA aussi

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.seo',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME').strip(),
        'USER': env('DB_USER').strip(),
        'PASSWORD': env('DB_PASSWORD').strip(),
        'HOST': env('DB_HOST').strip(),
        'PORT': env.int('DB_PORT'),
    }
}

required_db_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
missing_db_vars = [v for v in required_db_vars if not env.str(v, default=None)] 
if missing_db_vars:
    raise ImproperlyConfigured(
        f"Missing required database environment variables: {', '.join(missing_db_vars)}"
    )

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}}, 
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS configuration
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "localhost")  # Par défaut, localhost en développement

FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "")
if not FRONTEND_ORIGINS and not DEBUG:
    raise ImproperlyConfigured("FRONTEND_ORIGINS must be set in .env for production.")

CORS_ALLOWED_ORIGINS = FRONTEND_ORIGINS.split(";") if FRONTEND_ORIGINS else []
CORS_ALLOWED_ORIGIN_REGEXES = [fr"^https://\w+\.{SITE_DOMAIN.split('//')[-1]}$"]  # Génère la regex basée sur SITE_DOMAIN


if DEBUG and os.getenv("ENVIRONMENT") == "local":
    CORS_ALLOW_ALL_ORIGINS = False

 
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']

#users upload file
MEDIA_URL = '/media/' 
MEDIA_ROOT = BASE_DIR / 'mediafiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Mail config
# settings.py

# ... autres configurations ...
# DEBUG = env.bool("DEBUG", default=False) # Ceci lit la variable DEBUG de votre .env

# Configuration Email
if not DEBUG: 
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env.str('SMTP_HOST') 
    EMAIL_PORT = env.int('SMTP_PORT') 
    EMAIL_HOST_USER = env.str('SMTP_USER') 
    EMAIL_HOST_PASSWORD = env.str('SMTP_PASSWORD') 
    EMAIL_USE_TLS = env.bool('SMTP_USE_TLS', default=True) 
    EMAIL_USE_SSL = env.bool('SMTP_USE_SSL', default=False) 
    DEFAULT_FROM_EMAIL = env.str('SMTP_FROM', default=f'noreply@{SITE_DOMAIN}') 
    SERVER_EMAIL = env.str('SMTP_FROM', default=f'server-errors@{SITE_DOMAIN}') 
    ADMINS_EMAIL_STRING = env.str('ADMIN_MAIL', default='')
    if ADMINS_EMAIL_STRING:
        ADMINS = [('Admin', email.strip()) for email in ADMINS_EMAIL_STRING.split(';') if email.strip()]
    else:
        ADMINS = []

else: # DEBUG =True
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' 
    DEFAULT_FROM_EMAIL = f'console@{SITE_DOMAIN}'
    SERVER_EMAIL = f'console-server@{SITE_DOMAIN}'
    ADMINS = []
    print("🛠 Mode développement détecté : Emails redirigés vers la console.")

if not DEBUG:
    required_email_vars = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_FROM']
    missing_email_vars = [v for v in required_email_vars if not env.str(v, default=None)]
    if missing_email_vars:
        raise ImproperlyConfigured(
            f"Missing required email environment variables for production: {', '.join(missing_email_vars)}"
        )