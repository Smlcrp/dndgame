"""Entry point — launches the D&D AI Dungeon Master via Electron + Flask.

Requires Node.js. If missing, attempts to install via winget automatically.
"""

import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
_ELECTRON_DIR = _ROOT / "electron"


def _find_npm():
    return shutil.which("npm") or shutil.which("npm.cmd")


def _install_node():
    """Try to install Node.js LTS via winget (Windows 11 built-in)."""
    winget = shutil.which("winget")
    if not winget:
        return False
    print("Installing Node.js LTS via winget...")
    r = subprocess.run(
        [winget, "install", "--id", "OpenJS.NodeJS.LTS",
         "--accept-package-agreements", "--accept-source-agreements"],
    )
    return r.returncode == 0


def _refresh_path():
    """Re-read PATH from the registry so npm is findable without a new shell."""
    import winreg
    paths = []
    for root, sub in [
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER,  r"Environment"),
    ]:
        try:
            with winreg.OpenKey(root, sub) as k:
                val, _ = winreg.QueryValueEx(k, "PATH")
                paths.append(val)
        except FileNotFoundError:
            pass
    import os
    os.environ["PATH"] = ";".join(paths) + ";" + os.environ.get("PATH", "")


def main():
    npm = _find_npm()

    if not npm:
        print("Node.js not found.")
        if sys.platform == "win32":
            if _install_node():
                _refresh_path()
                npm = _find_npm()

        if not npm:
            print(
                "\nERROR: Node.js is required to run this game.\n"
                "Download and install it from: https://nodejs.org/\n"
                "Then run 'python main.py' again.",
                file=sys.stderr,
            )
            sys.exit(1)

    node_modules = _ELECTRON_DIR / "node_modules"
    if not node_modules.exists():
        print("Installing Electron dependencies (first run — ~30 s)...")
        r = subprocess.run([npm, "install"], cwd=_ELECTRON_DIR)
        if r.returncode != 0:
            print("ERROR: npm install failed.", file=sys.stderr)
            sys.exit(1)

    print("Starting D&D AI Dungeon Master...")
    subprocess.run([npm, "start"], cwd=_ELECTRON_DIR)


if __name__ == "__main__":
    main()
