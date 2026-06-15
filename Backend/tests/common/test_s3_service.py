import io
import pytest
from unittest.mock import MagicMock, patch
from fastapi import UploadFile, HTTPException
from app.common.services.s3_service import S3Service

# Fixture to mock environment variables
@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_secret")
    monkeypatch.setenv("AWS_REGION", "test_region")
    monkeypatch.setenv("S3_BUCKET_NAME", "test_bucket")

# Test initialization
def test_s3_service_init(mock_env_vars):
    with patch("boto3.client") as mock_boto:
        service = S3Service()
        assert service.s3_client is not None
        mock_boto.assert_called_once_with(
            "s3",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="test_region"
        )

def test_s3_service_init_missing_env(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    service = S3Service()
    assert service.s3_client is None

# Test upload_file
def test_upload_file_success(mock_env_vars):
    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        service = S3Service()

        # Create a mock UploadFile
        file_content = b"fake image content"
        file = UploadFile(filename="test.jpg", file=io.BytesIO(file_content), headers={"content-type": "image/jpeg"})

        url = service.upload_file(file, folder="events")

        # Verify upload called
        mock_client.upload_fileobj.assert_called_once()
        args, kwargs = mock_client.upload_fileobj.call_args
        assert args[1] == "test_bucket"
        assert args[2].startswith("events/")
        assert args[2].endswith(".jpg")
        assert kwargs["ExtraArgs"]["ContentType"] == "image/jpeg"

        # Verify URL format
        expected_url_prefix = "https://test_bucket.s3.test_region.amazonaws.com/events/"
        assert url.startswith(expected_url_prefix)

def test_upload_file_invalid_extension(mock_env_vars):
    with patch("boto3.client"):
        service = S3Service()
        file = UploadFile(filename="test.txt", file=io.BytesIO(b""))
        
        with pytest.raises(HTTPException) as exc:
            service.upload_file(file)
        assert exc.value.status_code == 400
        assert "Invalid image format" in exc.value.detail

def test_upload_file_no_client(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    service = S3Service()
    file = UploadFile(filename="test.jpg", file=io.BytesIO(b""))
    
    with pytest.raises(HTTPException) as exc:
        service.upload_file(file)
    assert exc.value.status_code == 500
    assert "S3 configuration is missing" in exc.value.detail

# Test upload multiple
def test_upload_multiple_images(mock_env_vars):
    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        service = S3Service()

        # Create mock UploadFiles
        files = [
            UploadFile(filename="test1.jpg", file=io.BytesIO(b"content1"), headers={"content-type": "image/jpeg"}),
            UploadFile(filename="test2.png", file=io.BytesIO(b"content2"), headers={"content-type": "image/png"})
        ]

        # Since we can't easily change the behavior of the router here (it calls upload_file loop)
        # We will just verify upload_file works when called multiple times in sequence
        # mimicking the loop in the router
        
        url1 = service.upload_file(files[0], folder="events")
        url2 = service.upload_file(files[1], folder="events")

        assert mock_client.upload_fileobj.call_count == 2
        assert url1.startswith("https://test_bucket.s3.test_region.amazonaws.com/events/")
        assert url2.startswith("https://test_bucket.s3.test_region.amazonaws.com/events/")
        assert url1 != url2

# Test delete_file
def test_delete_file_success(mock_env_vars):
    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        service = S3Service()

        url = "https://test_bucket.s3.test_region.amazonaws.com/events/test.jpg"
        result = service.delete_file(url)

        assert result is True
        mock_client.delete_object.assert_called_once_with(
            Bucket="test_bucket",
            Key="events/test.jpg"
        )

def test_delete_file_invalid_url(mock_env_vars):
    with patch("boto3.client") as mock_boto:
        service = S3Service()
        result = service.delete_file("https://google.com/image.jpg")
        assert result is False

def test_delete_file_no_client(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    service = S3Service()
    result = service.delete_file("some_url")
    assert result is False
