from django.conf import settings
from django.http import HttpRequest, HttpResponse


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method == "OPTIONS":
            response = HttpResponse(status=200)
        else:
            response = self.get_response(request)

        origin = request.headers.get("Origin", "")
        allowed = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        
        # Cho phép các nguồn localhost khác nhau trong môi trường phát triển
        is_local = origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:")
        if origin in allowed or (settings.DEBUG and is_local):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken, Cookie"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"

        return response
