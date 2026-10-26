"""PyInstaller entry point (it needs a script, not a module)."""

import sys

from unmeta.__main__ import main

sys.exit(main())
