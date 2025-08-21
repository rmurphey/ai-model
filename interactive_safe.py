#!/usr/bin/env python3
"""
Safe wrapper for interactive mode that handles terminal detection issues.
Falls back to basic input when questionary can't work.
"""

import sys
import os

# Check if we have a proper terminal
def check_terminal():
    """Check if we're in a proper terminal environment."""
    try:
        # Check if stdin is a terminal
        if not sys.stdin.isatty():
            return False
        # Try to get terminal size
        import shutil
        cols, rows = shutil.get_terminal_size()
        return cols > 0 and rows > 0
    except:
        return False

# Set environment variable to help questionary
if not check_terminal():
    print("Note: Running in non-terminal mode. Using basic input prompts.")
    print("For better experience, run in a proper terminal.\n")
    # Force questionary to not use fancy terminal features
    os.environ['TERM'] = 'dumb'

# Now import and run the interactive module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.interactive.wizard import InteractiveWizard
from src.interactive.prompts import display_header, display_info, display_error

def main():
    """Main entry point for safe interactive mode."""
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
        print("\nTroubleshooting:")
        print("1. Try running with: python -u interactive_safe.py")
        print("2. Or use the test mode: python test_interactive.py")
        print("3. For SSH/remote: export TERM=xterm-256color")
        sys.exit(1)

if __name__ == "__main__":
    main()