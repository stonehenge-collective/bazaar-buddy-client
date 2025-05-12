import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE = Path(__file__).with_name("app.log")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 1️⃣  File handler – always safe
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
file_handler.setFormatter(fmt)
logger.addHandler(file_handler)

# 2️⃣  Console handler – only if stdout really exists
if sys.__stdout__ is not None:  # works when you build *without* --noconsole
    console_handler = logging.StreamHandler(stream=sys.__stdout__)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)


# 3️⃣  Helper that redirects print(...) to the logger
class LoggerWriter:
    def __init__(self, level):
        self.level = level

    def write(self, msg):
        msg = msg.rstrip("\n")
        if msg:
            logger.log(self.level, msg)

    def flush(self):  # required for file-like objects
        pass


# Redirect the high-level streams (safe even in windowed mode)
sys.stdout = LoggerWriter(logging.INFO)
sys.stderr = LoggerWriter(logging.ERROR)
