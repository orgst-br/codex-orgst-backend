from pathlib import Path

import dj_database_url
import environ
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-secret-key-change-me")
DEBUG = env("DEBUG", default=True)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "ninja",
    # local apps
    "apps.accounts.apps.AccountsConfig",
    "apps.community.apps.CommunityConfig",
    "apps.docs.apps.DocsConfig",
    "apps.projects.apps.ProjectsConfig",
    "apps.boards.apps.BoardsConfig",
    "apps.tasks.apps.TasksConfig",
    "apps.kanban.apps.KanbanConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "orgst.common.middleware.DevCORSMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "orgst.common.middleware.ForcePasswordChangeMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]


ROOT_URLCONF = "orgst.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "orgst.wsgi.application"
ASGI_APPLICATION = "orgst.asgi.application"

default_sqlite_url = f"sqlite:///{BASE_DIR.parent / 'db.sqlite3'}"
DATABASE_URL = env("DATABASE_URL", default=default_sqlite_url)

db_config = dj_database_url.parse(
    DATABASE_URL,
    conn_max_age=600,
    ssl_require=False,
)

if db_config.get("ENGINE") == "django.db.backends.postgresql":
    db_config.setdefault("OPTIONS", {})

    # Só força SSL se explicitamente configurado
    if env.bool("DB_SSL_REQUIRE", default=False):
        db_config["OPTIONS"]["sslmode"] = "require"

DATABASES = {"default": db_config}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        )
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR.parent / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://127.0.0.1:3000"],
)
FRONTEND_HOME_URL = env(
    "FRONTEND_HOME_URL",
    default="http://localhost:3000/",
)

AUTH_USER_MODEL = "accounts.User"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.parent / "media"
