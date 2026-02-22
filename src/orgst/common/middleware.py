from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return self.get_response(request)

        if not getattr(user, "must_change_password", False):
            return self.get_response(request)

        # Só força dentro do admin.
        if not request.path.startswith("/admin/"):
            return self.get_response(request)

        force_url = reverse("admin_force_password_change")
        allowed = {
            force_url,
            reverse("admin:login"),
            reverse("admin:logout"),
        }

        if request.path not in allowed:
            return redirect(force_url)

        return self.get_response(request)


class DevCORSMiddleware:
    """Simple CORS middleware for local development."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = set(getattr(settings, "CORS_ALLOWED_ORIGINS", []))

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        origin = request.headers.get("Origin")
        if origin and origin in self.allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
            response["Vary"] = "Origin"

        return response
