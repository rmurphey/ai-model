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
                      test_automation: float, deployment_freq: str,
                      senior_ratio: float = 0.2, junior_ratio: float = 0.4):
    """
    Simulate delivery pipeline with given parameters and seniority constraints.
    
    Args:
        team_size: Total team size
        cost_per_seat: Cost per developer seat
        adoption: AI adoption rate (0-1)
        test_automation: Test automation level (0-1)
        deployment_freq: Deployment frequency
        senior_ratio: Ratio of senior developers (0-1)
        junior_ratio: Ratio of junior developers (0-1)
    """
    
    # Calculate team composition
    senior_count = max(1, int(team_size * senior_ratio))  # At least 1 senior
    junior_count = int(team_size * junior_ratio)
    mid_count = team_size - senior_count - junior_count
    
    # AI impact on each stage
    coding_speedup = 1.4  # 40% faster coding with AI
    review_slowdown = 1.25  # 25% slower review for AI code  
    test_increase = 1.3  # 30% more tests needed for AI code
    
    # Calculate throughput for each stage
    baseline_throughput = team_size * 2.0  # 2 features/dev/month baseline
    
    # Coding throughput increases with AI (juniors benefit most)
    junior_speedup = coding_speedup * 1.2  # Juniors get 20% more benefit
    mid_speedup = coding_speedup
    senior_speedup = coding_speedup * 0.8  # Seniors get less benefit
    
    weighted_speedup = (
        (junior_count * junior_speedup + 
         mid_count * mid_speedup + 
         senior_count * senior_speedup) / team_size
    )
    coding_throughput = baseline_throughput * (1 + (weighted_speedup - 1) * adoption)
    
    # Senior review capacity constraint - THE KEY BOTTLENECK
    # Each senior can review ~40 PRs per month effectively
    reviews_per_senior_per_month = 40
    max_review_capacity = senior_count * reviews_per_senior_per_month
    
    # AI increases PR volume from juniors (they code faster)
    base_prs_per_junior = 8  # PRs per junior per month
    ai_pr_multiplier = 1 + adoption * 0.5  # AI increases PR volume by up to 50%
    junior_pr_load = junior_count * base_prs_per_junior * ai_pr_multiplier
    
    # Mid-level and senior PR loads (less affected by AI)
    mid_pr_load = mid_count * 6  # Mid-level PRs per month
    senior_pr_load = senior_count * 4  # Senior PRs per month
    
    total_pr_load = junior_pr_load + mid_pr_load + senior_pr_load
    
    # Review throughput limited by senior capacity and slowed by AI complexity
    review_throughput = min(
        max_review_capacity / (1 + (review_slowdown - 1) * adoption),
        total_pr_load  # Can't review more than what's produced
    )
    
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
        'team_composition': {
            'senior': senior_count,
            'mid': mid_count,
            'junior': junior_count
        },
        'coding_throughput': coding_throughput,
        'review_throughput': review_throughput,
        'test_throughput': test_throughput,
        'actual_throughput': actual_throughput,
        'bottleneck': bottleneck,
        'senior_review_capacity': max_review_capacity,
        'junior_pr_load': junior_pr_load,
        'total_pr_load': total_pr_load,
        'review_utilization': total_pr_load / max_review_capacity if max_review_capacity > 0 else 0,
        'defects_in_production': defects_in_production,
        'monthly_value': monthly_value,
        'monthly_cost': monthly_cost,
        'monthly_profit': monthly_profit,
        'roi': roi,
        'payback_months': monthly_cost / monthly_profit if monthly_profit > 0 else 999
    }


def find_optimal_adoption(team_size: int, cost_per_seat: float, 
                         test_automation: float, deployment_freq: str,
                         senior_ratio: float = 0.2, junior_ratio: float = 0.4):
    """
    Find the adoption rate that maximizes profit given seniority constraints.
    """
    best_result = None
    best_profit = -float('inf')
    
    # Try different adoption rates
    for adoption_pct in range(10, 100, 5):
        adoption = adoption_pct / 100
        result = simulate_pipeline(team_size, cost_per_seat, adoption,
                                  test_automation, deployment_freq,
                                  senior_ratio, junior_ratio)
        
        if result['monthly_profit'] > best_profit:
            best_profit = result['monthly_profit']
            best_result = result
    
    return best_result


