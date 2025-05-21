from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from typing import Optional

import requests
from PyQt6.QtCore import QObject, pyqtSignal
import requests, tempfile, subprocess, sys
import subprocess
from PyQt6.QtWidgets import QApplication
import threading

from configuration import Configuration
from logging import Logger
from overlay import Overlay


# ───────────────────────────────────────────────────────────────
#  Update-source helpers (unchanged – included for completeness)
# ───────────────────────────────────────────────────────────────

class BaseUpdateSource(ABC):
    def __init__(self, logger: Logger):
        self.logger = logger
        self.latest_release: dict = self._get_latest_release()

    @abstractmethod
    def _get_latest_release(self) -> dict:  # pragma: no cover
        ...


class ProductionUpdateSource(BaseUpdateSource):
    def _get_latest_release(self) -> dict:
        response = requests.get(
            "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/releases/latest",
            timeout=30,
        )
        if response.status_code != 200:
            self.logger.error("Failed to get latest version from GitHub")
            raise RuntimeError("Failed to get latest version from GitHub")

        return response.json()


class TestUpdateSource(BaseUpdateSource):
    def __init__(self, logger: Logger, specific_version: Optional[str] = None):
        self._specific_version = specific_version
        super().__init__(logger)

    def _get_latest_release(self) -> dict:
        if self._specific_version:
            url = (
                "https://api.github.com/repos/stonehenge-collective/"
                f"bazaar-buddy-client-test/releases/{self._specific_version}"
            )
        else:
            url = (
                "https://api.github.com/repos/stonehenge-collective/"
                "bazaar-buddy-client-test/releases/latest"
            )

        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            self.logger.error("Failed to get latest version from GitHub")
            raise RuntimeError("Failed to get latest version from GitHub")

        return response.json()


# ───────────────────────────────────────────────────────────────
#                    Updater class hierarchy
# ───────────────────────────────────────────────────────────────

class MetaQObjectABC(type(QObject), ABCMeta): # type: ignore
    """Metaclass that inherits from both pyqtWrapperType and ABCMeta."""
    pass

class BaseUpdater(QObject, metaclass=MetaQObjectABC):
    """
    Houses every bit of behaviour that is **identical** across platforms.
    Concrete subclasses only implement :pymeth:`install_update()`.
    """

    update_completed = pyqtSignal()
    _ASSET_SUFFIX: str = "" # implemented by subclass

    def __init__(
        self,
        overlay: Overlay,
        logger: Logger,
        configuration: Configuration,
        latest_release: dict,
    ):
        super().__init__()
        self.overlay = overlay
        self.logger = logger
        self.configuration = configuration
        self.latest_release = latest_release
        self.thread_name = threading.current_thread().name

    # ───────────── public façade ─────────────

    def check_for_update(self) -> None:
        """Entry-point: determine whether to prompt and (possibly) update."""
        if self._update_available():
            self.logger.info(f"[{self.thread_name}] Update available")
            self._prompt_for_update()
        else:
            self.update_completed.emit()

    # ───────────── common helpers ─────────────

    def _update_available(self) -> bool:
        latest_version = self.latest_release.get("tag_name", "")
        if not latest_version:
            self.logger.error(f"[{self.thread_name}] Failed to get latest tag from GitHub API response")
            return False
        return self.configuration.current_version != latest_version

    def _prompt_for_update(self) -> None:
        """Display the Yes/No dialogue, wiring up handlers."""
        self.overlay.yes_clicked.connect(self._update_approved)
        self.overlay.no_clicked.connect(self._update_declined)

        if self.configuration.is_local:
            # Running from source – just tell the dev to git-pull.
            self.overlay.show_prompt_buttons(
                "A new version of Bazaar Buddy is available. "
                "Please pull the latest changes from the repository.",
                "Acknowledge",
            )
        else:
            self.overlay.show_prompt_buttons(
                f"Version {self.latest_release.get('tag_name')} of Bazaar Buddy "
                "is available. Would you like to update now?",
                "Update",
                "Not Now",
            )

    def _update_approved(self) -> None:
        self.overlay.yes_clicked.disconnect(self._update_approved)
        self.overlay.no_clicked.disconnect(self._update_declined)

        if self.configuration.is_local:
            self.logger.info(f"[{self.thread_name}] Running locally, skipping update")
            self.update_completed.emit()
            return

        self._download_and_install_update()
        self.update_completed.emit()

    def _update_declined(self) -> None:
        self.overlay.yes_clicked.disconnect(self._update_approved)
        self.overlay.no_clicked.disconnect(self._update_declined)
        self.update_completed.emit()

    def _download_asset(self, url: str) -> Path:
        """
        Stream the asset into a temporary file and return its path,
        updating the overlay with progress.
        """
        tmp_dir = Path(tempfile.mkdtemp(prefix="bb_update_"))
        target = tmp_dir / url.split("/")[-1]

        self.overlay.hide_prompt_buttons()
        self.overlay.set_message("Downloading update… 0 %")
        QApplication.processEvents()

        with requests.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            last_percent = -1

            with open(target, "wb") as fp:
                for chunk in resp.iter_content(chunk_size=8192):
                    if not chunk:   # keep-alive
                        continue
                    fp.write(chunk)
                    downloaded += len(chunk)

                    if total:
                        percent = int(downloaded * 100 / total)
                        if percent != last_percent:
                            last_percent = percent
                            self.overlay.set_message(
                                f"Downloading update… {percent} %"
                            )
                            QApplication.processEvents()

        # Guarantee a final 100 %
        self.overlay.set_message("Downloading update… 100 %")
        QApplication.processEvents()
        return target
    
    def _find_asset_url(self) -> Optional[str]:
        for asset in self.latest_release.get("assets", []):
            if asset.get("name", "").lower().endswith(self._ASSET_SUFFIX):
                return asset.get("browser_download_url")
        return None

    def _download_and_install_update(self) -> None:  # pragma: no cover
        """
        • Pick the correct release asset for the platform
        • Download it (using :py:meth:`_download_asset`)
        • Invoke the platform-specific helper script
        • Exit the running app (``sys.exit(0)``)
        """
        self.overlay.set_message("Downloading update…")
        QApplication.processEvents()

        download_url = self._find_asset_url()
        if not download_url:
            self.logger.error(f"[{self.thread_name}] No compatible package found, skipping update")
            self.overlay.set_message(
                "Update failed: no release package found. Skipping."
            )
            self.update_completed.emit()
            return

        self.logger.info(f"[{self.thread_name}] Downloading update from {download_url}")
        downloaded_exe_path = self._download_asset(download_url)
        self.overlay.set_message("Installing update…")
        QApplication.processEvents()

        self._install_update(downloaded_exe_path)

        sys.exit(0)

    @abstractmethod
    def _install_update(self,
        downloaded_exe_path: Path) -> None:
        ...

