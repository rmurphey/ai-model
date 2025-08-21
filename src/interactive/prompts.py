"""
Terminal-based prompt utilities for interactive input.
Provides consistent UI elements and input validation.
"""

import sys
from typing import Any, List, Tuple, Optional, Union
import questionary
from questionary import Style
from ..utils.colors import *


def display_header(title: str):
    """Display a formatted header."""
    width = max(50, len(title) + 4)
    print("\n" + "=" * width)
    print(f"  {header(title)}")
    print("=" * width)


def display_info(message: str):
    """Display an informational message."""
    print(info(message))


def display_success(message: str):
    """Display a success message."""
    print(success(f"✓ {message}"))


def display_warning(message: str):
    """Display a warning message."""
    print(warning(f"⚠ {message}"))


def display_error(message: str):
    """Display an error message."""
    print(error(f"✗ {message}"))


def get_text_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Get text input from user with optional default.
    
    Args:
        prompt: The prompt to display
        default: Default value if user presses Enter
    
    Returns:
        User input or default value
    """
    try:
        # Try questionary first
        result = questionary.text(
            prompt,
            default=str(default) if default is not None else "",
            qmark=""
        ).ask()
        
        if result is None:  # User pressed Ctrl+C
            raise KeyboardInterrupt
        
        return result.strip() if result else (str(default) if default is not None else "")
    except (OSError, ValueError) as e:
        # Fallback to basic input if terminal not available
        if default:
            prompt_text = f"{prompt} [{default}]: "
        else:
            prompt_text = f"{prompt}: "
        
        response = input(prompt_text).strip()
        if not response and default is not None:
            return str(default)
        return response
    except KeyboardInterrupt:
        print("\n")
        raise


def get_numeric_input(
    prompt: str,
    default: Optional[float] = None,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    integer_only: bool = False
) -> float:
    """
    Get numeric input with validation.
    
    Args:
        prompt: The prompt to display
        default: Default value if user presses Enter
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value
        integer_only: Whether to require integer input
    
    Returns:
        Validated numeric value
    """
    # Build range hint
    range_hint = ""
    if min_val is not None and max_val is not None:
        range_hint = f" [{min_val}-{max_val}]"
    elif min_val is not None:
        range_hint = f" [min: {min_val}]"
    elif max_val is not None:
        range_hint = f" [max: {max_val}]"
    
    def validate_number(text):
        """Validate numeric input"""
        if not text and default is not None:
            return True
        try:
            value = float(text)
            
            # Check integer requirement
            if integer_only and value != int(value):
                return "Please enter a whole number"
            
            # Validate range
            if min_val is not None and value < min_val:
                return f"Value must be at least {min_val}"
            
            if max_val is not None and value > max_val:
                return f"Value must be at most {max_val}"
            
            return True
        except ValueError:
            return "Please enter a valid number"
    
    try:
        result = questionary.text(
            f"{prompt}{range_hint}",
            default=str(default) if default is not None else "",
            validate=validate_number,
            qmark=""
        ).ask()
        
        if result is None:  # User pressed Ctrl+C
            raise KeyboardInterrupt
        
        if not result and default is not None:
            value = float(default)
        else:
            value = float(result)
        
        return int(value) if integer_only else value
        
    except KeyboardInterrupt:
        print("\n")
        raise


def select_from_menu(
    prompt: str,
    options: List[Tuple[str, str]],
    allow_multiple: bool = False
) -> Union[str, List[str]]:
    """
    Display a menu and get user selection.
    
    Args:
        prompt: The prompt to display
        options: List of (value, description) tuples
        allow_multiple: Whether to allow multiple selections
    
    Returns:
        Selected value(s)
    """
    try:
        # Create choice list with descriptions
        choices = [desc for _, desc in options]
        
        if allow_multiple:
            # Use checkbox for multiple selection
            results = questionary.checkbox(
                prompt,
                choices=choices,
                qmark=""
            ).ask()
            
            if results is None:  # User pressed Ctrl+C
                raise KeyboardInterrupt
            
            # Map descriptions back to values
            selected_values = []
            for desc in results:
                for value, opt_desc in options:
                    if opt_desc == desc:
                        selected_values.append(value)
                        break
            return selected_values
        else:
            # Use select for single selection
            result = questionary.select(
                prompt,
                choices=choices,
                qmark=""
            ).ask()
            
            if result is None:  # User pressed Ctrl+C
                raise KeyboardInterrupt
            
            # Map description back to value
            for value, desc in options:
                if desc == result:
                    return value
            
            # Fallback to first option if somehow not found
            return options[0][0]
    except (OSError, ValueError):
        # Fallback to numbered menu if terminal not available
        print(f"\n{prompt}")
        for i, (value, desc) in enumerate(options, 1):
            print(f"  {i}. {desc}")
        
        while True:
            try:
                response = input("\nSelect [1]: ").strip() or "1"
                index = int(response) - 1
                if 0 <= index < len(options):
                    return options[index][0]
                else:
                    print(f"Please select a number between 1 and {len(options)}")
            except ValueError:
                print("Please enter a valid number")
    except KeyboardInterrupt:
        print("\n")
        raise


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Get yes/no confirmation from user.
    
    Args:
        prompt: The prompt to display
        default: Default value if user presses Enter
    
    Returns:
        True if confirmed, False otherwise
    """
    try:
        result = questionary.confirm(
            prompt,
            default=default,
            qmark=""
        ).ask()
        
        if result is None:  # User pressed Ctrl+C
            raise KeyboardInterrupt
        
        return result
    except (OSError, ValueError):
        # Fallback to basic input if terminal not available
        default_hint = "Y/n" if default else "y/N"
        
        while True:
            response = input(f"{prompt} [{default_hint}]: ").strip().lower()
            if not response:
                return default
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    except KeyboardInterrupt:
        print("\n")
        raise


