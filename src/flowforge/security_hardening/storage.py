from uuid import UUID


def tenant_blob_path(tenant_id: UUID, category: str, object_id: UUID, filename: str) -> str:
    category = category.replace("..", "").strip("/\\")
    filename = filename.replace("..", "").replace("/", "_").replace("\\", "_")
    if not category or not filename:
        raise ValueError("Invalid storage path")
    return f"tenants/{tenant_id}/{category}/{object_id}/{filename}"


def tenant_cache_key(tenant_id: UUID, resource_type: str, resource_id: str) -> str:
    return f"{tenant_id}:{resource_type}:{resource_id}"


def tenant_queue_key(tenant_id: UUID, queue_name: str) -> str:
    return f"{queue_name}:{tenant_id}"
