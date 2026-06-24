"""Entry point — launches the desktop game."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from views.desktop.app import main

if __name__ == "__main__":
    main()