def display_results_table(data: List[List[str]], headers: Optional[List[str]] = None):
    """
    Display data in a formatted table.
    
    Args:
        data: List of rows, each row is a list of values
        headers: Optional header row
    """
    if not data:
        return
    
    # Calculate column widths
    if headers:
        all_rows = [headers] + data
    else:
        all_rows = data
    
    col_widths = []
    for col_idx in range(len(all_rows[0])):
        max_width = max(len(str(row[col_idx])) for row in all_rows)
        col_widths.append(max_width)
    
    # Build separator line
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    
    # Display table
    print(separator)
    
    if headers:
        header_row = "|"
        for i, h in enumerate(headers):
            header_row += f" {header(str(h).ljust(col_widths[i]))} |"
        print(header_row)
        print(separator.replace("-", "="))
    
    for row in data:
        row_str = "|"
        for i, cell in enumerate(row):
            # Apply color formatting based on content
            cell_str = str(cell)
            if "$" in cell_str or "%" in cell_str:
                if cell_str.startswith("-"):
                    cell_str = cost(cell_str)
                else:
                    cell_str = value(cell_str)
            row_str += f" {cell_str.ljust(col_widths[i])} |"
        print(row_str)
    
    print(separator)


def display_progress(current: int, total: int, label: str = "Progress"):
    """
    Display a progress bar.
    
    Args:
        current: Current progress value
        total: Total value
        label: Label to display
    """
    percentage = (current / total) * 100 if total > 0 else 0
    bar_width = 40
    filled = int(bar_width * current / total) if total > 0 else 0
    
    bar = "█" * filled + "░" * (bar_width - filled)
    
    sys.stdout.write(f"\r{label}: [{bar}] {percentage:.1f}%")
    sys.stdout.flush()
    
    if current >= total:
        print()  # New line when complete


def clear_screen():
    """Clear the terminal screen."""
    import os
    os.system('clear' if os.name == 'posix' else 'cls')


def pause(message: str = "Press Enter to continue..."):
    """Pause execution until user presses Enter."""
    try:
        questionary.press_any_key_to_continue(message=dim_text(message)).ask()
    except KeyboardInterrupt:
        print("\n")
        raise


def display_sparkline(values: List[float], width: int = 20, label: Optional[str] = None):
    """
    Display a simple sparkline chart in the terminal.
    
    Args:
        values: List of numeric values
        width: Width of the sparkline
        label: Optional label
    """
    if not values:
        return
    
    # Normalize values to 0-7 range (8 block characters)
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val if max_val != min_val else 1
    
    blocks = " ▁▂▃▄▅▆▇█"
    
    # Sample or interpolate to fit width
    if len(values) > width:
        # Sample evenly
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        sampled = values
    
    # Convert to block characters
    sparkline = ""
    for val in sampled:
        normalized = (val - min_val) / range_val
        block_idx = int(normalized * 8)
        sparkline += blocks[min(block_idx, 8)]
    
    if label:
        print(f"{label}: {sparkline}")
    else:
        print(sparkline)


def display_comparison(
    name1: str, value1: Any,
    name2: str, value2: Any,
    format_as: str = "number"
):
    """
    Display a side-by-side comparison.
    
    Args:
        name1: First item name
        value1: First item value
        name2: Second item name
        value2: Second item value
        format_as: How to format values ("number", "currency", "percentage")
    """
    # Format values
    if format_as == "currency":
        str1 = f"${value1:,.0f}"
        str2 = f"${value2:,.0f}"
    elif format_as == "percentage":
        str1 = f"{value1:.1%}"
        str2 = f"{value2:.1%}"
    else:
        str1 = f"{value1:,.2f}" if isinstance(value1, float) else str(value1)
        str2 = f"{value2:,.2f}" if isinstance(value2, float) else str(value2)
    
    # Calculate difference
    try:
        diff = float(value2) - float(value1)
        diff_pct = (diff / float(value1)) * 100 if float(value1) != 0 else 0
        
        if diff > 0:
            diff_str = success(f"+{diff:,.0f} ({diff_pct:+.1f}%)")
        elif diff < 0:
            diff_str = cost(f"{diff:,.0f} ({diff_pct:+.1f}%)")
        else:
            diff_str = dim_text("No change")
    except (ValueError, TypeError):
        diff_str = dim_text("N/A")
    
    # Display comparison
    max_name_len = max(len(name1), len(name2))
    print(f"\n{name1.ljust(max_name_len)}: {metric(str1)}")
    print(f"{name2.ljust(max_name_len)}: {metric(str2)}")
    print(f"{'Difference'.ljust(max_name_len)}: {diff_str}")


def get_multiline_input(prompt: str, end_marker: str = "END") -> str:
    """
    Get multi-line input from user.
    
    Args:
        prompt: The prompt to display
        end_marker: String to end input (on its own line)
    
    Returns:
        Multi-line string
    """
    print(f"{prompt}")
    print(dim_text(f"(Enter '{end_marker}' on a new line to finish)"))
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == end_marker:
                break
            lines.append(line)
        except KeyboardInterrupt:
            print("\n")
            raise
        except EOFError:
            break
    
    return "\n".join(lines)