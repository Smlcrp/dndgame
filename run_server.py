"""Launch the Flask web server for the D&D game (standalone / dev mode)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from views.web.api import app

if __name__ == "__main__":
    print("D&D Game Server — http://localhost:5000")
    print()
    app.run(debug=True, port=5000, use_reloader=False, threaded=True)