def display_results(result: dict, team_size: int, cost_per_seat: float,
                   test_automation: float, deployment_freq: str,
                   senior_ratio: float = 0.2, junior_ratio: float = 0.4):
    """Display optimization results with seniority constraints."""
    
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}PIPELINE VALUE OPTIMIZATION WITH SENIORITY CONSTRAINTS{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")
    
    if not result:
        print(f"{RED}No profitable configuration found{RESET}")
        return
    
    print(f"{GREEN}✓ Found optimal configuration{RESET}\n")
    
    # Team composition
    comp = result['team_composition']
    print(f"{BOLD}Team Composition:{RESET}")
    team_data = [
        ["Senior Developers", f"{comp['senior']} ({comp['senior']/team_size:.0%})"],
        ["Mid-level Developers", f"{comp['mid']} ({comp['mid']/team_size:.0%})"], 
        ["Junior Developers", f"{comp['junior']} ({comp['junior']/team_size:.0%})"],
    ]
    print(tabulate(team_data, tablefmt='simple'))
    print()
    
    # Pipeline metrics with seniority constraints
    print(f"{BOLD}Pipeline Throughput (features/month):{RESET}")
    pipeline = [
        ["Coding Capacity", f"{result['coding_throughput']:.1f}"],
        ["Review Capacity", f"{result['review_throughput']:.1f}"],
        ["  Senior Review Capacity", f"{result['senior_review_capacity']:.0f} PRs/month"],
        ["  Junior PR Load", f"{result['junior_pr_load']:.0f} PRs/month"],
        ["  Review Utilization", f"{result['review_utilization']:.1%}"],
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
    
    # Seniority-specific insights
    print(f"{BOLD}Seniority Constraints Analysis:{RESET}")
    
    comp = result['team_composition']
    if comp['junior'] > comp['senior'] * 3:  # Junior-heavy team
        print(f"⚠️  {YELLOW}Junior-heavy team detected{RESET}")
        print(f"   → {comp['junior']} juniors vs {comp['senior']} seniors")
        print("   → Senior review capacity is likely the constraint")
        
    if result['review_utilization'] > 0.8:
        print(f"⚠️  {RED}Senior review capacity overloaded ({result['review_utilization']:.0%}){RESET}")
        print(f"   → {comp['junior']} juniors producing {result['junior_pr_load']:.0f} PRs/month")
        print(f"   → {comp['senior']} seniors can handle {result['senior_review_capacity']:.0f} PRs/month")
        print("   → CRITICAL: This constrains junior-heavy teams")
        
    print(f"\n{BOLD}Key Bottleneck Insights:{RESET}")
    
    if result['bottleneck'] == "code_review":
        print(f"⚠️  {YELLOW}Code review is limiting throughput{RESET}")
        if comp['junior'] > comp['senior'] * 2:
            print("   → JUNIOR TEAM CONSTRAINT: Need more senior review capacity")
            print(f"   → Consider: Promote mid-level devs, hire seniors, or reduce AI adoption")
        else:
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
        if comp['junior'] / team_size > 0.5:
            print("   → Junior-heavy teams need stronger review processes")
        print("   → Improve testing coverage and code review")
    
    print(f"\n{BOLD}Optimal Strategy:{RESET}")
    print(f"• Adopt AI tools at {result['adoption']:.0f}% of team")
    if result['bottleneck'] == "code_review" and comp['junior'] > comp['senior'] * 2:
        print(f"• ⚠️  CRITICAL: Senior review capacity constrains this junior-heavy team")  
        print(f"• Consider: Hire seniors, promote mids, or limit AI to {max(20, int(result['adoption']*0.7))}%")
    else:
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
    parser.add_argument('--senior-ratio', type=float, default=0.2,
                       help='Ratio of senior developers (0.0-1.0, default: 0.2)')
    parser.add_argument('--junior-ratio', type=float, default=0.4,
                       help='Ratio of junior developers (0.0-1.0, default: 0.4)')
    
    args = parser.parse_args()
    
    # Validate seniority ratios
    if args.senior_ratio + args.junior_ratio > 1.0:
        print(f"{RED}Error: Senior ratio + Junior ratio cannot exceed 1.0{RESET}")
        sys.exit(1)
        
    mid_ratio = 1.0 - args.senior_ratio - args.junior_ratio
    if mid_ratio < 0:
        print(f"{RED}Error: Invalid seniority ratios{RESET}")
        sys.exit(1)
    
    print(f"\n{BOLD}Optimizing value delivery with seniority constraints...{RESET}")
    print(f"Team: {args.team} | Cost: ${args.cost}/seat")
    print(f"Test Automation: {args.automation:.0%} | Deploy: {args.deploy}")
    print(f"Team Composition: {args.senior_ratio:.0%} Senior, {mid_ratio:.0%} Mid, {args.junior_ratio:.0%} Junior")
    
    result = find_optimal_adoption(args.team, args.cost, args.automation, args.deploy,
                                  args.senior_ratio, args.junior_ratio)
    
    display_results(result, args.team, args.cost, args.automation, args.deploy,
                   args.senior_ratio, args.junior_ratio)
    
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()