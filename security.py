import random
import string
import setproctitle
from configuration import Configuration
from logging import Logger


class Security:
    def __init__(self, configuration: Configuration, logger: Logger):
        self.configuration = configuration
        self.logger = logger

    def randomize_process_name(self):
        random_name = "".join(random.choices(string.ascii_letters + string.digits, k=12))
        self.logger.info(f"Randomizing process name to {random_name}")
        setproctitle.setproctitle(random_name)
        return
