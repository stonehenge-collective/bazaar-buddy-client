from typing import Optional
from pydantic import BaseModel
import json
import sys
import platform
from pathlib import Path


class Configuration(BaseModel):
    """Runtime configuration for the Bazaar Buddy client.

    Instantiating ``Configuration()`` with no arguments will automatically load
    the values stored in ``configuration/configuration.json`` and augment them
    with information gathered at runtime (operating‑system, install path, and
    whether the program is running from source or a frozen binary).

    Keyword arguments can be supplied to override any of the auto‑detected or
    file‑based values – useful for testing.
    """

    current_version: str
    update_with_test_release: bool
    operating_system: str
    system_path: Path
    executable_path: Path
    is_local: bool
    save_images: bool
    target_test_release: Optional[str]

    def __init__(self):  # type: ignore[override]
        """Populate the model from disk and runtime context.

        Any keyword arguments provided will override the values discovered at
        runtime / loaded from JSON, allowing consumers to tweak selected fields
        as needed (e.g., in unit tests).
        """
        # ──────────────────────────────────────────────────────────────────────
        # Runtime‑derived information
        # ──────────────────────────────────────────────────────────────────────
        operating_system = platform.system()

        if getattr(sys, "frozen", False):
            # Running from a PyInstaller bundle
            system_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
            executable_path = Path(sys.executable).resolve().parent
        else:
            system_path = Path(__file__).parent
            executable_path = system_path

        is_local = not getattr(sys, "frozen", False)

        # ──────────────────────────────────────────────────────────────────────
        # Locate and load the JSON configuration file
        # ──────────────────────────────────────────────────────────────────────
        config_path = system_path / "configuration.json"

        try:
            with open(config_path, "r", encoding="utf-8") as fp:
                cfg = json.load(fp)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Configuration file not found at {config_path!s}.") from exc

        # ──────────────────────────────────────────────────────────────────────
        # Assemble the final data dictionary, giving priority to user‑supplied
        # overrides (``data``)
        # ──────────────────────────────────────────────────────────────────────
        auto_values = dict(
            current_version=cfg.get("version"),
            update_with_test_release=cfg.get("update_with_test_release", False),
            operating_system=operating_system,
            system_path=system_path,
            executable_path=executable_path,
            is_local=is_local,
            save_images=cfg.get("save_images", False),
            target_test_release=cfg.get("target_test_release", None)
        )

        super().__init__(**auto_values)


if __name__ == "__main__":
    # Creating an instance now automatically loads everything we need.
    config = Configuration()
    # Pretty‑print the resulting model for quick verification.
    print(config.model_dump_json(indent=2))
