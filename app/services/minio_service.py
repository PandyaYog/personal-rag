from minio import Minio
from minio.error import S3Error
from app.core.config import settings

class MinioClient:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False  
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensures the configured bucket exists."""
        try:
            found = self.client.bucket_exists(self.bucket_name)
            if not found:
                self.client.make_bucket(self.bucket_name)
                print(f"Bucket '{self.bucket_name}' created.")
            else:
                print(f"Bucket '{self.bucket_name}' already exists.")
        except S3Error as exc:
            print("Error occurred during Minio initialization", exc)
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