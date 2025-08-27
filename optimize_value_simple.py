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


def simulate_baseline_throughput(team_size: int, test_automation: float, deployment_freq: str,
                                senior_ratio: float, junior_ratio: float):
    """Calculate baseline throughput without AI."""
    pipeline = create_pipeline_model(team_size, test_automation, deployment_freq)
    baseline_data = pipeline.calculate_throughput(0.0)  # 0% AI adoption
    return baseline_data['throughput_per_day']


def simulate_pipeline(team_size: int, cost_per_seat: float, adoption: float,
                      test_automation: float, deployment_freq: str,
                      senior_ratio: float = 0.2, junior_ratio: float = 0.4,
                      avg_salary: int = 120000):
    """
    Simulate delivery pipeline with given parameters and seniority constraints.
    Now with realistic cost accounting including base salaries.
    
    Args:
        team_size: Total team size
        cost_per_seat: Cost per AI tool seat
        adoption: AI adoption rate (0-1)
        test_automation: Test automation level (0-1)
        deployment_freq: Deployment frequency
        senior_ratio: Ratio of senior developers (0-1)
        junior_ratio: Ratio of junior developers (0-1)
        avg_salary: Average developer salary for base costs
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
    
    # Financial calculations with REALISTIC values
    # Realistic feature value: $3-5k (not $10k)
    value_per_feature = 4000  # $4k value per feature
    defect_cost = 2000  # $2k per defect in production
    
    # Don't artificially cap throughput - it's already realistic from the pipeline model
    realistic_throughput = actual_throughput
    
    monthly_feature_value = realistic_throughput * value_per_feature
    monthly_defect_cost = defects_in_production * defect_cost
    monthly_net_value = monthly_feature_value - monthly_defect_cost
    
    # PROPER cost accounting including base salaries
    monthly_salary_cost = (avg_salary / 12) * team_size  # Base operational cost
    monthly_ai_cost = cost_per_seat * team_size * adoption  # AI tool cost
    total_monthly_cost = monthly_salary_cost + monthly_ai_cost
    
    # Calculate INCREMENTAL value (what we gain from optimization)
    # Baseline is throughput without AI (adoption = 0)
    baseline_throughput = simulate_baseline_throughput(team_size, test_automation, deployment_freq,
                                                      senior_ratio, junior_ratio)
    baseline_value = baseline_throughput * value_per_feature
    incremental_value = monthly_net_value - baseline_value
    
    # Implementation cost (even "exploitation" has cost)
    implementation_cost_monthly = (team_size * 500) / 12  # $500/person amortized over a year
    
    # Net profit (incremental value minus incremental costs)
    incremental_cost = monthly_ai_cost + implementation_cost_monthly
    net_incremental_profit = incremental_value - incremental_cost
    
    # REALISTIC ROI based on incremental returns
    if incremental_cost > 0:
        roi = (net_incremental_profit / incremental_cost * 100)
        annual_roi = roi * 12 / 12  # Annualized
    else:
        roi = 0
        annual_roi = 0
    
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
        'actual_throughput': realistic_throughput,  # Use realistic throughput
        'bottleneck': bottleneck,
        'senior_review_capacity': max_review_capacity,
        'junior_pr_load': junior_pr_load,
        'total_pr_load': total_pr_load,
        'review_utilization': total_pr_load / max_review_capacity if max_review_capacity > 0 else 0,
        'defects_in_production': defects_in_production,
        'monthly_value': monthly_net_value,
        'monthly_cost': total_monthly_cost,  # Include base salaries
        'monthly_ai_cost': monthly_ai_cost,  # AI cost separately
        'monthly_salary_cost': monthly_salary_cost,  # Base salaries
        'incremental_value': incremental_value,  # What we actually gain
        'incremental_cost': incremental_cost,  # What we actually spend extra
        'monthly_profit': net_incremental_profit,  # Real profit
        'roi': roi,  # Realistic ROI
        'annual_roi': annual_roi,  # Annualized
        'payback_months': incremental_cost / net_incremental_profit if net_incremental_profit > 0 else 999
    }


def find_optimal_using_toc(team_size: int, cost_per_seat: float,
                          test_automation: float, deployment_freq: str,
                          senior_ratio: float = 0.2, junior_ratio: float = 0.4):
    """
    Find optimal configuration using Theory of Constraints approach.
    Focuses on constraint throughput rather than global AI adoption optimization.
    """
    try:
        from src.model.delivery_pipeline import create_standard_pipeline
        from src.model.constraint_optimizer import ConstraintOptimizer
from src.model.delivery_pipeline import create_standard_pipeline as create_pipeline_model
        
        # Create team composition
        senior_count = max(1, int(team_size * senior_ratio))
        junior_count = int(team_size * junior_ratio)
        mid_count = team_size - senior_count - junior_count
        
        team_composition = {
            'senior': senior_count,
            'mid': mid_count, 
            'junior': junior_count
        }
        
        # Create pipeline and constraint optimizer
        pipeline = create_standard_pipeline(
            team_size=team_size,
            test_automation=test_automation,
            deployment_frequency=deployment_freq
        )
        
        optimizer = ConstraintOptimizer(pipeline)
        
        # Apply Theory of Constraints optimization
        toc_result = optimizer.optimize_for_constraint(team_composition, cost_per_seat)
        
        if toc_result:
            # Convert ToC result to format expected by display_results
            return {
                'adoption': toc_result['optimal_ai_adoption'],
                'team_composition': team_composition,
                'actual_throughput': toc_result['final_throughput'],
                'bottleneck': toc_result['constraint_analysis'].constraint_stage,
                'monthly_profit': toc_result['net_value_per_day'] * 30,
                'monthly_cost': toc_result['monthly_cost'],
                'toc_optimization': True,  # Flag indicating ToC approach used
                'constraint_analysis': toc_result['constraint_analysis'],
                'exploitation_result': toc_result['exploitation_result'],
                'subordination_rules': toc_result['subordination_rules']
            }
        else:
            # Fallback to original approach
            return find_optimal_adoption_legacy(team_size, cost_per_seat, 
                                              test_automation, deployment_freq,
                                              senior_ratio, junior_ratio)
            
    except ImportError:
        # Fallback if ToC modules not available
        return find_optimal_adoption_legacy(team_size, cost_per_seat,
                                          test_automation, deployment_freq, 
                                          senior_ratio, junior_ratio)


def find_optimal_adoption_legacy(team_size: int, cost_per_seat: float, 
                                test_automation: float, deployment_freq: str,
                                senior_ratio: float = 0.2, junior_ratio: float = 0.4):
    """
    Legacy approach: Find the adoption rate that maximizes profit.
    Kept for fallback compatibility.
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
    """Display optimization results - Theory of Constraints or legacy approach."""
    
    is_toc = result.get('toc_optimization', False)
    
    print(f"\n{CYAN}{'='*70}{RESET}")
    if is_toc:
        print(f"{BOLD}THEORY OF CONSTRAINTS OPTIMIZATION RESULTS{RESET}")
        print(f"{CYAN}Constraint-focused approach (not global AI adoption){RESET}")
    else:
        print(f"{BOLD}PIPELINE VALUE OPTIMIZATION WITH SENIORITY CONSTRAINTS{RESET}")
        print(f"{YELLOW}Legacy approach - consider using constraint_analyzer.py for ToC{RESET}")
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
    
    # Pipeline metrics - different format for ToC vs legacy
    print(f"{BOLD}Pipeline Throughput (features/month):{RESET}")
    
    if result.get('toc_optimization', False):
        # Theory of Constraints format
        constraint_analysis = result.get('constraint_analysis')
        pipeline = [
            ["Constraint Stage", result['bottleneck'].replace('_', ' ').title()],
            ["Actual Throughput", f"{result['actual_throughput']:.1f}"],
            ["Constraint Utilization", f"{constraint_analysis.constraint_utilization:.1%}" if constraint_analysis else "N/A"],
            ["", ""],
            ["Stage Throughputs:", ""],
        ]
        
        # Add individual stage throughputs if available
        if constraint_analysis and constraint_analysis.stage_throughputs:
            for stage, throughput in constraint_analysis.stage_throughputs.items():
                is_constraint = "🚫 " if stage == result['bottleneck'] else "   "
                pipeline.append([f"{is_constraint}{stage.replace('_', ' ').title()}", f"{throughput:.1f}"])
    else:
        # Legacy format
        pipeline = [
            ["Coding Capacity", f"{result.get('coding_throughput', 'N/A')}"],
            ["Review Capacity", f"{result.get('review_throughput', 'N/A')}"],
            ["  Senior Review Capacity", f"{result.get('senior_review_capacity', 0):.0f} PRs/month"],
            ["  Junior PR Load", f"{result.get('junior_pr_load', 0):.0f} PRs/month"],
            ["  Review Utilization", f"{result.get('review_utilization', 0):.1%}"],
            ["Testing Capacity", f"{result.get('test_throughput', 'N/A')}"],
            ["", ""],
            ["Actual Throughput", f"{result['actual_throughput']:.1f}"],
            ["Bottleneck", result['bottleneck'].replace('_', ' ').title()],
            ["", ""],
            ["Defects in Production", f"{result.get('defects_in_production', 0):.1f}/month"],
        ]
    
    print(tabulate(pipeline, tablefmt='simple'))
    print()
    
    # Financial metrics
    print(f"{BOLD}Financial Impact:{RESET}")
    
    # Calculate ROI and payback for both formats
    monthly_profit = result['monthly_profit']
    monthly_cost = result['monthly_cost']
    roi = (monthly_profit / monthly_cost * 100) if monthly_cost > 0 else 0
    payback = monthly_cost / monthly_profit if monthly_profit > 0 else 999
    
    financial = [
        ["Adoption Rate", f"{result['adoption']:.0f}%"],
        ["", ""],
        ["Monthly Value", f"${result.get('monthly_value', result['actual_throughput'] * 10000 * 30):,.0f}"],
        ["Monthly Cost", f"${monthly_cost:,.0f}"],
        ["Monthly Profit", f"${monthly_profit:,.0f}"],
        ["", ""],
        ["ROI", f"{roi:.0f}%"],
        ["Payback Period", f"{payback:.1f} months"],
    ]
    print(tabulate(financial, tablefmt='simple'))
    print()
    
    # Analysis - different for ToC vs legacy
    if result.get('toc_optimization', False):
        print(f"{BOLD}Theory of Constraints Analysis:{RESET}")
        
        constraint_analysis = result.get('constraint_analysis')
        if constraint_analysis:
            print(f"🎯 Constraint: {constraint_analysis.constraint_stage.replace('_', ' ').title()}")
            print(f"💡 Improvement potential: {constraint_analysis.improvement_potential:.1%}")
            print(f"💰 Cost of constraint: ${constraint_analysis.cost_of_constraint:,.0f}/day")
            
            if constraint_analysis.queue_buildup:
                total_queue = sum(constraint_analysis.queue_buildup.values())
                if total_queue > 0:
                    print(f"⚠️  Queue buildup: {total_queue:.1f} features waiting")
        
        exploitation_result = result.get('exploitation_result')
        if exploitation_result:
            print(f"\n{BOLD}Exploitation Opportunities:{RESET}")
            print(f"• Current throughput: {exploitation_result['original_throughput']:.1f}")
            print(f"• After exploitation: {exploitation_result['exploited_throughput']:.1f}")
            print(f"• Improvement: {exploitation_result['improvement_percent']:.1f}% at $0 cost")
    else:
        # Legacy seniority-specific insights
        print(f"{BOLD}Seniority Constraints Analysis:{RESET}")
        
        comp = result['team_composition']
        if comp['junior'] > comp['senior'] * 3:  # Junior-heavy team
            print(f"⚠️  {YELLOW}Junior-heavy team detected{RESET}")
            print(f"   → {comp['junior']} juniors vs {comp['senior']} seniors")
            print("   → Senior review capacity is likely the constraint")
            
        review_util = result.get('review_utilization', 0)
        if review_util > 0.8:
            print(f"⚠️  {RED}Senior review capacity overloaded ({review_util:.0%}){RESET}")
            print(f"   → {comp['junior']} juniors producing {result.get('junior_pr_load', 0):.0f} PRs/month")
            print(f"   → {comp['senior']} seniors can handle {result.get('senior_review_capacity', 0):.0f} PRs/month")
            print("   → CRITICAL: This constrains junior-heavy teams")
            
        print(f"\n{BOLD}Key Bottleneck Insights:{RESET}")
        
        if result['bottleneck'] == "code_review":
            print(f"⚠️  {YELLOW}Code review is limiting throughput{RESET}")
            if comp['junior'] > comp['senior'] * 2:
                print("   → JUNIOR TEAM CONSTRAINT: Need more senior review capacity")
                print(f"   → Consider: Promote mid-level devs, hire seniors, or reduce AI adoption")
            else:
                print("   → Increase review capacity or improve review tools")
        elif result['bottleneck'] == "testing":
            print(f"⚠️  {YELLOW}Testing is limiting throughput{RESET}")
            print("   → Increase test automation or parallel testing")
            print(f"   → Current automation: {test_automation:.0%}")
        elif result['bottleneck'] == "deployment":
            print(f"⚠️  {YELLOW}Deployment frequency is limiting value delivery{RESET}")
            print(f"   → Current: {deployment_freq} deployments")
            print("   → Consider more frequent deployments")
        
        defects = result.get('defects_in_production', 0)
        if defects > result['actual_throughput'] * 0.1:
            print(f"\n⚠️  {YELLOW}High defect rate ({defects:.1f}/month){RESET}")
            if comp['junior'] / team_size > 0.5:
                print("   → Junior-heavy teams need stronger review processes")
            print("   → Improve testing coverage and code review")
    
    print(f"\n{BOLD}Optimal Strategy:{RESET}")
    
    if result.get('toc_optimization', False):
        # Theory of Constraints specific recommendations
        constraint_analysis = result.get('constraint_analysis')
        exploitation_result = result.get('exploitation_result')
        
        print(f"🎯 {GREEN}Theory of Constraints Approach{RESET}")
        print(f"• Constraint identified: {constraint_analysis.constraint_stage.replace('_', ' ').title()}")
        print(f"• Optimal AI adoption: {result['adoption']:.0f}% (constraint-focused, not global max)")
        
        if exploitation_result:
            print(f"• Exploit constraint first: +{exploitation_result['improvement_percent']:.1f}% throughput improvement")
            print(f"• Implementation cost: ${exploitation_result['cost']:,} (exploit before adding capacity)")
        
        print(f"• Focus on constraint throughput: {result['actual_throughput']:.1f} features/month")
        
        # Subordination rules
        subordination_rules = result.get('subordination_rules', [])
        if subordination_rules:
            print(f"• Subordination rules active: {len(subordination_rules)} stages supporting constraint")
        
        print(f"\n{BOLD}Theory of Constraints Principles Applied:{RESET}")
        print(f"  1. ✓ Constraint identified: {constraint_analysis.constraint_stage if constraint_analysis else 'N/A'}")
        print(f"  2. ✓ Exploitation strategies: {len(constraint_analysis.exploitation_strategies) if constraint_analysis else 0} available")
        print(f"  3. ✓ Subordination: All stages optimized for constraint support")
        print(f"  4. → Elevation: Next step if exploitation insufficient")
        print(f"  5. → Repeat: Monitor for constraint movement")
        
    else:
        # Legacy approach recommendations
        print(f"• Adopt AI tools at {result['adoption']:.0f}% of team")
        if result['bottleneck'] == "code_review" and comp['junior'] > comp['senior'] * 2:
            print(f"• ⚠️  CRITICAL: Senior review capacity constrains this junior-heavy team")  
            print(f"• Consider: Hire seniors, promote mids, or limit AI to {max(20, int(result['adoption']*0.7))}%")
        else:
            print(f"• Focus on relieving the {result['bottleneck'].replace('_', ' ')} bottleneck")
    
    print(f"\n• Expected monthly profit: ${result['monthly_profit']:,.0f}")
    
    if result.get('toc_optimization', False):
        print(f"\n{GREEN}💡 ToC Insight: This optimization focuses on system throughput via constraint management,")
        print(f"   not global AI adoption maximization. More economically sound approach.{RESET}")


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
    
    result = find_optimal_using_toc(args.team, args.cost, args.automation, args.deploy,
                                   args.senior_ratio, args.junior_ratio)
    
    display_results(result, args.team, args.cost, args.automation, args.deploy,
                   args.senior_ratio, args.junior_ratio)
    
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()