from pydantic import BaseModel, model_validator
import json
import sys
import platform
from pathlib import Path
import os

GITHUB_BEARER_TOKEN = os.getenv("GITHUB_BEARER_TOKEN", None)


if getattr(sys, "frozen", False):
    SYSTEM_PATH = Path(sys._MEIPASS).parent
else:
    SYSTEM_PATH = Path(__file__).parent.parent

OPERATING_SYSTEM = platform.system()

# true is we are running from source (i.e. python main.py)
IS_LOCAL = getattr(sys, "frozen", False) == False


class Configuration(BaseModel):
    """Configuration model for Bazaar Buddy client.

    Attributes:
        current_version: The version of the client that is currently running.
        update_with_beta: If True, the updater will download the latest beta release.
        github_bearer_token: Bearer token for GitHub API access. Only used when update_with_beta is True.
            Required because GitHub's release API doesn't return beta releases without push access. Therefore, we must include a bearer token that grants this access.
        operating_system: The operating system of the host machine.
        system_path: Path object pointing to the client installation directory.
        is_local: True if the client is running from source code rather than a compiled executable.
    """

    current_version: str
    update_with_beta: bool
    github_bearer_token: str | None = None
    operating_system: str
    system_path: Path
    is_local: bool

    @model_validator(mode="after")
    def validate_github_bearer_token(self):
        if self.update_with_beta and not self.github_bearer_token:
            raise ValueError("github_bearer_token is required when update_with_beta is True")
        return self


def get_configuration() -> Configuration:

    if not IS_LOCAL and OPERATING_SYSTEM == "Darwin":
        """
        packaged as an app on macOS, the --add-data (in the build process)flag will add the configuration file to the Resources directory automatically. I guess this is standard behavior for macOS apps.
        """
        path = SYSTEM_PATH / "Resources" / "configuration" / "configuration.json"
    else:
        path = SYSTEM_PATH / "configuration" / "configuration.json"

    with open(path, "r") as f:
        config = json.load(f)
    return Configuration(
        current_version=config["version"],
        update_with_beta=config["update_with_beta"],
        github_bearer_token=GITHUB_BEARER_TOKEN,
        operating_system=OPERATING_SYSTEM,
        system_path=SYSTEM_PATH,
        is_local=IS_LOCAL,
    )


if __name__ == "__main__":
    config = get_configuration()
    print(config)
