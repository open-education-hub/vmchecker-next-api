import hashlib
from pathlib import Path


class Storage():
    def put(self, data: bytes) -> str:
        raise NotImplementedError()

    def get(self, file_id: str) -> bytes:
        raise NotImplementedError()


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


storage: Storage = OnDiskStorage()
