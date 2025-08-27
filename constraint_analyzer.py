#!/usr/bin/env python3
"""
Theory of Constraints analyzer for software delivery pipelines.
Implements Goldratt's Five Focusing Steps methodology.
"""

import argparse
import sys
from tabulate import tabulate
from typing import Dict, Any

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

from src.model.delivery_pipeline import create_standard_pipeline
from src.model.constraint_optimizer import ConstraintOptimizer
from src.model.technical_debt import create_debt_model


def analyze_constraints(team_size: int, 
                       cost_per_seat: float,
                       senior_ratio: float = 0.2,
                       junior_ratio: float = 0.4,
                       test_automation: float = 0.5,
                       deployment_freq: str = "weekly"):
    """
    Perform complete Theory of Constraints analysis on delivery pipeline.
    
    Implements Goldratt's Five Focusing Steps:
    1. Identify the constraint
    2. Exploit the constraint
    3. Subordinate everything to the constraint  
    4. Elevate the constraint
    5. Return to step 1 (avoid inertia)
    """
    
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
    
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}THEORY OF CONSTRAINTS ANALYSIS{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")
    
    print(f"{BOLD}Team Configuration:{RESET}")
    team_data = [
        ["Total Team Size", team_size],
        ["Senior Developers", f"{senior_count} ({senior_count/team_size:.0%})"],
        ["Mid-level Developers", f"{mid_count} ({mid_count/team_size:.0%})"],
        ["Junior Developers", f"{junior_count} ({junior_count/team_size:.0%})"],
        ["", ""],
        ["Test Automation", f"{test_automation:.0%}"],
        ["Deployment Frequency", deployment_freq],
        ["Cost per Seat", f"${cost_per_seat:,.0f}/month"],
    ]
    print(tabulate(team_data, tablefmt='simple'))
    print()
    
    # Apply Theory of Constraints optimization
    result = optimizer.optimize_for_constraint(team_composition, cost_per_seat)
    
    if not result:
        print(f"{RED}No profitable configuration found{RESET}")
        return None
    
    constraint_analysis = result['constraint_analysis']
    exploitation_result = result['exploitation_result']
    subordination_rules = result['subordination_rules']
    
    print(f"{BOLD}STEP 1: IDENTIFY THE CONSTRAINT{RESET}")
    print(f"🔍 {GREEN}Constraint identified: {constraint_analysis.constraint_type.value.upper()}{RESET}")
    print()
    
    constraint_data = [
        ["Constraint Stage", constraint_analysis.constraint_stage],
        ["Current Throughput", f"{constraint_analysis.current_throughput:.1f} features/month"],
        ["Constraint Utilization", f"{constraint_analysis.constraint_utilization:.1%}"],
        ["Improvement Potential", f"{constraint_analysis.improvement_potential:.1%}"],
        ["Daily Cost of Constraint", f"${constraint_analysis.cost_of_constraint:,.0f}"],
    ]
    print(tabulate(constraint_data, tablefmt='simple'))
    print()
    
    # Show stage throughputs and queue buildup
    print(f"{BOLD}Pipeline Stage Analysis:{RESET}")
    stage_data = []
    for stage, throughput in constraint_analysis.stage_throughputs.items():
        queue_buildup = constraint_analysis.queue_buildup.get(stage, 0)
        is_constraint = "🚫" if stage == constraint_analysis.constraint_stage else ""
        stage_data.append([
            f"{is_constraint} {stage.replace('_', ' ').title()}",
            f"{throughput:.1f}",
            f"{queue_buildup:.1f}" if queue_buildup > 0 else "-"
        ])
    
    print(tabulate(stage_data, 
                   headers=["Stage", "Throughput", "Queue Buildup"],
                   tablefmt='simple'))
    print()
    
    print(f"{BOLD}STEP 2: EXPLOIT THE CONSTRAINT{RESET}")
    print(f"⚡ {GREEN}Exploit without adding capacity{RESET}")
    print()
    
    print(f"Original Throughput: {exploitation_result['original_throughput']:.1f} features/month")
    print(f"After Exploitation: {exploitation_result['exploited_throughput']:.1f} features/month")
    print(f"Improvement: {YELLOW}{exploitation_result['improvement_percent']:.1f}%{RESET}")
    print(f"Implementation Cost: {GREEN}${exploitation_result['cost']:,}{RESET}")
    print(f"Timeline: {exploitation_result['timeline_days']} days")
    print()
    
    print("Exploitation Strategies:")
    for strategy in constraint_analysis.exploitation_strategies:
        print(f"  • {strategy}")
    print()
    
    print(f"{BOLD}STEP 3: SUBORDINATE EVERYTHING TO THE CONSTRAINT{RESET}")
    print(f"🎯 {GREEN}Align all resources to support the constraint{RESET}")
    print()
    
    if subordination_rules:
        subordination_data = []
        for rule in subordination_rules:
            subordination_data.append([
                rule.stage.value.replace('_', ' ').title(),
                rule.rule_type.title(),
                rule.rule_description,
                f"{rule.impact_factor:.1%}"
            ])
        
        print(tabulate(subordination_data,
                       headers=["Stage", "Rule Type", "Description", "Impact"],
                       tablefmt='simple'))
        
        total_subordination_benefit = sum(rule.impact_factor for rule in subordination_rules)
        print(f"\nTotal Subordination Benefit: {GREEN}{total_subordination_benefit:.1%}{RESET}")
    else:
        print("No subordination rules needed - constraint is well supported.")
    print()
    
    print(f"{BOLD}STEP 4: ELEVATE THE CONSTRAINT{RESET}")
    elevation_result = optimizer.elevate_constraint(constraint_analysis, team_composition)
    
    if elevation_result['recommended_strategy']:
        strategy = elevation_result['recommended_strategy']
        print(f"💰 {YELLOW}Recommended elevation strategy:{RESET}")
        print(f"  Strategy: {strategy['description']}")
        print(f"  Cost: ${strategy['cost']:,}")
        print(f"  Timeline: {strategy['timeline_days']} days")
        print(f"  Throughput Increase: +{strategy['throughput_increase']} features/month")
        
        # Calculate ROI
        monthly_cost = strategy['cost'] / 12
        monthly_value_increase = strategy['throughput_increase'] * 10000  # $10k per feature
        roi = (monthly_value_increase - monthly_cost) / monthly_cost * 100
        print(f"  ROI: {GREEN if roi > 20 else YELLOW}{roi:.0f}%{RESET}")
    else:
        print(f"{YELLOW}No elevation strategies needed at this time.{RESET}")
    print()
    
    print(f"{BOLD}STEP 5: CONTINUOUS IMPROVEMENT{RESET}")
    print(f"🔄 {GREEN}Repeat process as constraints shift{RESET}")
    print()
    
    # Show what happens after elevation
    if elevation_result['recommended_strategy']:
        print("After elevation, expect constraint to move to next bottleneck:")
        # Sort stages by throughput to predict next constraint
        sorted_stages = sorted(
            constraint_analysis.stage_throughputs.items(),
            key=lambda x: x[1]
        )
        next_constraint = sorted_stages[1][0] if len(sorted_stages) > 1 else "unknown"
        print(f"  Next likely constraint: {next_constraint.replace('_', ' ').title()}")
        print(f"  Recommended: Re-run analysis after elevation")
    print()
    
    print(f"{BOLD}FINANCIAL SUMMARY{RESET}")
    financial_data = [
        ["Optimal AI Adoption", f"{result['optimal_ai_adoption']:.0f}%"],
        ["Final Throughput", f"{result['final_throughput']:.1f} features/month"],
        ["Daily Value", f"${result['daily_value']:,.0f}"],
        ["Monthly Cost", f"${result['monthly_cost']:,.0f}"],
        ["Net Value per Day", f"${result['net_value_per_day']:,.0f}"],
        ["", ""],
        ["Approach", "Theory of Constraints (constraint-focused)"],
        ["vs Global Optimization", "Focuses on system throughput, not local efficiency"]
    ]
    print(tabulate(financial_data, tablefmt='simple'))
    print()
    
    # Key insights
    print(f"{BOLD}KEY INSIGHTS:{RESET}")
    
    if constraint_analysis.constraint_type.value == "code_review":
        print(f"🎯 {YELLOW}Code review constraint detected{RESET}")
        if junior_count > senior_count * 2:
            print(f"   ⚠️  Junior-heavy team - senior review capacity is critical bottleneck")
            print(f"   → Consider: hiring seniors, promoting mids, or optimizing review process")
        else:
            print(f"   → Focus on review tooling and process optimization before adding capacity")
    
    elif constraint_analysis.constraint_type.value == "testing":
        print(f"🎯 {YELLOW}Testing constraint detected{RESET}")
        print(f"   → Current automation: {test_automation:.0%}")
        print(f"   → Focus on test automation and parallel execution")
    
    # Theory of Constraints principle violations to avoid
    print(f"\n{BOLD}ToC PRINCIPLES TO REMEMBER:{RESET}")
    principles = [
        "Don't optimize non-constraints - it creates inventory, not throughput",
        "Constraint utilization determines system throughput",
        "An hour lost at the constraint is an hour lost for the entire system",
        "An hour saved at a non-constraint is a mirage",
        "Focus on flow, not local efficiency"
    ]
    
    for principle in principles:
        print(f"  • {principle}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Theory of Constraints analysis for software delivery',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Theory of Constraints applied to software delivery:

Goldratt's Five Focusing Steps:
1. Identify the constraint (bottleneck)
2. Exploit the constraint (optimize without adding capacity)  
3. Subordinate everything to the constraint
4. Elevate the constraint (add capacity if needed)
5. Return to step 1 (avoid inertia)

This approach focuses on system throughput rather than local optimization,
following the principle that the constraint determines system performance.

Examples:
  python constraint_analyzer.py --team 50 --cost 100
  python constraint_analyzer.py --team 20 --cost 50 --senior-ratio 0.3
  python constraint_analyzer.py --team 100 --cost 200 --automation 0.8
        """
    )
    
    parser.add_argument('--team', type=int, required=True, 
                       help='Team size')
    parser.add_argument('--cost', type=float, required=True,
                       help='Cost per seat/month')
    parser.add_argument('--senior-ratio', type=float, default=0.2,
                       help='Ratio of senior developers (0.0-1.0)')
    parser.add_argument('--junior-ratio', type=float, default=0.4,
                       help='Ratio of junior developers (0.0-1.0)')
    parser.add_argument('--automation', type=float, default=0.5,
                       help='Test automation level (0.0-1.0)')
    parser.add_argument('--deploy', choices=['daily', 'weekly', 'biweekly', 'monthly'],
                       default='weekly', help='Deployment frequency')
    
    args = parser.parse_args()
    
    # Validate ratios
    if args.senior_ratio + args.junior_ratio > 1.0:
        print(f"{RED}Error: Senior ratio + Junior ratio cannot exceed 1.0{RESET}")
        sys.exit(1)
    
    print(f"\n{BOLD}Theory of Constraints Analysis{RESET}")
    print(f"Team: {args.team} | Cost: ${args.cost}/seat | Automation: {args.automation:.0%}")
    print(f"Team Composition: {args.senior_ratio:.0%} Senior, {args.junior_ratio:.0%} Junior")
    
    result = analyze_constraints(
        team_size=args.team,
        cost_per_seat=args.cost,
        senior_ratio=args.senior_ratio,
        junior_ratio=args.junior_ratio,
        test_automation=args.automation,
        deployment_freq=args.deploy
    )
    
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()