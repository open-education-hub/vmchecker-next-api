import io
import hashlib
from abc import ABCMeta, abstractmethod
from pathlib import Path

from minio import Minio
from django.conf import settings
import urllib3


class Storage(metaclass=ABCMeta):
    @abstractmethod
    def put(self, data: bytes) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get(self, file_id: str) -> bytes:
        raise NotImplementedError()


class MinioStorage(Storage):
    def __init__(self) -> None:
        self._client = Minio(
            settings.MINIO_ADDRESS,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )

        if not self._client.bucket_exists(settings.MINIO_BUCKET):
            self._client.make_bucket(settings.MINIO_BUCKET)

    def put(self, data: bytes) -> str:
        file_id = hashlib.sha1(data).hexdigest()
        self._client.put_object(
            settings.MINIO_BUCKET,
            file_id,
            io.BytesIO(data),
            len(data),
            content_type="application/zip",
        )
        return file_id

    def get(self, file_id: str) -> bytes:
        try:
            data: urllib3.response.HTTPResponse = self._client.get_object(settings.MINIO_BUCKET, file_id)
            return data.data
        except:
            return b''
        finally:
            data.close()
            data.release_conn()


class OnDiskStorage(Storage):
    def __init__(self) -> None:
        super().__init__()
        self.data_dir = Path('/', 'tmp', 'data')
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes) -> str:
        file_id = hashlib.sha1(data).hexdigest()
        with open(self.data_dir / file_id, 'wb') as f:
            f.write(data)

        return file_id

    def get(self, file_id: str) -> bytes:
        with open(str(self.data_dir / file_id), 'rb') as f:
            return f.read()


storage: Storage = MinioStorage()
