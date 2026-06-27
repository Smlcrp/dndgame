"""Entry point — launches the D&D AI Dungeon Master via Electron + Flask.

Requires Node.js. If missing, attempts to install via winget automatically.
Flask is started here (correct Python guaranteed) before Electron opens.
"""

import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

_ROOT         = Path(__file__).parent
_ELECTRON_DIR = _ROOT / "electron"
_FLASK_PORT   = 5000
_PING_URL     = f"http://localhost:{_FLASK_PORT}/api/ping"

_NODE_COMMON_DIRS = [
    r"C:\Program Files\nodejs",
    r"C:\Program Files (x86)\nodejs",
]


def _find_npm():
    found = shutil.which("npm") or shutil.which("npm.cmd")
    if found:
        return found
    for d in _NODE_COMMON_DIRS:
        p = Path(d) / "npm.cmd"
        if p.exists():
            return str(p)
    return None


def _ensure_node_in_path(npm_path):
    import os
    node_dir = str(Path(npm_path).parent)
    if node_dir not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = node_dir + os.pathsep + os.environ.get("PATH", "")


def _install_node():
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
    import winreg, os
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
    os.environ["PATH"] = ";".join(paths) + ";" + os.environ.get("PATH", "")


def _flask_alive():
    try:
        urllib.request.urlopen(_PING_URL, timeout=1)
        return True
    except Exception:
        return False


def _start_flask():
    """Start Flask using the current Python interpreter. Returns the process."""
    proc = subprocess.Popen(
        [sys.executable, str(_ROOT / "run_server.py")],
        cwd=_ROOT,
    )
    print("Waiting for game server...", end="", flush=True)
    for _ in range(60):
        if _flask_alive():
            print(" ready.")
            return proc
        time.sleep(0.5)
        print(".", end="", flush=True)
    print()
    proc.terminate()
    return None


def _ensure_electron(npm):
    electron_bin = _ELECTRON_DIR / "node_modules" / "electron" / "dist" / "electron.exe"
    if electron_bin.exists():
        return True
    print("Installing Electron dependencies (first run — ~30 s)...")
    r = subprocess.run([npm, "install"], cwd=_ELECTRON_DIR)
    if r.returncode != 0:
        return False
    subprocess.run([npm, "approve-scripts", "electron"], cwd=_ELECTRON_DIR)
    subprocess.run([npm, "install"], cwd=_ELECTRON_DIR)
    return electron_bin.exists()


def main():
    # ── Find / install Node.js ────────────────────────────────────────────────
    npm = _find_npm()
    if not npm:
        print("Node.js not found.")
        if sys.platform == "win32" and _install_node():
            _refresh_path()
            npm = _find_npm()
    if not npm:
        print(
            "\nERROR: Node.js is required.\n"
            "Download from: https://nodejs.org/  then run main.py again.",
            file=sys.stderr,
        )
        sys.exit(1)

    _ensure_node_in_path(npm)

    if not _ensure_electron(npm):
        print("ERROR: Electron failed to install.", file=sys.stderr)
        sys.exit(1)

    # ── Start Flask (Python-side, no PATH guesswork) ──────────────────────────
    flask_proc = _start_flask()
    if flask_proc is None:
        print("ERROR: Game server failed to start.", file=sys.stderr)
        sys.exit(1)

    # ── Launch Electron (Flask already running) ───────────────────────────────
    print("Starting D&D AI Dungeon Master...")
    try:
        subprocess.run([npm, "start"], cwd=_ELECTRON_DIR)
    finally:
        flask_proc.terminate()


if __name__ == "__main__":
    main()
