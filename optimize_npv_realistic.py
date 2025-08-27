#!/usr/bin/env python3
"""
NPV optimization with realistic constraints based on actual scenarios.
"""

import argparse
import sys
from tabulate import tabulate
from ortools.sat.python import cp_model

# Colors
try:
    from src.utils.colors import *
except ImportError:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'


def optimize_npv_realistic(team_size: int, cost_per_seat: float, 
                           avg_salary: int = 120000,
                           months: int = 36, 
                           discount_rate: float = 0.12,
                           scenario_type: str = 'moderate'):
    """
    Find parameters that maximize NPV with realistic constraints.
    
    Based on our scenario analysis:
    - Conservative: 5-10% overall productivity gain
    - Moderate: 15-25% overall productivity gain  
    - Aggressive: 35-50% overall productivity gain
    """
    
    model = cp_model.CpModel()
    
    # === VARIABLES ===
    
    # Adoption rate (percentage, 0-100)
    if scenario_type == 'conservative':
        peak_adoption = model.NewIntVar(30, 70, 'peak_adoption')
    elif scenario_type == 'aggressive':
        peak_adoption = model.NewIntVar(70, 95, 'peak_adoption')
    else:  # moderate
        peak_adoption = model.NewIntVar(50, 85, 'peak_adoption')
    
    # Productivity improvements based on scenario type
    if scenario_type == 'conservative':
        # Conservative: Based on realistic_assessment scenario
        feature_improvement = model.NewIntVar(30, 100, 'feature')  # 3-10%
        bug_fix_improvement = model.NewIntVar(50, 150, 'bug_fix')  # 5-15%
        pr_review_improvement = model.NewIntVar(50, 200, 'pr_review')  # 5-20%
        quality_improvement = model.NewIntVar(20, 80, 'quality')  # 2-8%
        capacity_gain = model.NewIntVar(10, 30, 'capacity')  # 1-3%
        
    elif scenario_type == 'aggressive':
        # Aggressive: Based on aggressive strategy
        feature_improvement = model.NewIntVar(250, 400, 'feature')  # 25-40%
        bug_fix_improvement = model.NewIntVar(350, 500, 'bug_fix')  # 35-50%
        pr_review_improvement = model.NewIntVar(500, 700, 'pr_review')  # 50-70%
        quality_improvement = model.NewIntVar(300, 450, 'quality')  # 30-45%
        capacity_gain = model.NewIntVar(100, 150, 'capacity')  # 10-15%
        
    else:  # moderate
        # Moderate: Between conservative and aggressive
        feature_improvement = model.NewIntVar(150, 250, 'feature')  # 15-25%
        bug_fix_improvement = model.NewIntVar(200, 350, 'bug_fix')  # 20-35%
        pr_review_improvement = model.NewIntVar(300, 500, 'pr_review')  # 30-50%
        quality_improvement = model.NewIntVar(150, 300, 'quality')  # 15-30%
        capacity_gain = model.NewIntVar(50, 100, 'capacity')  # 5-10%
    
    # === CONSTRAINTS ===
    
    # Total productivity gain should be realistic
    total_productivity = feature_improvement + bug_fix_improvement + quality_improvement + capacity_gain
    
    if scenario_type == 'conservative':
        model.Add(total_productivity <= 400)  # Max 40% total
    elif scenario_type == 'aggressive':
        model.Add(total_productivity <= 1500)  # Max 150% total
    else:
        model.Add(total_productivity <= 900)  # Max 90% total
    
    # Bug fixes should improve more than features (empirically true)
    model.Add(bug_fix_improvement >= feature_improvement)
    
    # PR reviews benefit significantly from AI
    model.Add(pr_review_improvement >= feature_improvement)
    
    # Higher adoption requires demonstrable value
    if scenario_type != 'aggressive':
        # For non-aggressive scenarios, high adoption needs high value
        model.Add(peak_adoption * 5 <= total_productivity)
    
    # === NPV CALCULATION ===
    
    # Monthly value per developer
    # Based on actual productivity gains from scenarios
    value_weights = {
        'feature': 0.3,  # Feature delivery is high value
        'bug_fix': 0.2,  # Bug fixing saves time
        'pr_review': 0.1,  # Review speed helps flow
        'quality': 0.25,  # Quality reduces rework
        'capacity': 0.15  # More capacity for features
    }
    
    monthly_salary = avg_salary / 12
    
    # Pre-calculate NPV discount factor
    monthly_rate = (1 + discount_rate) ** (1/12) - 1
    npv_factor = int(sum(1/(1+monthly_rate)**i for i in range(1, months+1)))
    
    # Build linear objective
    # Value component (improvements create value)
    value_per_improvement = int(monthly_salary * 0.01 * team_size * npv_factor / 100)
    
    value_component = (
        feature_improvement * int(value_weights['feature'] * value_per_improvement) +
        bug_fix_improvement * int(value_weights['bug_fix'] * value_per_improvement) +
        pr_review_improvement * int(value_weights['pr_review'] * value_per_improvement) +
        quality_improvement * int(value_weights['quality'] * value_per_improvement) +
        capacity_gain * int(value_weights['capacity'] * value_per_improvement)
    )
    
    # Adoption scaling (value increases with adoption)
    adoption_multiplier = int(npv_factor * team_size * monthly_salary * 0.001)
    
    # Cost component
    total_cost = int(cost_per_seat * team_size * months)
    
    # NPV proxy: value from improvements scaled by adoption minus costs
    npv_proxy = (
        value_component +
        peak_adoption * adoption_multiplier -
        peak_adoption * int(total_cost / 100)  # Scale cost by adoption
    )
    
    # === OPTIMIZE ===
    
    model.Maximize(npv_proxy)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)
    
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Extract solution
        adoption = solver.Value(peak_adoption)
        
        improvements = {
            'feature': solver.Value(feature_improvement) / 10,
            'bug_fix': solver.Value(bug_fix_improvement) / 10,
            'pr_review': solver.Value(pr_review_improvement) / 10,
            'quality': solver.Value(quality_improvement) / 10,
            'capacity': solver.Value(capacity_gain) / 10
        }
        
        # Calculate weighted average productivity gain
        total_gain = sum(improvements.values()) / len(improvements)
        
        # Calculate actual NPV using realistic model
        monthly_value = monthly_salary * (total_gain / 100) * team_size * (adoption / 100)
        monthly_cost = cost_per_seat * team_size * (adoption / 100)
        
        npv = 0
        for month in range(1, months + 1):
            monthly_net = monthly_value - monthly_cost
            npv += monthly_net / (1 + monthly_rate) ** month
        
        # Annual metrics
        annual_value = monthly_value * 12
        annual_cost = monthly_cost * 12
        roi = ((annual_value - annual_cost) / annual_cost * 100) if annual_cost > 0 else 0
        payback = (annual_cost / (monthly_value - monthly_cost)) if monthly_value > monthly_cost else 999
        
        return {
            'status': 'success',
            'adoption': adoption,
            'improvements': improvements,
            'total_gain': total_gain,
            'financials': {
                'npv': npv,
                'monthly_value': monthly_value,
                'monthly_cost': monthly_cost,
                'annual_value': annual_value,
                'annual_cost': annual_cost,
                'roi': roi,
                'payback_months': min(payback, 999)
            }
        }
    
    return {'status': 'failed'}


