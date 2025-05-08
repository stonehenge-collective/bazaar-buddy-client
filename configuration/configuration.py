from pydantic import BaseModel
import json
import sys
import platform
from pathlib import Path

# Define SYSTEM_PATH based on whether we're running as a frozen executable or not
if getattr(sys, "frozen", False):
    # When frozen, we need to look in the _internal directory
    SYSTEM_PATH = Path(sys._MEIPASS).parent
else:
    SYSTEM_PATH = Path(__file__).parent.parent

OPERATING_SYSTEM = platform.system()

# true is we are running from source (i.e. python main.py)
IS_LOCAL = getattr(sys, "frozen", False) == False


class Configuration(BaseModel):
    """ "
    current_version: the version of the client that is currently running
    update_with_beta: if true, when updating the updater will download the latest beta release
    operating_system: the operating system of the host machine
    system_path: the path to the client (Path object)
    is_local: if true, the client is running from source
    """

    current_version: str
    update_with_beta: bool
    operating_system: str
    system_path: Path
    is_local: bool


def get_configuration() -> Configuration:
    with open(SYSTEM_PATH / "configuration" / "configuration.json", "r") as f:
        config = json.load(f)
        return Configuration(
            current_version=config["version"],
            update_with_beta=config["update_with_beta"],
            operating_system=OPERATING_SYSTEM,
            system_path=SYSTEM_PATH,
            is_local=IS_LOCAL,
        )


if __name__ == "__main__":
    config = get_configuration()
    print(config)
