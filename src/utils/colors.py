"""
Color utilities for console output formatting.
Provides colorful text output for terminal display.
"""

from colorama import Fore, Back, Style, init
import sys

# Initialize colorama for cross-platform support
init(autoreset=True)


class Colors:
    """ANSI color codes for terminal output"""
    
    # Foreground colors
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    BRIGHT_RED = Fore.LIGHTRED_EX
    BRIGHT_GREEN = Fore.LIGHTGREEN_EX
    BRIGHT_YELLOW = Fore.LIGHTYELLOW_EX
    BRIGHT_BLUE = Fore.LIGHTBLUE_EX
    BRIGHT_CYAN = Fore.LIGHTCYAN_EX
    
    # Styles
    BOLD = Style.BRIGHT
    DIM = Style.DIM
    RESET = Style.RESET_ALL


def colored_text(text: str, color: str = "", style: str = "") -> str:
    """Return colored text for terminal output"""
    return f"{style}{color}{text}{Colors.RESET}"


def success(text: str) -> str:
    """Green text for success messages"""
    return colored_text(text, Colors.BRIGHT_GREEN, Colors.BOLD)


def error(text: str) -> str:
    """Red text for error messages"""
    return colored_text(text, Colors.BRIGHT_RED, Colors.BOLD)


def warning(text: str) -> str:
    """Yellow text for warning messages"""
    return colored_text(text, Colors.BRIGHT_YELLOW, Colors.BOLD)


def info(text: str) -> str:
    """Blue text for info messages"""
    return colored_text(text, Colors.BRIGHT_BLUE, Colors.BOLD)


def header(text: str) -> str:
    """Cyan text for headers"""
    return colored_text(text, Colors.BRIGHT_CYAN, Colors.BOLD)


def money(text: str) -> str:
    """Green text for monetary values"""
    return colored_text(text, Colors.GREEN)


def percentage(text: str) -> str:
    """Yellow text for percentages"""
    return colored_text(text, Colors.YELLOW)


def metric(text: str) -> str:
    """White text for general metrics"""
    return colored_text(text, Colors.WHITE, Colors.BOLD)


def dim_text(text: str) -> str:
    """Dim text for less important info"""
    return colored_text(text, "", Colors.DIM)


def format_currency(value: float, positive_good: bool = True) -> str:
    """Format currency with appropriate colors"""
    if value >= 1e6:
        text = f"${value/1e6:.1f}M"
    elif value >= 1e3:
        text = f"${value/1e3:.0f}K"
    else:
        text = f"${value:.0f}"
    
    # Color based on value and context
    if positive_good:
        return success(text) if value > 0 else error(text)
    else:
        return error(text) if value > 0 else success(text)


def format_percentage(value: float, positive_good: bool = True) -> str:
    """Format percentage with appropriate colors"""
    text = f"{value*100:.1f}%"
    
    # Color based on value and context
    if positive_good:
        return success(text) if value > 0 else error(text)
    else:
        return error(text) if value > 0 else success(text)


def progress_bar(current: int, total: int, width: int = 30) -> str:
    """Create a colored progress bar"""
    progress = current / total
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    percentage = f"{progress*100:.1f}%"
    
    if progress < 0.5:
        color = Colors.RED
    elif progress < 0.8:
        color = Colors.YELLOW
    else:
        color = Colors.GREEN
    
    return f"{color}{bar}{Colors.RESET} {percentage}"


def section_divider(title: str, width: int = 60) -> str:
    """Create a colored section divider"""
    return header(f"\n{'='*width}\n{title.upper()}\n{'='*width}")


def subsection_divider(title: str, width: int = 60) -> str:
    """Create a colored subsection divider"""
    return info(f"\n{'-'*width}\n{title}\n{'-'*width}")


# Export common colors for backward compatibility
RED = Colors.RED
GREEN = Colors.GREEN
YELLOW = Colors.YELLOW
BLUE = Colors.BLUE
CYAN = Colors.CYAN
WHITE = Colors.WHITE
BOLD = Colors.BOLD
RESET = Colors.RESET