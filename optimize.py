#!/usr/bin/env python3
"""
Constraint-based optimization CLI for AI impact model.
Finds optimal parameters given business constraints and objectives.
"""

import argparse
import sys
from typing import Dict, Any, Optional
from tabulate import tabulate

from src.constraints import (
    ConstraintSolver, 
    BusinessConstraints,
    OptimizationObjective,
    ObjectiveType
)
from src.utils.exceptions import ValidationError, CalculationError

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


def create_optimization_model(objective: str, constraints: Dict[str, Any]) -> ConstraintSolver:
    """
    Create and configure optimization model.
    
    Args:
        objective: Optimization objective type
        constraints: Dictionary of constraints
        
    Returns:
        Configured constraint solver
    """
    solver = ConstraintSolver(use_integer_solver=False)
    
    # Add variables with realistic bounds
    team_size = solver.add_variable('team_size', 1, 1000, is_integer=True)
    cost_per_seat = solver.add_variable('cost_per_seat_month', 10, 500, is_integer=True)
    
    # Adoption variables (scaled by 1000 for integer solver)
    initial_adopters = solver.add_variable('initial_adopters', 10, 300)  # 0.01 to 0.30
    plateau_efficiency = solver.add_variable('plateau_efficiency', 100, 950)  # 0.10 to 0.95
    dropout_rate = solver.add_variable('dropout_rate_month', 0, 100)  # 0.00 to 0.10
    
    # Impact variables (scaled by 1000)
    feature_cycle_reduction = solver.add_variable('feature_cycle_reduction', 0, 500)  # 0 to 0.50
    bug_fix_reduction = solver.add_variable('bug_fix_reduction', 0, 600)  # 0 to 0.60
    defect_reduction = solver.add_variable('defect_reduction', 0, 400)  # 0 to 0.40
    incident_reduction = solver.add_variable('incident_reduction', 0, 500)  # 0 to 0.50
    
    # Team composition (scaled by 1000)
    junior_ratio = solver.add_variable('junior_ratio', 50, 700)  # 0.05 to 0.70
    mid_ratio = solver.add_variable('mid_ratio', 100, 700)  # 0.10 to 0.70
    senior_ratio = solver.add_variable('senior_ratio', 50, 500)  # 0.05 to 0.50
    
    # Apply business constraints
    business = BusinessConstraints(solver)
    
    # Budget constraint if specified
    if 'budget' in constraints:
        business.add_budget_constraint(
            constraints['budget'],
            team_size,
            cost_per_seat
        )
    
    # Team size constraint if specified
    if 'min_team' in constraints or 'max_team' in constraints:
        min_team = constraints.get('min_team', 1)
        max_team = constraints.get('max_team', 1000)
        business.add_team_size_constraint(team_size, min_team, max_team)
    
    # Team composition must sum to 1.0
    business.add_team_composition_constraint(junior_ratio, mid_ratio, senior_ratio)
    
    # Adoption constraints
    business.add_adoption_constraints(initial_adopters, plateau_efficiency, dropout_rate)
    
    # Impact constraints
    impact_vars = {
        'feature_cycle_reduction': feature_cycle_reduction,
        'bug_fix_reduction': bug_fix_reduction,
        'defect_reduction': defect_reduction,
        'incident_reduction': incident_reduction
    }
    business.add_impact_constraints(impact_vars)
    
    # ROI constraint if specified
    if 'min_roi' in constraints:
        # Simplified ROI calculation for demo
        value_proxy = (feature_cycle_reduction + bug_fix_reduction + 
                      defect_reduction + incident_reduction)
        cost_proxy = team_size * cost_per_seat / 100
        roi_proxy = value_proxy - cost_proxy
        solver.add_constraint(roi_proxy >= constraints['min_roi'] * 100, "min_roi_constraint")
    
    # Set optimization objective
    obj_manager = OptimizationObjective(solver)
    
    if objective == 'max_npv':
        # Simplified NPV proxy
        value_vars = {
            'feature_value': feature_cycle_reduction * team_size,
            'bug_value': bug_fix_reduction * team_size,
            'defect_value': defect_reduction * team_size
        }
        cost_vars = {
            'license_cost': team_size * cost_per_seat
        }
        obj_manager.set_npv_maximization(value_vars, cost_vars, 24)
        
    elif objective == 'max_roi':
        value_vars = {
            'total_value': (feature_cycle_reduction + bug_fix_reduction + 
                          defect_reduction + incident_reduction) * team_size
        }
        cost_vars = {
            'total_cost': team_size * cost_per_seat
        }
        obj_manager.set_roi_maximization(value_vars, cost_vars)
        
    elif objective == 'min_cost':
        cost_vars = {
            'total_cost': team_size * cost_per_seat
        }
        obj_manager.set_cost_minimization(cost_vars)
        
    elif objective == 'max_adoption':
        adoption_vars = {
            'initial_adopters': initial_adopters,
            'plateau_efficiency': plateau_efficiency,
            'dropout_rate': dropout_rate
        }
        obj_manager.set_adoption_maximization(adoption_vars)
        
    elif objective == 'balanced':
        value_vars = {
            'value': (feature_cycle_reduction + bug_fix_reduction) * team_size
        }
        cost_vars = {
            'cost': team_size * cost_per_seat
        }
        adoption_vars = {
            'plateau_efficiency': plateau_efficiency
        }
        obj_manager.set_balanced_scorecard(
            npv_weight=0.4, roi_weight=0.3, adoption_weight=0.2, cost_weight=0.1,
            value_vars=value_vars, cost_vars=cost_vars, adoption_vars=adoption_vars
        )
    else:
        raise ValueError(f"Unknown objective: {objective}")
    
    return solver


