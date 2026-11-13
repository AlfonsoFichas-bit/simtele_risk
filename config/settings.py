"""Django settings for the SIMTELE Risk starter.

The interesting part of this file is the bottom section: Inertia + Vite.
Everything above it is a fairly standard Django 6 configuration.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-simtele-risk-development-key-change-me",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Inertia server adapter
    "inertia",
    # Local app (also provides the {% vite_assets %} template tag)
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # Must run after sessions/auth/messages so shared data and flash
    # messages are available when the Inertia response is rendered.
    "inertia.middleware.InertiaMiddleware",
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


# Database

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

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Vite writes its build output to static/build. In production, collectstatic
# copies these files into STATIC_ROOT.
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Inertia + Vite
# ---------------------------------------------------------------------------

# The Django template that wraps the Inertia page. It only needs to expose
# {% block inertia %}{% endblock %}.
INERTIA_LAYOUT = "layout.html"

# Used by Inertia to detect stale assets and force a full reload. Set this to
# the release/build identifier in production.
INERTIA_VERSION = os.environ.get("INERTIA_VERSION", "1.0")

# Vite entrypoint, relative to BASE_DIR. It is the key used both by the dev
# server URL and by static/build/manifest.json.
VITE_ENTRY = "frontend/main.ts"

# Where `npm run dev` listens. The {% vite_assets %} tag points here while
# DEBUG is on; production reads the built manifest instead.
VITE_DEV_SERVER = os.environ.get("VITE_DEV_SERVER", "http://127.0.0.1:5173")
