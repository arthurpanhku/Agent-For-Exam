"""OpenAPI schema customization."""
from fastapi.openapi.utils import get_openapi

from app.config import settings


def build_custom_openapi(app):
    """Attach global API key security when AFE_API_KEY is configured."""

    def openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        if settings.afe_api_key:
            openapi_schema.setdefault("components", {}).setdefault(
                "securitySchemes",
                {},
            )["ApiKeyAuth"] = {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Set AFE_API_KEY on the server and send the same value here.",
            }
            openapi_schema["security"] = [{"ApiKeyAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return openapi
