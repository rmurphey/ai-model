#!/usr/bin/env python3
"""
Constraint validation CLI for AI impact model.
Validates scenarios against business constraints and provides recommendations.
"""

import argparse
import sys
from pathlib import Path
from tabulate import tabulate

from src.constraints import ConstraintValidator, ValidationStatus
from src.scenarios.scenario_loader import ScenarioLoader
from src.utils.exceptions import ConfigurationError

# Import colors
try:
    from src.utils.colors import *
except ImportError:
    # Fallback if colors module has issues
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'


def validate_single_scenario(validator: ConstraintValidator, 
                            scenario_name: str, 
                            scenario_file: str = "src/scenarios") -> int:
    """
    Validate a single scenario.
    
    Args:
        validator: Constraint validator instance
        scenario_name: Name of scenario to validate
        scenario_file: Path to scenarios
        
    Returns:
        Exit code (0 for success, 1 for warnings, 2 for violations)
    """
    try:
        loader = ScenarioLoader(scenario_file)
        scenarios = loader.load_all_scenarios()
        
        if scenario_name not in scenarios:
            print(f"{RED}Error: Scenario '{scenario_name}' not found{RESET}")
            print(f"\nAvailable scenarios:")
            for name in scenarios.keys():
                print(f"  • {name}")
            return 2
        
        scenario_data = scenarios[scenario_name]
        result = validator.validate_scenario(scenario_data, scenario_name)
        
        # Display results
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}CONSTRAINT VALIDATION: {scenario_name}{RESET}")
        print(f"{CYAN}{'='*60}{RESET}\n")
        
        # Status with color
        if result.status == ValidationStatus.VALID:
            status_color = GREEN
            status_icon = "✓"
        elif result.status == ValidationStatus.WARNING:
            status_color = YELLOW
            status_icon = "⚠"
        else:
            status_color = RED
            status_icon = "✗"
        
        print(f"Status: {status_color}{status_icon} {result.status.value.upper()}{RESET}\n")
        
        # Parameters checked
        if result.parameters_checked:
            print(f"{BOLD}Parameters Checked:{RESET}")
            param_table = []
            for param, value in result.parameters_checked.items():
                if isinstance(value, float) and value < 1:
                    display_value = f"{value:.1%}"
                elif param.endswith('_month') or param.startswith('cost'):
                    display_value = f"${value:.0f}"
                else:
                    display_value = f"{value:.1f}" if isinstance(value, float) else str(value)
                param_table.append([param.replace('_', ' ').title(), display_value])
            
            print(tabulate(param_table, headers=['Parameter', 'Value'], tablefmt='simple'))
            print()
        
        # Violations
        if result.violations:
            print(f"{RED}{BOLD}VIOLATIONS:{RESET}")
            for violation in result.violations:
                print(f"  {RED}✗{RESET} {violation}")
            print()
        
        # Warnings
        if result.warnings:
            print(f"{YELLOW}{BOLD}WARNINGS:{RESET}")
            for warning in result.warnings:
                print(f"  {YELLOW}⚠{RESET} {warning}")
            print()
        
        # Suggestions
        if result.suggestions:
            print(f"{CYAN}{BOLD}SUGGESTIONS:{RESET}")
            for suggestion in result.suggestions:
                print(f"  {CYAN}→{RESET} {suggestion}")
            print()
        
        # Return appropriate exit code
        if result.status == ValidationStatus.INVALID:
            return 2
        elif result.status == ValidationStatus.WARNING:
            return 1
        else:
            return 0
            
    except ConfigurationError as e:
        print(f"{RED}Configuration Error: {e}{RESET}")
        if hasattr(e, 'resolution_steps') and e.resolution_steps:
            print(f"\n{YELLOW}Resolution steps:{RESET}")
            for step in e.resolution_steps:
                print(f"  • {step}")
        return 2
    except Exception as e:
        print(f"{RED}Unexpected error: {e}{RESET}")
        return 2


