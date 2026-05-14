import sys
import signal
from pathlib import Path

# Add src to python path so we can import voicetype
sys.path.insert(0, str(Path(__file__).parent / "src"))

from voicetype.logger import setup_logging
from voicetype.gui import main

if __name__ == "__main__":
    # Allow Ctrl+C to exit the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    setup_logging()
    main()
