from django.contrib import admin
from django.urls import include, path

from accounts.views import admin_login, admin_logout, admin_me
from backoffice.views import LeftScreenDisplayView, RightScreenDisplayView
from backoffice.urls import urlpatterns as backoffice_urlpatterns
from health.views import health_check


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/admin/auth/login", admin_login, name="admin-login"),
    path("api/admin/auth/login/", admin_login, name="admin-login-slash"),
    path("api/admin/auth/logout", admin_logout, name="admin-logout"),
    path("api/admin/auth/logout/", admin_logout, name="admin-logout-slash"),
    path("api/admin/auth/me", admin_me, name="admin-me"),
    path("api/admin/auth/me/", admin_me, name="admin-me-slash"),
    path("api/admin/", include(backoffice_urlpatterns)),
    path("api/screens/<str:area_code>/left", LeftScreenDisplayView.as_view(), name="screen-left"),
    path("api/screens/<str:area_code>/left/", LeftScreenDisplayView.as_view(), name="screen-left-slash"),
    path("api/screens/<str:area_code>/right", RightScreenDisplayView.as_view(), name="screen-right"),
    path("api/screens/<str:area_code>/right/", RightScreenDisplayView.as_view(), name="screen-right-slash"),
    path("api/health", health_check, name="api-health"),
    path("api/health/", health_check, name="api-health-slash"),
]
