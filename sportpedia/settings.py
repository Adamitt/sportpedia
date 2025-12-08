"""
Django settings for sportpedia project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Media files (upload)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-kfq8bf45j2_@pwen@&kdmh9g@3)z6wlni4-fhg6e8p^8jx4bb&"

PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "ainur-fadhil-sportpedia.pbp.cs.ui.ac.id",
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # apps project-mu
    "landingpage",
    "gearguide",
    "sportlibrary",
    "profile_app",
    "accounts",
    "admin_sportpedia",
    "metrics",
    "videos",
    "sportforum",

    # third-party
    "corsheaders",
]

# URL login default Django (untuk decorator login_required, dll.)
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",          # harus di paling atas sebelum CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "landingpage.middleware.PageHitMiddleware",
]

ROOT_URLCONF = "sportpedia.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "sportpedia" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# view yang dilacak metric
TRACKED_VIEWS = {
    "sportlibrary:sport_detail",
    "gearguide:detail",
    "videos:detail",
    "forum:thread_detail",
}

WSGI_APPLICATION = "sportpedia.wsgi.application"

# Database
if PRODUCTION:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT"),
            "OPTIONS": {
                "options": f"-c search_path={os.getenv('SCHEMA', 'public')}",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"

# Folder tempat Django nyari file static (dev)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Folder tempat Django collectstatic pas deploy
STATIC_ROOT = BASE_DIR / "staticfiles"

# --------- CORS & CSRF untuk Flutter / front-end ----------

# CookieRequest pakai cookies (credentials: include)
CORS_ALLOW_CREDENTIALS = True

# Pakai regex supaya semua port localhost ke-cover (Flutter web sering ganti port)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
    r"^https://ainur-fadhil-sportpedia\.pbp\.cs\.ui\.ac\.id$",
]

# Origin yang dipercaya untuk CSRF (HTML form / API non-@csrf_exempt)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://ainur-fadhil-sportpedia.pbp.cs.ui.ac.id",
]

# Cookie settings (dev friendly)
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
