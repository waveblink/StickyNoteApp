"""Enable running `python -m aurora_notes`.

This simple wrapper imports and calls the package's GUI entry point.
"""

from .main import main

if __name__ == "__main__":
    main()
