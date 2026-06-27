"""Entry point — launches the D&D AI Dungeon Master (Electron + Flask)."""

import sys
import subprocess
from pathlib import Path

_electron_dir = Path(__file__).parent / "electron"


def main():
    if not _electron_dir.exists():
        print("ERROR: electron/ directory not found.", file=sys.stderr)
        sys.exit(1)

    if not (_electron_dir / "node_modules").exists():
        print("Installing Electron dependencies (first run — this takes ~30 s)...")
        r = subprocess.run(["npm", "install"], cwd=_electron_dir, shell=True)
        if r.returncode != 0:
            print(
                "ERROR: npm install failed.\n"
                "Make sure Node.js is installed: https://nodejs.org/",
                file=sys.stderr,
            )
            sys.exit(1)

    print("Starting D&D AI Dungeon Master...")
    subprocess.run(["npm", "start"], cwd=_electron_dir, shell=True)


if __name__ == "__main__":
    main()