def format_optimization_results(result):
    """Format optimization results for display."""
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}OPTIMIZATION RESULTS{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")
    
    # Status
    status_color = GREEN if result.is_successful else RED
    print(f"Status: {status_color}{result.status.value.upper()}{RESET}")
    print(f"Message: {result.message}")
    print(f"Solve time: {result.solve_time_seconds:.2f} seconds")
    
    if result.objective_value is not None:
        print(f"Objective value: {result.objective_value:.2f}")
    
    print()
    
    if result.is_successful:
        # Format optimal values
        print(f"{BOLD}OPTIMAL PARAMETER VALUES:{RESET}\n")
        
        # Unscale and organize parameters
        params = []
        for name, value in result.optimal_values.items():
            # Unscale percentage values
            if name in ['initial_adopters', 'plateau_efficiency', 'dropout_rate_month',
                       'feature_cycle_reduction', 'bug_fix_reduction', 'defect_reduction',
                       'incident_reduction', 'junior_ratio', 'mid_ratio', 'senior_ratio']:
                display_value = f"{value/1000:.1%}" if value < 1 else f"{value/1000:.1%}"
            elif name == 'team_size':
                display_value = f"{int(value)}"
            elif name == 'cost_per_seat_month':
                display_value = f"${value:.0f}"
            else:
                display_value = f"{value:.2f}"
            
            params.append([name.replace('_', ' ').title(), display_value])
        
        print(tabulate(params, headers=['Parameter', 'Optimal Value'], tablefmt='simple'))
        
        # Show total monthly cost if applicable
        if 'team_size' in result.optimal_values and 'cost_per_seat_month' in result.optimal_values:
            team = int(result.optimal_values['team_size'])
            cost = result.optimal_values['cost_per_seat_month']
            total_cost = team * cost
            print(f"\n{BOLD}Total Monthly Cost: ${total_cost:,.0f}{RESET}")
    else:
        # Show constraint violations
        if result.constraints_violated:
            print(f"{RED}Constraints violated:{RESET}")
            for constraint in result.constraints_violated:
                print(f"  • {constraint}")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Optimize AI impact model parameters with constraints',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Maximize NPV with budget constraint
  python optimize.py --objective max_npv --budget 10000
  
  # Maximize ROI with team size constraint
  python optimize.py --objective max_roi --min-team 10 --max-team 50
  
  # Balanced optimization with multiple constraints
  python optimize.py --objective balanced --budget 20000 --min-roi 2.0
  
  # Minimize cost while maintaining minimum ROI
  python optimize.py --objective min_cost --min-roi 1.5

Available objectives:
  max_npv      - Maximize Net Present Value
  max_roi      - Maximize Return on Investment
  min_cost     - Minimize total costs
  max_adoption - Maximize adoption success
  balanced     - Balanced multi-objective optimization
        """
    )
    
    parser.add_argument(
        '--objective',
        choices=['max_npv', 'max_roi', 'min_cost', 'max_adoption', 'balanced'],
        default='max_npv',
        help='Optimization objective (default: max_npv)'
    )
    
    parser.add_argument(
        '--budget',
        type=float,
        help='Maximum monthly budget constraint'
    )
    
    parser.add_argument(
        '--min-team',
        type=int,
        help='Minimum team size constraint'
    )
    
    parser.add_argument(
        '--max-team',
        type=int,
        help='Maximum team size constraint'
    )
    
    parser.add_argument(
        '--min-roi',
        type=float,
        help='Minimum ROI constraint (e.g., 1.5 for 150%%)'
    )
    
    parser.add_argument(
        '--time-limit',
        type=int,
        default=60,
        help='Solver time limit in seconds (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Build constraints dictionary
    constraints = {}
    if args.budget:
        constraints['budget'] = args.budget
    if args.min_team:
        constraints['min_team'] = args.min_team
    if args.max_team:
        constraints['max_team'] = args.max_team
    if args.min_roi:
        constraints['min_roi'] = args.min_roi
    
    print(f"\n{BOLD}Optimizing with:{RESET}")
    print(f"  Objective: {args.objective}")
    if constraints:
        print(f"  Constraints: {constraints}")
    print(f"  Time limit: {args.time_limit} seconds")
    
    try:
        # Create and solve optimization model
        solver = create_optimization_model(args.objective, constraints)
        result = solver.solve(time_limit_seconds=args.time_limit)
        
        # Display results
        format_optimization_results(result)
        
        # Return appropriate exit code
        sys.exit(0 if result.is_successful else 1)
        
    except (ValidationError, CalculationError) as e:
        print(f"\n{RED}Error: {e}{RESET}")
        if hasattr(e, 'suggestions') and e.suggestions:
            print(f"\n{YELLOW}Suggestions:{RESET}")
            for suggestion in e.suggestions:
                print(f"  • {suggestion}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()