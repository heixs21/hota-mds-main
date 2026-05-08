from rest_framework.response import Response


def success_response(message, data, status_code=200):
    return Response(
        {
            "success": True,
            "code": "OK",
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def error_response(code, message, status_code):
    return Response(
        {
            "success": False,
            "code": code,
            "message": message,
            "data": None,
        },
        status=status_code,
    )
