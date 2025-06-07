from abc import ABC, abstractmethod
from typing import Protocol, TypeVar, Generic, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime
import json
import os
from enum import Enum

from configuration import Configuration


class FileType(Enum):
    """Enumeration of supported file types."""

    CONFIG = "config"


class FileData(BaseModel):
    """Base class for all structured file data models."""

    class Config:
        # Allow serialization of datetime and other complex types
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ConfigData(FileData):
    """Structure for configuration file data."""

    user_preferences: Dict[str, Any] = {}
    app_settings: Dict[str, Any] = {}
    overlay_position: Optional[Dict[str, int]] = None  # {"x": int, "y": int, "width": int, "height": int}
    last_updated: datetime = datetime.now()

    def update_preference(self, key: str, value: Any):
        """Update a user preference."""
        self.user_preferences[key] = value
        self.last_updated = datetime.now()

    def update_setting(self, key: str, value: Any):
        """Update an app setting."""
        self.app_settings[key] = value
        self.last_updated = datetime.now()

    def update_overlay_position(self, x: int, y: int, width: int, height: int):
        self.overlay_position = {"x": x, "y": y, "width": width, "height": height}
        self.last_updated = datetime.now()


T = TypeVar("T", bound=FileData)


class FileWriterProtocol(Protocol[T]):
    """Protocol for file writers that handle specific data types."""

    def write(self, data: T) -> bool:
        """Write data to file."""
        ...

    def read(self) -> Optional[T]:
        """Read data from file."""
        ...

    def exists(self) -> bool:
        """Check if file exists."""
        ...

    def delete(self) -> bool:
        """Delete the file."""
        ...


class BaseFileWriter(ABC, Generic[T]):
    """Base abstract class for file writers."""

    def __init__(self, file_path: Path, data_class: type[T]):
        self.file_path = file_path
        self.data_class = data_class
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure the directory exists."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def write(self, data: T) -> bool:
        """Write data to file."""
        pass

    @abstractmethod
    def read(self) -> Optional[T]:
        """Read data from file."""
        pass

    def exists(self) -> bool:
        """Check if file exists."""
        return self.file_path.exists()

    def delete(self) -> bool:
        """Delete the file."""
        try:
            if self.exists():
                self.file_path.unlink()
            return True
        except Exception:
            return False


class BaseFileSystem(ABC):
    """Base abstract class for file system operations."""

    def __init__(self, base_path: Path, configuration: Configuration):
        self.base_path = base_path
        self.configuration = configuration
        self._ensure_base_directory()

        if self.configuration.operating_system == "Darwin":
            import fcntl

    def _ensure_base_directory(self):
        """Ensure the base directory exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_file_writer(self, file_type: FileType, filename: str) -> BaseFileWriter:
        """Get a file writer for the specified file type."""
        pass

    @abstractmethod
    def get_default_paths(self) -> Dict[FileType, Path]:
        """Get default file paths for each file type."""
        pass


class MacFileWriter(BaseFileWriter[T]):
    """Mac-specific file writer implementation."""

    def write(self, data: T) -> bool:
        import fcntl

        with open(f"{self.file_path}.lock", "w", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

            try:

                temp_path = self.file_path.with_suffix(self.file_path.suffix + ".tmp")

                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

                temp_path.rename(self.file_path)

                os.chmod(self.file_path, 0o600)

                return True
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                return False

    def read(self) -> Optional[T]:
        try:
            if not self.exists():
                return None

            with open(self.file_path, "r", encoding="utf-8") as f:
                data_dict = json.load(f)

            return self.data_class.model_validate(data_dict)
        except Exception:
            return None


class MacFileSystem(BaseFileSystem):
    """Mac-specific file system implementation."""

    def __init__(self, base_path: Path, configuration: Configuration):
        super().__init__(base_path, configuration)

    def get_default_paths(self) -> Dict[FileType, Path]:
        """Get Mac-appropriate default paths."""
        home = Path.home()
        app_support = home / "Library" / "Application Support" / "BazaarBuddy"

        return {
            FileType.CONFIG: app_support / "config.json",
        }

    def get_file_writer(self, file_type: FileType, filename: Optional[str] = None) -> BaseFileWriter:
        """Get a Mac file writer for the specified file type."""
        if filename:
            file_path = self.base_path / filename
        else:
            file_path = self.get_default_paths()[file_type]

        return MacFileWriter(file_path, ConfigData)


class WindowsFileWriter(BaseFileWriter[T]):
    """Windows-specific file writer implementation."""

    def write(self, data: T) -> bool:
        """Write data to file with Windows-specific optimizations."""
        try:
            # Use atomic write - write to temp file then replace
            temp_path = self.file_path.with_suffix(self.file_path.suffix + ".tmp")

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

            # Use os.replace for atomic replacement (handles existing files)
            os.replace(temp_path, self.file_path)

            return True
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False

    def read(self) -> Optional[T]:
        """Read data from file."""
        try:
            if not self.exists():
                return None

            with open(self.file_path, "r", encoding="utf-8") as f:
                data_dict = json.load(f)

            return self.data_class.model_validate(data_dict)
        except Exception:
            return None


class WindowsFileSystem(BaseFileSystem):
    """Windows-specific file system implementation."""

    def get_default_paths(self) -> Dict[FileType, Path]:
        """Get Windows-appropriate default paths."""
        home = Path.home()
        app_data = home / "AppData" / "Roaming" / "BazaarBuddy"

        return {
            FileType.CONFIG: app_data / "config.json",
        }

    def get_file_writer(self, file_type: FileType, filename: Optional[str] = None) -> BaseFileWriter:
        """Get a Windows file writer for the specified file type."""
        if filename:
            file_path = self.base_path / filename
        else:
            file_path = self.get_default_paths()[file_type]

        return WindowsFileWriter(file_path, ConfigData)
