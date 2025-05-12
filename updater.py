import requests
from PyQt5.QtCore import QObject, pyqtSignal
import sys
import subprocess
from abc import ABC, abstractmethod

from configuration import Configuration
from overlay import Overlay
from logging import Logger
import requests, shutil, tempfile, subprocess, sys, time, os
from pathlib import Path
from PyQt5.QtWidgets import QApplication

class BaseUpdateSource(ABC):

    def __init__(self, logger: Logger):
        self.logger = logger
        self.latest_release = self._get_latest_release()

    @abstractmethod
    def _get_latest_release(self) -> dict:
        raise NotImplementedError("function must be implemented by subclass")


class ProductionUpdateSource(BaseUpdateSource):
    def __init__(self, logger: Logger):
        super().__init__(logger)

    def _get_latest_release(self) -> dict:
        response = requests.get(
            "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/releases/latest"
        )
        if response.status_code != 200:
            self.logger.error("Failed to get latest version from GitHub")
            raise Exception("Failed to get latest version from GitHub")
        return response.json()


class TestUpdateSource(BaseUpdateSource):
    def __init__(self, logger: Logger):
        super().__init__(logger)

    def _get_latest_release(self) -> dict:
        response = requests.get(
            "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client-test/releases/latest"
        )
        if response.status_code != 200:
            self.logger.error("Failed to get latest version from GitHub")
            raise Exception("Failed to get latest version from GitHub")
        return response.json()


