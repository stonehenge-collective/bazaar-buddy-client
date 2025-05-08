import requests
from PyQt5.QtCore import QObject, pyqtSignal
import sys
import subprocess


class Updater(QObject):

    update_completed = pyqtSignal()

    def __init__(self, overlay, logger, config):
        super().__init__()
        self.overlay = overlay
        self.logger = logger
        self.config = config
        self.new_version = None

    def check_and_prompt(self):
        if self.check_for_updates():
            self.prompt_for_update()
        else:
            self.update_completed.emit()

    def check_for_updates(self):
        # get the latest version from github
        response = requests.get(
            "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/releases/latest"
        )
        latest_version = response.json().get("tag_name")
        if not latest_version:
            self.logger.error("Failed to get latest version from GitHub")
            return False
        if self.config.current_version == latest_version:
            return False
        self.new_version = latest_version
        return True

    def prompt_for_update(self):

        # Connect to signals
        self.overlay.yes_clicked.connect(self._update_approved)
        self.overlay.no_clicked.connect(self._update_declined)

        """
        if we are running Bazaar Buddy from source, we will show a different prompt as we do not want to install the
        executable. Instead we will tell the user to pull the latest changes from the
        Bazaar Buddy Repository.
        """
        if self.config.is_local:
            self.overlay.show_prompt_buttons(
                "There is a new version of Bazaar Buddy available. You should pull the latest changes from the Bazaar Buddy Repository.",
                "Acknowledge",
            )
            return

        # Show buttons
        self.overlay.show_prompt_buttons(
            f"Version {self.new_version} of Bazaar Buddy is available. Would you like to update now?",
            "Update",
            "Not Now",
        )
        return

    def _update_approved(self):
        self.overlay.yes_clicked.disconnect(self._update_approved)
        self.overlay.no_clicked.disconnect(self._update_declined)

        if self.config.is_local:
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

    def install_update(self):
        self.overlay.set_message("Installing update...")

        response = requests.get(
            "https://api.github.com/repos/stonehenge-collective/bazaar-buddy-client/releases/latest"
        )

        assets = response.json().get("assets", [])
        if not assets:
            self.overlay.set_message("Update failed: No release assets found")
            return False

        # Find executable for current platform
        download_url = None
        for asset in assets:
            name = asset.get("name", "").lower()
            print(f"Asset name: {name}")
            if (self.config.operating_system == "Windows" and name.endswith(".exe")) or (
                self.config.operating_system == "Darwin" and name.endswith(".zip")
            ):
                download_url = asset.get("browser_download_url")
                break

        if not download_url:
            self.overlay.set_message("Update failed: No compatible package found")
            return False
        # Launch platform-specific updater
        if self.config.operating_system == "Windows":
            updater_script = self.config.system_path / "update_scripts" / "windows_updater.bat"
            subprocess.Popen(["cmd", "/c", str(updater_script), download_url])
        else:  # macOS
            updater_script = self.config.system_path / "update_scripts" / "mac_updater.sh"
            subprocess.Popen(["bash", str(updater_script), download_url])

        sys.exit(0)
