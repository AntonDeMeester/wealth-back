from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def create_custom_api(app: FastAPI):
    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="Custom title",
            version="2.5.0",
            description="This is a very custom OpenAPI schema",
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "in": "header",
                "description": "Add a JWT auth token to your request",
            }
        }
        openapi_schema["security"] = [{"bearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore
