import os
import sys
import subprocess

def install_requirements():
    # Check if tkinter is available
    try:
        import tkinter
    except ImportError:
        print("❌ Tkinter is not installed. Please install it manually.")
        print("👉 On Ubuntu/Debian: sudo apt install python3-tk")
        print("👉 On Arch: sudo pacman -S tk")
        print("👉 On Windows: reinstall Python from python.org with Tcl/Tk option enabled")
        return

    # Read requirements.txt ignoring "tk"
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_path):
        return

    with open(req_path, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("tk")]

    if not lines:
        return

    temp_path = os.path.join(os.path.dirname(__file__), "temp_requirements.txt")
    with open(temp_path, "w") as temp:
        temp.write("\n".join(lines))

    subprocess.run([sys.executable, "-m", "pip", "install", "-r", temp_path])
    os.remove(temp_path)

# Run installer
install_requirements()

# Launch app
from launcher import check_and_launch
check_and_launch()