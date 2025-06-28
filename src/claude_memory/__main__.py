"""
Entry point for running Claude Memory Server as a module.

Usage:
    python -m claude_memory
"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())