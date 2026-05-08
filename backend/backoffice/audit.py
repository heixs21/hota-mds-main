from .models import OperationLog


SENSITIVE_CHANGE_KEYS = {
    "secretConfig",
    "secretSummary",
    "secretCiphertext",
    "secretEnvMapping",
}


def sanitize_change_summary(change_summary):
    if not isinstance(change_summary, dict):
        return change_summary

    sanitized = {}
    for key, value in change_summary.items():
        if key in SENSITIVE_CHANGE_KEYS:
            sanitized[key] = "[protected]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_change_summary(value)
        else:
            sanitized[key] = value

    return sanitized


def log_operation(actor, action, target_type, target_id="", target_label="", request=None, change_summary=None):
    OperationLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id or ""),
        target_label=target_label or "",
        request_method=(request.method if request else ""),
        request_path=(request.path if request else ""),
        change_summary=sanitize_change_summary(change_summary or {}),
    )
