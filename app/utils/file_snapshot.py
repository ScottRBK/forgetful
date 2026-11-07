"""File activity snapshots omit binary payloads on every write surface."""
from app.models.file_models import File


def file_snapshot(file: File) -> dict:
    snapshot = file.model_dump(mode="json")
    snapshot.pop("data", None)
    return snapshot
