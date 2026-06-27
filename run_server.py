"""
Launch the Flask web server for the D&D game.

Usage:
    python run_server.py

The Tkinter desktop app continues to work via:
    python main.py

Both can run at the same time — they share the same save files.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from views.web.api import app

if __name__ == "__main__":
    print("D&D Game — Web Server")
    print("  API health: http://localhost:5000/api/ping")
    print("  (Frontend not built yet — that's Stage 4b)")
    print()
    app.run(debug=True, port=5000, use_reloader=False, threaded=True)
