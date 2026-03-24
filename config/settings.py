import os
from pathlib import Path

from dotenv import load_dotenv
from config.secrets import get_secrets_manager

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Initialize secrets manager (Key Vault + environment variables)
secrets = get_secrets_manager(use_key_vault=not os.getenv("DISABLE_KEY_VAULT"))

SECRET_KEY = secrets.get("SECRET_KEY", default="django-insecure-local-dev-only")
DEBUG = secrets.get_bool("DEBUG", default=True)
ALLOWED_HOSTS = secrets.get_list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "users",
    "school",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": secrets.get("POSTGRES_DB", default="edusys"),
        "USER": secrets.get("POSTGRES_USER", default="edusys"),
        "PASSWORD": secrets.get("POSTGRES_PASSWORD", default="edusys"),
        "HOST": secrets.get("POSTGRES_HOST", default="db"),
        "PORT": secrets.get_int("POSTGRES_PORT", default=5432),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
LOGIN_URL = "login"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = secrets.get("EMAIL_HOST", default="mailhog")
EMAIL_PORT = secrets.get_int("EMAIL_PORT", default=1025)
EMAIL_USE_TLS = secrets.get_bool("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = secrets.get_bool("EMAIL_USE_SSL", default=False)
DEFAULT_FROM_EMAIL = secrets.get("DEFAULT_FROM_EMAIL", default="no-reply@edusys.local")