class WindowsUpdater(BaseUpdater):
    """Handles ``.exe`` assets and launches *windows_updater.bat*."""

    _ASSET_SUFFIX = ".exe"

    def _install_update(
        self,
        downloaded_exe_path: Path,
    ) -> None:
        """
        Replace a running PyInstaller one-file exe with an already-downloaded
        new build.

        Parameters
        ----------
        new_exe      Path to the *downloaded* (not-yet-running) executable.
        running_exe  Path to the *currently running* executable.
        attempts     How many times to retry the initial rename if something
                    (AV, backup, etc.) holds the file open without SHARE_DELETE.
        backoff      Seconds to wait between retries.

        Raises
        ------
        OSError if the swap cannot be completed (after rollback, the original exe
        is back in place).
        """
        downloaded_exe_path  =downloaded_exe_path.resolve()
        current_exe_path      = (self.configuration.executable_path / "BazaarBuddy.exe").resolve()
        bak_path     = current_exe_path.with_suffix(".bak")

        if not current_exe_path.is_file():
            raise FileNotFoundError(f"New exe not found: {current_exe_path}")

        os.replace(current_exe_path, bak_path)

        try:
            shutil.copy2(downloaded_exe_path, current_exe_path)
            env = os.environ.copy()
            env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
            subprocess.Popen([str(current_exe_path)], close_fds=True, env=env)
        except Exception as copy_error:
            try:
                os.replace(bak_path, current_exe_path)
            except Exception as restore_error:
                raise RuntimeError(
                    f"Copy failed ({copy_error}) and rollback failed ({restore_error}). "
                    "Application may not start."
                ) from restore_error
            raise copy_error         # propagate the original copy failure

        else:
            return
    


class MacUpdater(BaseUpdater):
    """Handles ``.zip`` assets and launches *mac_updater.sh*."""

    _ASSET_SUFFIX = ".zip"

    def _install_update(self, downloaded_exe_path: Path) -> None:
        updater_script = (
            self.configuration.system_path
            / "update_scripts"
            / "mac_updater.sh"
        )

        self.logger.info("Launching macOS updater: %s", updater_script)
        subprocess.Popen(
            [
                "bash",
                str(updater_script),
                str(downloaded_exe_path),
                str(self.configuration.executable_path.parent.parent),
            ]
        )
        return


class MockUpdater(BaseUpdater):
    """
    Drop-in stub that suppresses the entire auto-update flow.
    Useful for unit tests or debug builds.
    """

    def __init__(
        self,
        overlay: Overlay,
        logger: Logger,
        configuration: Configuration,
        latest_release: dict | None = None,
    ):
        # Pass an empty dict to satisfy the base class.
        super().__init__(overlay, logger, configuration, latest_release or {})

    # Override BOTH public entry-points so that nothing happens.
    def check_for_update(self) -> None:  # noqa: D401
        self.update_completed.emit()

    def _download_and_install_update(self) -> None:  # pragma: no cover
        pass
# ───────────────────────────────────────────────────────────────
#                       Example bootstrap
# ───────────────────────────────────────────────────────────────

if __name__ == "__main__":  # pragma: no cover
    from logger import logger

    cfg = Configuration()
    source = ProductionUpdateSource(logger)
    