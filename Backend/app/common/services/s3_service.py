import os
import uuid
import boto3
from fastapi import UploadFile, HTTPException
from botocore.exceptions import ClientError

class S3Service:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("AWS_REGION")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")

        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.region_name, self.bucket_name]):
            # If S3 is not configured, we might want to log a warning or fail
            # For now, we'll let it fail when methods are called if not initialized properly
            self.s3_client = None
        else:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            )

    def upload_file(self, file: UploadFile, folder: str = "events") -> str:
        if not self.s3_client:
             raise HTTPException(status_code=500, detail="S3 configuration is missing.")

        # Validate file extension
        filename = file.filename
        extension = filename.split(".")[-1].lower() if "." in filename else ""
        if extension not in ["jpg", "jpeg", "png", "webp"]:
             raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: jpg, jpeg, png, webp")

        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.{extension}"
        key = f"{folder}/{unique_filename}"

        try:
            # Upload file
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": file.content_type}
            )
            
            # Construct public URL
            url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{key}"
            return url

        except ClientError as e:
            print(f"S3 Upload Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload image to storage.")

    def delete_file(self, file_url: str) -> bool:
        if not self.s3_client:
             return False

        try:
            # Extract key from URL
            # Expected format: https://BUCKET.s3.REGION.amazonaws.com/KEY
            # Split by amazonaws.com/ to get the key
            if "amazonaws.com/" not in file_url:
                return False
            
            key = file_url.split("amazonaws.com/")[-1]
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            print(f"S3 Delete Error: {e}")
            return False

# Global instance
s3_service = S3Service()
