from permitflow.models import PermissionItem


def validate_prerequisites(item: PermissionItem, owned_permissions: set[str]) -> list[str]:
    return [name for name in item.prerequisites if name not in owned_permissions]