class MockUpdateSource(BaseUpdateSource):
    def __init__(self, logger: Logger):
        super().__init__(logger)

    def _get_latest_release(self) -> dict:
        return {
            "url": "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/releases/217663198",
            "assets_url": "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/releases/217663198/assets",
            "upload_url": "https://uploads.github.com/repos/stonehenge-collective/bazaar-buddy-client/releases/217663198/assets{?name,label}",
            "html_url": "https://github.com/stonehenge-collective/bazaar-buddy-client/releases/tag/v0.0.7",
            "id": 217663198,
            "author": {
                "login": "github-actions[bot]",
                "id": 41898282,
                "node_id": "MDM6Qm90NDE4OTgyODI=",
                "avatar_url": "https://avatars.githubusercontent.com/in/15368?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/github-actions%5Bbot%5D",
                "html_url": "https://github.com/apps/github-actions",
                "followers_url": "https://api.github.com/users/github-actions%5Bbot%5D/followers",
                "following_url": "https://api.github.com/users/github-actions%5Bbot%5D/following{/other_user}",
                "gists_url": "https://api.github.com/users/github-actions%5Bbot%5D/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/github-actions%5Bbot%5D/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/github-actions%5Bbot%5D/subscriptions",
                "organizations_url": "https://api.github.com/users/github-actions%5Bbot%5D/orgs",
                "repos_url": "https://api.github.com/users/github-actions%5Bbot%5D/repos",
                "events_url": "https://api.github.com/users/github-actions%5Bbot%5D/events{/privacy}",
                "received_events_url": "https://api.github.com/users/github-actions%5Bbot%5D/received_events",
                "type": "Bot",
                "user_view_type": "public",
                "site_admin": False,
            },
            "node_id": "RE_kwDOOiDlvc4M-Ube",
            "tag_name": "v0.0.7",
            "target_commitish": "main",
            "name": "Release v0.0.7",
            "draft": False,
            "prerelease": False,
            "created_at": "2025-05-09T17:40:26Z",
            "published_at": "2025-05-09T17:41:49Z",
            "assets": [
                {
                    "url": "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/releases/assets/253262650",
                    "id": 253262650,
                    "node_id": "RA_kwDOOiDlvc4PGHs6",
                    "name": "BazaarBuddy-mac.zip",
                    "label": "",
                    "uploader": {
                        "login": "github-actions[bot]",
                        "id": 41898282,
                        "node_id": "MDM6Qm90NDE4OTgyODI=",
                        "avatar_url": "https://avatars.githubusercontent.com/in/15368?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/github-actions%5Bbot%5D",
                        "html_url": "https://github.com/apps/github-actions",
                        "followers_url": "https://api.github.com/users/github-actions%5Bbot%5D/followers",
                        "following_url": "https://api.github.com/users/github-actions%5Bbot%5D/following{/other_user}",
                        "gists_url": "https://api.github.com/users/github-actions%5Bbot%5D/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/github-actions%5Bbot%5D/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/github-actions%5Bbot%5D/subscriptions",
                        "organizations_url": "https://api.github.com/users/github-actions%5Bbot%5D/orgs",
                        "repos_url": "https://api.github.com/users/github-actions%5Bbot%5D/repos",
                        "events_url": "https://api.github.com/users/github-actions%5Bbot%5D/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/github-actions%5Bbot%5D/received_events",
                        "type": "Bot",
                        "user_view_type": "public",
                        "site_admin": False,
                    },
                    "content_type": "application/zip",
                    "state": "uploaded",
                    "size": 46463847,
                    "download_count": 0,
                    "created_at": "2025-05-09T17:41:50Z",
                    "updated_at": "2025-05-09T17:41:52Z",
                    "browser_download_url": "https://github.com/stonehenge-collective/bazaar-buddy-client/releases/download/v0.0.7/BazaarBuddy-mac.zip",
                },
                {
                    "url": "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/releases/assets/253262805",
                    "id": 253262805,
                    "node_id": "RA_kwDOOiDlvc4PGHvV",
                    "name": "BazaarBuddy.exe",
                    "label": "",
                    "uploader": {
                        "login": "github-actions[bot]",
                        "id": 41898282,
                        "node_id": "MDM6Qm90NDE4OTgyODI=",
                        "avatar_url": "https://avatars.githubusercontent.com/in/15368?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/github-actions%5Bbot%5D",
                        "html_url": "https://github.com/apps/github-actions",
                        "followers_url": "https://api.github.com/users/github-actions%5Bbot%5D/followers",
                        "following_url": "https://api.github.com/users/github-actions%5Bbot%5D/following{/other_user}",
                        "gists_url": "https://api.github.com/users/github-actions%5Bbot%5D/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/github-actions%5Bbot%5D/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/github-actions%5Bbot%5D/subscriptions",
                        "organizations_url": "https://api.github.com/users/github-actions%5Bbot%5D/orgs",
                        "repos_url": "https://api.github.com/users/github-actions%5Bbot%5D/repos",
                        "events_url": "https://api.github.com/users/github-actions%5Bbot%5D/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/github-actions%5Bbot%5D/received_events",
                        "type": "Bot",
                        "user_view_type": "public",
                        "site_admin": False,
                    },
                    "content_type": "application/octet-stream",
                    "state": "uploaded",
                    "size": 158826459,
                    "download_count": 5,
                    "created_at": "2025-05-09T17:43:28Z",
                    "updated_at": "2025-05-09T17:43:33Z",
                    "browser_download_url": "https://github.com/stonehenge-collective/bazaar-buddy-client/releases/download/v0.0.7/BazaarBuddy.exe",
                },
            ],
            "tarball_url": "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/tarball/v0.0.7",
            "zipball_url": "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/zipball/v0.0.7",
            "body": "",
        }


class BaseUpdater(QObject):

    update_completed = pyqtSignal()

    def __init__(self):
        super().__init__()

    def check_for_update(self):
        raise NotImplementedError("function must be implemented by subclass")


