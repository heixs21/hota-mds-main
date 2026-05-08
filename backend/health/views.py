from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    database_status = "ok"
    status_code = 200

    try:
        connection.ensure_connection()
    except Exception as exc:
        database_status = f"error: {exc.__class__.__name__}"
        status_code = 503

    return Response(
        {
            "success": database_status == "ok",
            "code": "OK" if database_status == "ok" else "DATABASE_UNAVAILABLE",
            "message": "healthy" if database_status == "ok" else "database unavailable",
            "data": {
                "service": "backend",
                "database": database_status,
            },
        },
        status=status_code,
    )
