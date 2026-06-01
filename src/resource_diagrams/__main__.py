"""
__main__.py
===========

Enables `python -m resource_diagrams` to invoke the CLI.

This is the thinnest possible shim (one import + call) so that the
installed console script, `python -m resource_diagrams`, and
`python -m resource_diagrams.cli` are all entry points to the same
minimal argparse wrapper.

See cli.py for the actual implementation and disclaimers.
"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    main()
