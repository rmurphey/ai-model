#!/usr/bin/env python3
"""
Version Management CLI
Utility for managing model versions in the AI Impact Analysis tool.
"""

import argparse
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.version import (
    get_current_version, get_current_version_string, 
    get_version_bump_instructions, VERSION_HISTORY
)


def show_current_version():
    """Display current version information"""
    version = get_current_version()
    version_str = get_current_version_string()
    
    print(f"Current Version: v{version_str}")
    print(f"Release Date: {VERSION_HISTORY.get(version_str, {}).get('release_date', 'Unknown')}")
    
    history_entry = VERSION_HISTORY.get(version_str, {})
    if history_entry.get('description'):
        print(f"Description: {history_entry['description']}")


def show_version_history():
    """Display version history"""
    print("Version History:")
    print("=" * 50)
    
    for version_str, info in VERSION_HISTORY.items():
        print(f"\nv{version_str} ({info.get('release_date', 'Unknown date')})")
        print(f"  {info.get('description', 'No description')}")
        
        if info.get('breaking_changes'):
            print("  Breaking Changes:")
            for change in info['breaking_changes']:
                print(f"    - {change}")
                
        if info.get('new_features'):
            print("  New Features:")
            for feature in info['new_features']:
                print(f"    - {feature}")


def show_bump_instructions(bump_type: str):
    """Show instructions for version bump"""
    try:
        instructions = get_version_bump_instructions(bump_type)
        print(instructions)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Manage versions for the AI Impact Analysis Model"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Current version command
    current_parser = subparsers.add_parser('current', help='Show current version')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show version history')
    
    # Bump command
    bump_parser = subparsers.add_parser('bump', help='Get instructions for version bump')
    bump_parser.add_argument(
        'type', 
        choices=['major', 'minor', 'patch'],
        help='Type of version bump'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'current':
        show_current_version()
    elif args.command == 'history':
        show_version_history()
    elif args.command == 'bump':
        show_bump_instructions(args.type)


if __name__ == '__main__':
    main()