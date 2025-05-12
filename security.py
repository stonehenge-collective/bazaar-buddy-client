import random
import string

from configuration import Configuration


class Security:
    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def randomize_process_name(self):
        random_name = "".join(random.choices(string.ascii_letters + string.digits, k=12))

        if self.configuration.operating_system == "Darwin":
            import ctypes

            libc = ctypes.CDLL("libc.dylib")
            libc.setprogname(random_name.encode())
        elif self.configuration.operating_system == "Windows":
            import ctypes

            ctypes.windll.kernel32.SetConsoleTitleW(random_name)
