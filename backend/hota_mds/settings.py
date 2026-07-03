import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-local-env")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "backoffice",
    "health",
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

ROOT_URLCONF = "hota_mds.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "hota_mds.wsgi.application"

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.mysql",
#         "NAME": os.getenv("MYSQL_DATABASE", "hota_mds"),
#         "USER": os.getenv("MYSQL_USER", "hota_user"),
#         "PASSWORD": os.getenv("MYSQL_PASSWORD", "hota_password"),
#         "HOST": os.getenv("MYSQL_HOST", "db"),
#         "PORT": os.getenv("MYSQL_PORT", "3306"),
#         "OPTIONS": {
#             "charset": "utf8mb4",
#         },
#     }
# }
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "mds-dev",
        "USER": "root",
        "PASSWORD": "123456",
        "HOST": "192.168.36.86",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 无本地快照时是否允许直连外部能耗库（False 则仅返回缓存，需定时任务 sync_energy_dashboard_snapshots）
ENERGY_DASHBOARD_ALLOW_LIVE_FALLBACK = os.getenv(
    "ENERGY_DASHBOARD_ALLOW_LIVE_FALLBACK", "true"
).lower() in ("1", "true", "yes")

# OPC UA 订阅制（大屏读缓存；管理端测试连接仍一次性直连）
# 发布间隔：OPC 服务器向客户端推送 DataChange 的批次间隔（非大屏轮询、非数据源 refresh_interval）
OPCUA_SUBSCRIPTION_PUBLISHING_MS = int(os.getenv("OPCUA_SUBSCRIPTION_PUBLISHING_MS", "500"))
OPCUA_SUBSCRIPTION_RECONNECT_SECONDS = int(os.getenv("OPCUA_SUBSCRIPTION_RECONNECT_SECONDS", "2"))
OPCUA_SUBSCRIPTION_RECONCILE_SECONDS = int(os.getenv("OPCUA_SUBSCRIPTION_RECONCILE_SECONDS", "30"))
OPCUA_SUBSCRIPTION_CLIENT_TIMEOUT_SECONDS = int(os.getenv("OPCUA_SUBSCRIPTION_CLIENT_TIMEOUT_SECONDS", "5"))
OPCUA_SUBSCRIPTION_OFFLINE_RETRY_SECONDS = float(os.getenv("OPCUA_SUBSCRIPTION_OFFLINE_RETRY_SECONDS", "2"))
# 大屏 HTTP 拉取实时监控 API 的间隔（读订阅缓存，不是 OPC 订阅读点周期）
OPCUA_SCREEN_POLL_SECONDS = int(os.getenv("OPCUA_SCREEN_POLL_SECONDS", "2"))
# 单 Subscription 内 MonitoredItem 上限（遇 BadTooManyMonitoredItems 可调小）
OPCUA_MAX_MONITORED_ITEMS_PER_SUBSCRIPTION = int(
    os.getenv("OPCUA_MAX_MONITORED_ITEMS_PER_SUBSCRIPTION", "32")
)
# 同一 OPC UA endpoint 跨数据源合并后的 MonitoredItem 总上限
OPCUA_MAX_MONITORED_ITEMS_PER_ENDPOINT = int(
    os.getenv("OPCUA_MAX_MONITORED_ITEMS_PER_ENDPOINT", "96")
)

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "hota_mds.exceptions.api_exception_handler",
}
