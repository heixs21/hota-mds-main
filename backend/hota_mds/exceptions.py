from django.db.models.deletion import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _extract_message(detail):
    if isinstance(detail, list) and detail:
        return _extract_message(detail[0])
    if isinstance(detail, dict) and detail:
        first_value = next(iter(detail.values()))
        return _extract_message(first_value)
    return str(detail)


def _build_protected_error_message(protected_objects):
    model_hints = {
        "ProductionLine": "产线",
        "Device": "设备",
        "ScreenConfig": "大屏屏幕配置",
        "ScreenPageBinding": "大屏子页绑定",
        "Order": "订单",
        "Material": "物料",
    }
    hints = []
    seen = set()
    for obj in protected_objects:
        model_name = obj.__class__.__name__
        if model_name in model_hints and model_name not in seen:
            seen.add(model_name)
            hints.append(model_hints[model_name])
    if not hints:
        return "当前记录仍被其他数据引用，无法删除。请先解除关联后再试。"
    return f"当前记录仍被{'、'.join(hints)}引用，无法删除。请先解除关联后再试。"


def api_exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        labels = [str(obj) for obj in exc.protected_objects]
        return Response(
            {
                "success": False,
                "code": "CONFLICT",
                "message": _build_protected_error_message(exc.protected_objects),
                "data": {"protectedObjects": labels},
            },
            status=409,
        )

    response = exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data.get("detail", response.data)
    code = "ERROR"
    if response.status_code == 400:
        code = "INVALID_INPUT"
    elif response.status_code == 401:
        code = "UNAUTHORIZED"
    elif response.status_code == 403:
        code = "FORBIDDEN"
    elif response.status_code == 404:
        code = "NOT_FOUND"

    return Response(
        {
            "success": False,
            "code": code,
            "message": _extract_message(detail),
            "data": response.data,
        },
        status=response.status_code,
    )
