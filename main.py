#!/usr/bin/env python3
"""Điểm vào gốc: python main.py  hoặc  python -m chatbot_haui"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from chatbot_haui.cli import main

if __name__ == "__main__":
    main()