def display_results(result: dict, team_size: int, cost_per_seat: float, 
                    scenario_type: str, months: int):
    """Display optimization results."""
    
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}REALISTIC NPV-OPTIMIZED STRATEGY ({scenario_type.upper()}){RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")
    
    if result['status'] != 'success':
        print(f"{RED}Optimization failed{RESET}")
        return
    
    print(f"{GREEN}✓ Found optimal parameters for {scenario_type} scenario{RESET}\n")
    
    # Strategy summary
    print(f"{BOLD}Optimal Strategy:{RESET}")
    strategy = [
        ["Peak Adoption Rate", f"{result['adoption']}%"],
        ["", ""],
        ["Feature Delivery", f"+{result['improvements']['feature']:.1f}%"],
        ["Bug Fixing", f"+{result['improvements']['bug_fix']:.1f}%"],
        ["Code Reviews", f"+{result['improvements']['pr_review']:.1f}%"],
        ["Code Quality", f"+{result['improvements']['quality']:.1f}%"],
        ["Capacity Gain", f"+{result['improvements']['capacity']:.1f}%"],
        ["", ""],
        ["Overall Productivity", f"+{result['total_gain']:.1f}%"]
    ]
    print(tabulate(strategy, tablefmt='simple'))
    print()
    
    # Financial results
    print(f"{BOLD}Financial Impact:{RESET}")
    fin = result['financials']
    financial = [
        [f"NPV ({months} months)", f"${fin['npv']:,.0f}"],
        ["", ""],
        ["Monthly Value", f"${fin['monthly_value']:,.0f}"],
        ["Monthly Cost", f"${fin['monthly_cost']:,.0f}"],
        ["Monthly Net", f"${fin['monthly_value'] - fin['monthly_cost']:,.0f}"],
        ["", ""],
        ["Annual Value", f"${fin['annual_value']:,.0f}"],
        ["Annual Cost", f"${fin['annual_cost']:,.0f}"],
        ["Annual Net", f"${fin['annual_value'] - fin['annual_cost']:,.0f}"],
        ["", ""],
        ["ROI", f"{fin['roi']:.0f}%"],
        ["Payback Period", f"{fin['payback_months']:.1f} months"]
    ]
    print(tabulate(financial, tablefmt='simple'))
    print()
    
    # Adoption details
    adopted = int(team_size * result['adoption'] / 100)
    print(f"{BOLD}Implementation:{RESET}")
    impl = [
        ["Team Adoption", f"{adopted} of {team_size} developers"],
        ["Per-Developer Value", f"${fin['monthly_value']/adopted:,.0f}/month" if adopted > 0 else "N/A"],
        ["Per-Developer Cost", f"${cost_per_seat:.0f}/month"],
        ["Break-even Adoption", f"{int(cost_per_seat/(fin['monthly_value']/adopted)*100) if adopted > 0 else 0}%"]
    ]
    print(tabulate(impl, tablefmt='simple'))


def main():
    parser = argparse.ArgumentParser(
        description='Find NPV-optimal AI adoption with realistic constraints',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scenarios are based on real-world observations:

conservative:  5-15% productivity gains (most realistic)
  - Based on actual enterprise deployments
  - Conservative adoption rates (30-70%)
  - Lower risk, proven benefits

moderate:     15-35% productivity gains (balanced)
  - Assumes good implementation and training
  - Moderate adoption rates (50-85%)
  - Balanced risk/reward

aggressive:   35-50% productivity gains (optimistic)
  - Assumes ideal conditions and full buy-in
  - High adoption rates (70-95%)
  - Higher risk, requires excellence

Examples:
  python optimize_npv_realistic.py --team 50 --cost 100
  python optimize_npv_realistic.py --team 100 --cost 200 --scenario aggressive
  python optimize_npv_realistic.py --team 20 --cost 50 --scenario conservative
        """
    )
    
    parser.add_argument('--team', type=int, required=True, help='Team size')
    parser.add_argument('--cost', type=float, required=True, help='Cost per seat/month')
    parser.add_argument('--salary', type=int, default=120000, help='Average salary')
    parser.add_argument('--months', type=int, default=36, help='Time horizon')
    parser.add_argument('--scenario', choices=['conservative', 'moderate', 'aggressive'],
                       default='moderate', help='Scenario type')
    
    args = parser.parse_args()
    
    print(f"\n{BOLD}Optimizing NPV with {args.scenario} constraints...{RESET}")
    print(f"Team: {args.team} | Cost: ${args.cost}/seat | Horizon: {args.months} months")
    
    result = optimize_npv_realistic(
        team_size=args.team,
        cost_per_seat=args.cost,
        avg_salary=args.salary,
        months=args.months,
        scenario_type=args.scenario
    )
    
    display_results(result, args.team, args.cost, args.scenario, args.months)
    
    sys.exit(0 if result['status'] == 'success' else 1)


if __name__ == "__main__":
    main()