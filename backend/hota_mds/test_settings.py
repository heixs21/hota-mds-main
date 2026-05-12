from .settings import *  # noqa: F403,F401


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",  # noqa: F405
    }
}

# 避免测试跑 SQLite 时后台设备刷新线程与用例并发写库导致 table locked
DISABLE_DEVICE_RUNTIME_STATUS_REFRESH = True
# 测试环境不写 OPC 历史（减轻 SQLite 锁竞争；单测断言 OPC 调用仍正常）
OPCUA_HISTORY_DISABLED = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
