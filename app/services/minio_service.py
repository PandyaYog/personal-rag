from minio import Minio
from minio.error import S3Error
from app.core.config import settings

class MinioClient:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.R2_ENDPOINT,
            access_key=settings.R2_ACCESS_KEY,
            secret_key=settings.R2_SECRET_KEY,
            secure=True  # R2 requires HTTPS
        )
        self.bucket_name = settings.R2_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Verifies the configured bucket exists in Cloudflare R2."""
        try:
            found = self.client.bucket_exists(self.bucket_name)
            if not found:
                print(f"WARNING: Bucket '{self.bucket_name}' not found in R2. Please create it in the Cloudflare Dashboard.")
            else:
                print(f"Bucket '{self.bucket_name}' connection verified in R2.")
        except S3Error as exc:
            print("Error occurred during R2 Minio initialization", exc)
            raise

    def upload_file(self, file_path_in_minio: str, file_data, file_size: int, content_type: str):
        """Uploads a file-like object to Minio."""
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_path_in_minio,
                data=file_data,
                length=file_size,
                content_type=content_type
            )
            print(f"Successfully uploaded {file_path_in_minio} to bucket {self.bucket_name}.")
            return True
        except S3Error as exc:
            print(f"Error uploading file to Minio: {exc}")
            return False

    def get_object_file(self, file_path_in_minio: str):
        """Downloads a file from Minio."""
        try:
            response = self.client.get_object(self.bucket_name, file_path_in_minio)
            return response.read()
        except S3Error as exc:
            print(f"Error downloading file from Minio: {exc}")
            return None
        finally:
            if 'response' in locals() and response:
                response.close()
                response.release_conn()
                
    def download_file(self, file_path_in_minio: str):
        """Downloads a file from Minio."""
        try:
            response = self.client.get_object(self.bucket_name, file_path_in_minio)
            return response
        except S3Error as exc:
            print(f"Error downloading file from Minio: {exc}")
            return None
        finally:
            if 'response' in locals() and response:
                response.close()
                response.release_conn()
    
    def delete_file(self, file_path_in_minio: str):
        """Deletes a file from Minio."""
        try:
            self.client.remove_object(self.bucket_name, file_path_in_minio)
            print(f"Successfully deleted {file_path_in_minio} from bucket {self.bucket_name}.")
            return True
        except S3Error as exc:
            print(f"Error deleting file from Minio: {exc}")
            return False

minio_client = MinioClient()