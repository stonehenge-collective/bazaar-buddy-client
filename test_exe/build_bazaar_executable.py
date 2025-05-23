import os
import platform
import subprocess
import sys

def build_executable():
    system = platform.system()
    script_path = os.path.join("bazaar_executable.py")

    if not os.path.exists(script_path):
        print("Error: bazaar_executable.py not found.")
        return

    if system == "Darwin":
        # macOS
        add_data = "images:images"
        exe_name = "The Bazaar"
    elif system == "Windows":
        # Windows
        add_data = "images;images"
        exe_name = "TheBazaar.exe"
    else:
        print(f"Unsupported OS: {system}")
        return

    command = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={exe_name}",
        f"--add-data={add_data}",
        script_path,
    ]

    print("Running PyInstaller command:")
    print(" ".join(command))

    subprocess.run(command, check=True)

if __name__ == "__main__":
    try:
        build_executable()
    except subprocess.CalledProcessError as e:
        print("Build failed:", e)
        sys.exit(1)