def validate_all_scenarios(validator: ConstraintValidator, 
                          scenario_file: str = "src/scenarios",
                          verbose: bool = False) -> int:
    """
    Validate all scenarios in a file or directory.
    
    Args:
        validator: Constraint validator instance
        scenario_file: Path to scenarios
        verbose: Show detailed results for each scenario
        
    Returns:
        Exit code (0 for all valid, 1 for some warnings, 2 for any violations)
    """
    try:
        results = validator.validate_all_scenarios(scenario_file)
        
        # Display summary
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}CONSTRAINT VALIDATION SUMMARY{RESET}")
        print(f"{CYAN}{'='*60}{RESET}\n")
        
        # Count results by status
        valid_count = sum(1 for r in results if r.status == ValidationStatus.VALID)
        warning_count = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        invalid_count = sum(1 for r in results if r.status == ValidationStatus.INVALID)
        
        print(f"Total scenarios checked: {len(results)}")
        print(f"  {GREEN}✓ Valid:{RESET} {valid_count}")
        print(f"  {YELLOW}⚠ Warnings:{RESET} {warning_count}")
        print(f"  {RED}✗ Invalid:{RESET} {invalid_count}")
        print()
        
        # Create results table
        table_data = []
        for result in results:
            if result.status == ValidationStatus.VALID:
                status = f"{GREEN}✓ Valid{RESET}"
            elif result.status == ValidationStatus.WARNING:
                status = f"{YELLOW}⚠ Warning{RESET}"
            else:
                status = f"{RED}✗ Invalid{RESET}"
            
            violations = len(result.violations)
            warnings = len(result.warnings)
            
            table_data.append([
                result.scenario_name,
                status,
                str(violations) if violations else "-",
                str(warnings) if warnings else "-"
            ])
        
        print(tabulate(
            table_data,
            headers=['Scenario', 'Status', 'Violations', 'Warnings'],
            tablefmt='grid'
        ))
        
        # Show details for invalid scenarios
        if invalid_count > 0:
            print(f"\n{RED}{BOLD}INVALID SCENARIOS:{RESET}")
            for result in results:
                if result.status == ValidationStatus.INVALID:
                    print(f"\n{BOLD}{result.scenario_name}:{RESET}")
                    for violation in result.violations[:3]:  # Show first 3
                        print(f"  {RED}✗{RESET} {violation}")
                    if len(result.violations) > 3:
                        print(f"  ... and {len(result.violations) - 3} more violations")
        
        # Show details if verbose
        if verbose and (warning_count > 0 or invalid_count > 0):
            print(f"\n{BOLD}DETAILED RESULTS:{RESET}")
            for result in results:
                if result.status != ValidationStatus.VALID:
                    print(f"\n{'-'*40}")
                    print(result.get_report())
        
        # Return appropriate exit code
        if invalid_count > 0:
            return 2
        elif warning_count > 0:
            return 1
        else:
            return 0
            
    except ConfigurationError as e:
        print(f"{RED}Configuration Error: {e}{RESET}")
        if hasattr(e, 'resolution_steps') and e.resolution_steps:
            print(f"\n{YELLOW}Resolution steps:{RESET}")
            for step in e.resolution_steps:
                print(f"  • {step}")
        return 2
    except Exception as e:
        print(f"{RED}Unexpected error: {e}{RESET}")
        return 2


def main():
    parser = argparse.ArgumentParser(
        description='Validate AI impact model scenarios against business constraints',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a specific scenario
  python validate_constraints.py moderate_enterprise
  
  # Validate all scenarios in default location
  python validate_constraints.py --all
  
  # Validate all with detailed output
  python validate_constraints.py --all --verbose
  
  # Validate scenarios from custom file
  python validate_constraints.py --all --file custom_scenarios.yaml

Exit codes:
  0 - All constraints satisfied
  1 - Warnings present but no violations
  2 - Constraint violations found
        """
    )
    
    parser.add_argument(
        'scenario',
        nargs='?',
        help='Name of specific scenario to validate'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Validate all scenarios'
    )
    
    parser.add_argument(
        '--file', '-f',
        default='src/scenarios',
        help='Path to scenarios file or directory (default: src/scenarios)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed validation results'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors (exit code 2 for warnings)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.scenario and not args.all:
        parser.error("Either specify a scenario name or use --all")
    
    if args.scenario and args.all:
        parser.error("Cannot specify both a scenario name and --all")
    
    # Create validator
    validator = ConstraintValidator()
    
    # Run validation
    if args.all:
        exit_code = validate_all_scenarios(validator, args.file, args.verbose)
    else:
        exit_code = validate_single_scenario(validator, args.scenario, args.file)
    
    # Apply strict mode if requested
    if args.strict and exit_code == 1:
        exit_code = 2
    
    # Final message
    if exit_code == 0:
        print(f"\n{GREEN}✓ All constraints satisfied!{RESET}")
    elif exit_code == 1:
        print(f"\n{YELLOW}⚠ Validation completed with warnings{RESET}")
    else:
        print(f"\n{RED}✗ Constraint violations found{RESET}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()