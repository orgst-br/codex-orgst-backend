from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path

from apps.accounts.admin_views import AdminForcePasswordChangeView
from orgst.api.v1.router import api


def redirect_view(request):
    return redirect(settings.FRONTEND_HOME_URL, permanent=False)


urlpatterns = [
    path("", redirect_view),
    path("home/", redirect_view),
    path(
        "admin/force-password-change/",
        admin.site.admin_view(AdminForcePasswordChangeView.as_view()),
        name="admin_force_password_change",
    ),
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
