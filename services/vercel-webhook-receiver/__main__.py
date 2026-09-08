"""Run server from this package directory:

  python3 server.py --bind 127.0.0.1 --port 8080
  # or: python3 __main__.py …
"""

from __future__ import annotations

from server import main

if __name__ == "__main__":
    raise SystemExit(main())