class Updater(BaseUpdater):

    def __init__(self, overlay: Overlay, logger: Logger, configuration: Configuration, latest_release: dict):
        super().__init__()
        self.overlay = overlay
        self.logger = logger
        self.configuration = configuration
        self.latest_release = latest_release

    def check_for_update(self):
        if self._update_available():
            self.logger.info("Update available")
            self.prompt_for_update()
        else:
            self.update_completed.emit()

    def _update_available(self):
        latest_version = self.latest_release.get("tag_name", "")
        if not latest_version:
            self.logger.error("Failed to get latest tag from GitHub API response")
            return False
        if self.configuration.current_version == latest_version:
            return False
        return True

    def prompt_for_update(self):

        self.overlay.yes_clicked.connect(self._update_approved)
        self.overlay.no_clicked.connect(self._update_declined)

        """
        if we are running Bazaar Buddy from source, we will show a different prompt as we do not want to install the
        executable. Instead we will tell the user to pull the latest changes from the
        Bazaar Buddy Repository.
        """
        if self.configuration.is_local:
            self.overlay.show_prompt_buttons(
                "There is a new version of Bazaar Buddy available. You should pull the latest changes from the Bazaar Buddy Repository.",
                "Acknowledge",
            )
        else:
            self.overlay.show_prompt_buttons(
                f"Version {self.latest_release.get('tag_name')} of Bazaar Buddy is available. Would you like to update now?",
                "Update",
                "Not Now",
            )

    def _update_approved(self):
        self.overlay.yes_clicked.disconnect(self._update_approved)
        self.overlay.no_clicked.disconnect(self._update_declined)

        if self.configuration.is_local:
            self.logger.info("Running locally, skipping update")
            self.update_completed.emit()
            return
        else:
            self.install_update()
            self.update_completed.emit()

    def _update_declined(self):
        self.overlay.yes_clicked.disconnect(self._update_approved)
        self.overlay.no_clicked.disconnect(self._update_declined)
        self.update_completed.emit()

    def download_asset(self, url: str) -> Path:
        """
        Stream the asset to a temp file and return its path, emitting
        progress (%) to the overlay as we go.
        """
        tmp_dir = Path(tempfile.mkdtemp(prefix="bb_update_"))
        target = tmp_dir / url.split("/")[-1]

        self.overlay.set_message("Downloading update… 0 %")
        QApplication.processEvents()

        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            last_percent = -1

            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:        # keep‑alive
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total:            # avoid div‑by‑zero
                        percent = int(downloaded * 100 / total)
                        if percent != last_percent:
                            last_percent = percent
                            self.overlay.set_message(f"Downloading update… {percent} %")
                            QApplication.processEvents()

        # guarantee a final 100 %
        self.overlay.set_message("Downloading update… 100 %")
        QApplication.processEvents()
        return target
      
    def install_update(self):
        self.overlay.set_message("Downloading update…")
        QApplication.processEvents()

        assets = self.latest_release.get("assets", [])
        if not assets:
            self.logger.error("No release assets found, skipping update")
            self.overlay.set_message("Update failed: No release assets found. Skipping update.")
            self.update_completed.emit()
            return

        # Find executable for current platform
        download_url = None
        for asset in assets:
            name = asset.get("name", "").lower()
            print(f"Asset name: {name}")
            if (self.configuration.operating_system == "Windows" and name.endswith(".exe")) or (
                self.configuration.operating_system == "Darwin" and name.endswith(".zip")
            ):
                download_url = asset.get("browser_download_url")
                break

        if not download_url:
            self.logger.error("No compatible package found, skipping update")
            self.overlay.set_message("Update failed: No compatible package found. Skipping update.")
            self.update_completed.emit()
            return

        self.logger.info(f"Downloading update from {download_url}")
        
        local_download_location = self.download_asset(download_url)
        self.overlay.set_message("Installing update…")
        QApplication.processEvents()
        # Launch platform-specific updater
        if self.configuration.operating_system == "Windows":
            updater_script = self.configuration.system_path / "update_scripts" / "windows_updater.bat"
            subprocess.Popen([
                "cmd", "/c", str(updater_script),
                str(local_download_location),
                str(self.configuration.executable_path)   # install dir
            ])
        else:  # macOS
            updater_script = self.configuration.system_path / "update_scripts" / "mac_updater.sh"
            subprocess.Popen(
                ["bash", str(updater_script), download_url, str(self.configuration.system_path.parent.parent)]
            )

        sys.exit(0)


class MockUpdater(BaseUpdater):
    """
    This class can be used to skip the entire auto updating flow.
    """

    def __init__(self, overlay: Overlay, logger: Logger, configuration: Configuration, latest_release: dict):
        super().__init__()

    def check_and_prompt(self):
        self.update_completed.emit()

if __name__ == "__main__":  # pragma: no cover
    from logger import logger

    cfg = Configuration()
    updater = Updater()