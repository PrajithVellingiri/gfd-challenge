import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.storage import storage_service

client = TestClient(app)


def test_storage_sanitize_filename():
    """
    Verifies that filenames are strictly sanitized against path traversal attempts.
    """
    assert storage_service.sanitize_filename("photo.jpg") == "photo.jpg"
    assert storage_service.sanitize_filename("../../etc/passwd") == "passwd"
    assert storage_service.sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert storage_service.sanitize_filename("my photo with spaces & symbols!.png") == "my_photo_with_spaces___symbols_.png"


def test_storage_generate_path():
    """
    Verifies structured path generation format: {user_id}/{request_id}/{sanitized_filename}
    """
    user_id = uuid.uuid4()
    request_id = uuid.uuid4()
    original_filename = "../../dangerous_file.mp3"

    path = storage_service.generate_storage_path(user_id, request_id, original_filename)
    expected_path = f"{user_id}/{request_id}/dangerous_file.mp3"
    assert path == expected_path


def test_storage_validate_owner():
    """
    Verifies user ownership check on storage paths.
    """
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    request_id = uuid.uuid4()

    valid_path = f"{user_id}/{request_id}/image.jpg"
    assert storage_service.validate_storage_path_owner(valid_path, user_id) is True
    assert storage_service.validate_storage_path_owner(valid_path, other_user_id) is False


def test_storage_bucket_resolution():
    """
    Verifies that image and audio file types resolve to citizen-images and citizen-audio buckets.
    """
    assert storage_service.get_bucket_for_type("image") == "citizen-images"
    assert storage_service.get_bucket_for_type("photo") == "citizen-images"
    assert storage_service.get_bucket_for_type("audio") == "citizen-audio"
    assert storage_service.get_bucket_for_type("voice") == "citizen-audio"

    with pytest.raises(ValueError):
        storage_service.get_bucket_for_type("executable")


def test_storage_path_endpoint():
    """
    Verifies POST /api/v1/requests/storage-path endpoint generates isolated upload parameters.
    """
    user_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())

    response = client.post("/api/v1/requests/storage-path", json={
        "user_id": user_id,
        "request_id": request_id,
        "bucket_type": "image",
        "original_filename": "pothole_evidence.jpg"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["bucket"] == "citizen-images"
    assert data["storage_path"] == f"{user_id}/{request_id}/pothole_evidence.jpg"
    assert "image/jpeg" in data["allowed_mime_types"]
    assert data["max_size_bytes"] == 10 * 1024 * 1024
