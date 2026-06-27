"""Entry point — launches the D&D AI Dungeon Master via Electron + Flask.

Requires Node.js. If missing, attempts to install via winget automatically.
"""

import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
_ELECTRON_DIR = _ROOT / "electron"


_NODE_COMMON_DIRS = [
    r"C:\Program Files\nodejs",
    r"C:\Program Files (x86)\nodejs",
]


def _find_npm():
    # Check PATH first, then common Windows install locations
    found = shutil.which("npm") or shutil.which("npm.cmd")
    if found:
        return found
    for d in _NODE_COMMON_DIRS:
        p = Path(d) / "npm.cmd"
        if p.exists():
            return str(p)
    return None


def _ensure_node_in_path(npm_path: str):
    """Make sure the Node.js directory is in PATH so 'node' resolves when Electron spawns."""
    import os
    node_dir = str(Path(npm_path).parent)
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    if node_dir not in path_dirs:
        os.environ["PATH"] = node_dir + os.pathsep + os.environ.get("PATH", "")


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

    _ensure_node_in_path(npm)

    electron_bin = _ELECTRON_DIR / "node_modules" / "electron" / "dist" / "electron.exe"
    if not electron_bin.exists():
        print("Installing Electron dependencies (first run — ~30 s)...")
        r = subprocess.run([npm, "install"], cwd=_ELECTRON_DIR)
        if r.returncode != 0:
            print("ERROR: npm install failed.", file=sys.stderr)
            sys.exit(1)
        # Approve electron's postinstall script (blocked by default in newer npm)
        subprocess.run([npm, "approve-scripts", "electron"], cwd=_ELECTRON_DIR)
        r2 = subprocess.run([npm, "install"], cwd=_ELECTRON_DIR)
        if r2.returncode != 0 or not electron_bin.exists():
            print("ERROR: Electron binary failed to download.", file=sys.stderr)
            sys.exit(1)

    import os
    os.environ["PYTHON_EXE"] = sys.executable  # tell Electron exactly which Python to use
    print("Starting D&D AI Dungeon Master...")
    subprocess.run([npm, "start"], cwd=_ELECTRON_DIR)


if __name__ == "__main__":
    main()
