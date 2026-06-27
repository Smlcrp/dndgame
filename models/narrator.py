"""Narrator — Kokoro ONNX TTS wrapper for voicing DM narration.

Voice: bm_george (deep British male) at 0.85x speed — closest local approximation
to the gravelly, authoritative tone of a fantasy narrator.

First call downloads model files (~90MB total, one-time) and loads them into
memory. Subsequent calls are fast (~0.5-2s per paragraph on CPU/GPU).
Thread-safe: the TTS lock ensures only one synthesis runs at a time.
"""

import io
import threading
import urllib.request
from pathlib import Path

import numpy as np

_kokoro = None
_lock   = threading.Lock()

_DATA_DIR = Path(__file__).parent.parent / "data" / "kokoro"

_RELEASE_BASE = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
)
_MODEL_FILES = [
    ("kokoro-v1.0.int8.onnx", "Kokoro model (int8, ~88 MB)"),
    ("voices-v1.0.bin",       "voice embeddings (~2 MB)"),
]

_DEFAULT_VOICE = "bm_george"
_SPEED         = 0.85


def _ensure_model_files():
    """Download Kokoro model files to data/kokoro/ if not already present."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    for filename, label in _MODEL_FILES:
        dest = _DATA_DIR / filename
        if not dest.exists():
            url = _RELEASE_BASE + filename
            print(f"[narrator] Downloading {label} …")
            urllib.request.urlretrieve(url, dest)
            print(f"[narrator] Saved → {dest}")


def _get_kokoro():
    """Return the Kokoro instance, loading + downloading on first call."""
    global _kokoro
    if _kokoro is not None:
        return _kokoro

    _ensure_model_files()

    from kokoro_onnx import Kokoro

    model_path  = str(_DATA_DIR / "kokoro-v1.0.int8.onnx")
    voices_path = str(_DATA_DIR / "voices-v1.0.bin")
    _kokoro = Kokoro(model_path, voices_path)
    return _kokoro


def speak(text: str, voice: str = _DEFAULT_VOICE, speed: float = _SPEED) -> bytes:
    """Convert text to WAV bytes using Kokoro TTS.

    Returns raw WAV bytes ready to serve as audio/wav.
    Blocks until synthesis completes. Thread-safe via internal lock.
    """
    import soundfile as sf

    with _lock:
        k = _get_kokoro()

        # Graceful fallback if the requested voice isn't in this model's voice set
        available = k.get_voices()
        if voice not in available:
            # Prefer any British male voice, then any male voice
            voice = (
                next((v for v in available if v.startswith("bm_")), None)
                or next((v for v in available if v.startswith("am_")), None)
                or available[0]
            )

        samples, sample_rate = k.create(text, voice=voice, speed=speed, lang="en-us")

    # Normalise to 16-bit PCM for broadest browser compatibility
    samples_16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    buf = io.BytesIO()
    sf.write(buf, samples_16, sample_rate, format="WAV")
    buf.seek(0)
    return buf.read()
