import tempfile
from abc import ABC, abstractmethod
from json import JSONDecodeError
from pathlib import Path

from pydantic import ValidationError

from core.exceptions import RepositoryCorruptedError


class AbstractJsonRepository[T](ABC):
    DEFAULT_DATA_PATH = Path("~/.codescape/pyfolio")
    DEFAULT_JSON_FILE_NAME: Path

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    def __init__(self, json_path: Path | None = None) -> None:
        self.json_path = (
            (json_path if json_path is not None else self._get_default_json_path())
            .expanduser()
            .resolve()
        )
        self._cache: T | None = None
        self._is_dirty: bool = False

    def mark_dirty(self) -> None:
        self._is_dirty = True

    def commit(self) -> None:
        """Persist buffered changes to disk using an atomic write."""

        if not self._is_dirty or self._cache is None:
            return

        json_bytes = self._serialize(self._cache)
        self.json_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            "wb", dir=self.json_path.parent, delete=False
        ) as tmp_file:
            tmp_file.write(json_bytes)
            tmp_path = Path(tmp_file.name)

        tmp_path.replace(self.json_path)
        self._is_dirty = False

    @abstractmethod
    def _default_data(self) -> T:
        """Return the default empty data structure when file does not exist."""
        ...

    @abstractmethod
    def _serialize(self, data: T) -> bytes:
        """Convert in-memory data into formatted JSON bytes."""
        ...

    @abstractmethod
    def _deserialize(self, raw_bytes: bytes) -> T:
        """Convert raw JSON bytes into in-memory data structure."""
        ...

    def _get_data(self) -> T:
        """Lazy-load data from disk into memory cache on first access."""
        if self._cache is None:
            if self.json_path.exists():
                try:
                    raw_bytes = self.json_path.read_bytes()
                    self._cache = self._deserialize(raw_bytes)
                except (JSONDecodeError, ValueError, ValidationError) as err:
                    raise RepositoryCorruptedError(
                        f"Failed to parse repository file at '{self.json_path}': {err}"
                    ) from err
            else:
                self._cache = self._default_data()
        return self._cache

    def _get_default_json_path(self) -> Path:
        return self.DEFAULT_DATA_PATH / self.DEFAULT_JSON_FILE_NAME
