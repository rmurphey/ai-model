#!/usr/bin/env python3
"""
Simplified value delivery optimization focusing on throughput bottlenecks.
"""

import argparse
import sys
from tabulate import tabulate

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


def simulate_pipeline(team_size: int, cost_per_seat: float, adoption: float,
                      test_automation: float, deployment_freq: str):
    """
    Simulate delivery pipeline with given parameters.
    """
    
    # AI impact on each stage
    coding_speedup = 1.4  # 40% faster coding with AI
    review_slowdown = 1.25  # 25% slower review for AI code  
    test_increase = 1.3  # 30% more tests needed for AI code
    
    # Calculate throughput for each stage
    baseline_throughput = team_size * 2.0  # 2 features/dev/month baseline
    
    # Coding throughput increases with AI
    coding_throughput = baseline_throughput * (1 + (coding_speedup - 1) * adoption)
    
    # Review capacity is limited and slower with AI
    review_capacity = team_size * 0.3  # 30% can review
    review_throughput = review_capacity * 2.0 / (1 + (review_slowdown - 1) * adoption)
    
    # Testing throughput depends on automation
    test_base = team_size * 1.5  # 1.5 features/tester/month
    test_multiplier = 0.5 + test_automation * 1.0  # Automation helps
    test_throughput = test_base * test_multiplier / (1 + (test_increase - 1) * adoption)
    
    # Deployment throughput
    deploy_frequencies = {
        "daily": 30,
        "weekly": 4,
        "biweekly": 2,
        "monthly": 1
    }
    deploy_throughput = deploy_frequencies[deployment_freq] * 10  # Deployments can batch
    
    # Bottleneck determines actual throughput
    actual_throughput = min(coding_throughput, review_throughput, test_throughput, deploy_throughput)
    
    # Identify bottleneck
    if actual_throughput == review_throughput:
        bottleneck = "code_review"
    elif actual_throughput == test_throughput:
        bottleneck = "testing"
    elif actual_throughput == deploy_throughput:
        bottleneck = "deployment"
    else:
        bottleneck = "coding"
    
    # Quality impact
    defect_rate = 0.05  # 5% baseline defect rate
    defect_rate_with_ai = defect_rate * (1 + adoption * 0.2)  # AI adds 20% more defects
    escape_rate = 0.3 * (1 - test_automation * 0.5)  # Automation catches more
    defects_in_production = actual_throughput * defect_rate_with_ai * escape_rate
    
    # Financial calculations
    value_per_feature = 10000  # $10k value per feature
    defect_cost = 5000  # $5k per defect in production
    
    monthly_value = actual_throughput * value_per_feature
    monthly_defect_cost = defects_in_production * defect_cost
    monthly_net_value = monthly_value - monthly_defect_cost
    
    # Costs
    monthly_cost = cost_per_seat * team_size * adoption
    monthly_profit = monthly_net_value - monthly_cost
    
    # ROI
    roi = (monthly_profit / monthly_cost * 100) if monthly_cost > 0 else 0
    
    return {
        'adoption': adoption * 100,
        'coding_throughput': coding_throughput,
        'review_throughput': review_throughput,
        'test_throughput': test_throughput,
        'actual_throughput': actual_throughput,
        'bottleneck': bottleneck,
        'defects_in_production': defects_in_production,
        'monthly_value': monthly_value,
        'monthly_cost': monthly_cost,
        'monthly_profit': monthly_profit,
        'roi': roi,
        'payback_months': monthly_cost / monthly_profit if monthly_profit > 0 else 999
    }


def find_optimal_adoption(team_size: int, cost_per_seat: float, 
                         test_automation: float, deployment_freq: str):
    """
    Find the adoption rate that maximizes profit.
    """
    best_result = None
    best_profit = -float('inf')
    
    # Try different adoption rates
    for adoption_pct in range(10, 100, 5):
        adoption = adoption_pct / 100
        result = simulate_pipeline(team_size, cost_per_seat, adoption,
                                  test_automation, deployment_freq)
        
        if result['monthly_profit'] > best_profit:
            best_profit = result['monthly_profit']
            best_result = result
    
    return best_result


