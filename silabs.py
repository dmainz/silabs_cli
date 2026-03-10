#!/usr/bin/env python3
"""
Silabs CLI - Command-line interface for Simplicity Studio 6 development

Provides project creation, configuration, building, and flashing capabilities
through a unified command-line interface inspired by ESP-IDF's idf.py.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from silabs.commands import silabs


def main():
    """Main entry point"""
    try:
        silabs()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
