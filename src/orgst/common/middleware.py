from django.conf import settings
from django.http import HttpResponse


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