def display_results(result: dict, team_size: int, cost_per_seat: float,
                   test_automation: float, deployment_freq: str):
    """Display optimization results."""
    
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}PIPELINE VALUE OPTIMIZATION RESULTS{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")
    
    if not result:
        print(f"{RED}No profitable configuration found{RESET}")
        return
    
    print(f"{GREEN}✓ Found optimal configuration{RESET}\n")
    
    # Pipeline metrics
    print(f"{BOLD}Pipeline Throughput (features/month):{RESET}")
    pipeline = [
        ["Coding Capacity", f"{result['coding_throughput']:.1f}"],
        ["Review Capacity", f"{result['review_throughput']:.1f}"],
        ["Testing Capacity", f"{result['test_throughput']:.1f}"],
        ["", ""],
        ["Actual Throughput", f"{result['actual_throughput']:.1f}"],
        ["Bottleneck", result['bottleneck'].replace('_', ' ').title()],
        ["", ""],
        ["Defects in Production", f"{result['defects_in_production']:.1f}/month"],
    ]
    print(tabulate(pipeline, tablefmt='simple'))
    print()
    
    # Financial metrics
    print(f"{BOLD}Financial Impact:{RESET}")
    financial = [
        ["Adoption Rate", f"{result['adoption']:.0f}%"],
        ["", ""],
        ["Monthly Value", f"${result['monthly_value']:,.0f}"],
        ["Monthly Cost", f"${result['monthly_cost']:,.0f}"],
        ["Monthly Profit", f"${result['monthly_profit']:,.0f}"],
        ["", ""],
        ["ROI", f"{result['roi']:.0f}%"],
        ["Payback Period", f"{result['payback_months']:.1f} months"],
    ]
    print(tabulate(financial, tablefmt='simple'))
    print()
    
    # Insights
    print(f"{BOLD}Key Insights:{RESET}")
    
    if result['bottleneck'] == "code_review":
        print(f"⚠️  {YELLOW}Code review is limiting throughput{RESET}")
        print("   → Increase review capacity or improve review tools")
        print(f"   → Currently {result['review_throughput']:.1f} vs {result['coding_throughput']:.1f} coding")
    elif result['bottleneck'] == "testing":
        print(f"⚠️  {YELLOW}Testing is limiting throughput{RESET}")
        print("   → Increase test automation or parallel testing")
        print(f"   → Current automation: {test_automation:.0%}")
    elif result['bottleneck'] == "deployment":
        print(f"⚠️  {YELLOW}Deployment frequency is limiting value delivery{RESET}")
        print(f"   → Current: {deployment_freq} deployments")
        print("   → Consider more frequent deployments")
    
    if result['defects_in_production'] > result['actual_throughput'] * 0.1:
        print(f"\n⚠️  {YELLOW}High defect rate ({result['defects_in_production']:.1f}/month){RESET}")
        print("   → Improve testing coverage and code review")
    
    print(f"\n{BOLD}Optimal Strategy:{RESET}")
    print(f"• Adopt AI tools at {result['adoption']:.0f}% of team")
    print(f"• Focus on relieving the {result['bottleneck'].replace('_', ' ')} bottleneck")
    print(f"• Expected monthly profit: ${result['monthly_profit']:,.0f}")


def main():
    parser = argparse.ArgumentParser(
        description='Find optimal AI adoption considering pipeline bottlenecks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Theory of Constraints applied to software delivery:
- Throughput is limited by the slowest stage (bottleneck)
- AI speeds up coding but slows down review
- More code means more testing
- Value only realized when deployed to production

Examples:
  python optimize_value_simple.py --team 50 --cost 100
  python optimize_value_simple.py --team 20 --cost 50 --automation 0.7
  python optimize_value_simple.py --team 100 --cost 200 --deploy daily
        """
    )
    
    parser.add_argument('--team', type=int, required=True, help='Team size')
    parser.add_argument('--cost', type=float, required=True, help='Cost per seat/month')
    parser.add_argument('--automation', type=float, default=0.5,
                       help='Test automation level (0.0-1.0)')
    parser.add_argument('--deploy', choices=['daily', 'weekly', 'biweekly', 'monthly'],
                       default='weekly', help='Deployment frequency')
    
    args = parser.parse_args()
    
    print(f"\n{BOLD}Optimizing value delivery...{RESET}")
    print(f"Team: {args.team} | Cost: ${args.cost}/seat")
    print(f"Test Automation: {args.automation:.0%} | Deploy: {args.deploy}")
    
    result = find_optimal_adoption(args.team, args.cost, args.automation, args.deploy)
    
    display_results(result, args.team, args.cost, args.automation, args.deploy)
    
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()