#!/usr/bin/env python3
"""
Interactive mode entry point for AI Impact Model.
Provides a guided, terminal-based interface for scenario creation and analysis.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.interactive.wizard import InteractiveWizard
from src.interactive.prompts import display_header, display_info, display_error


def main():
    """Main entry point for interactive mode."""
    try:
        # Initialize and run the wizard
        wizard = InteractiveWizard()
        wizard.run()
    except KeyboardInterrupt:
        print("\n")
        display_info("Session terminated by user.")
        sys.exit(0)
    except Exception as e:
        display_error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()