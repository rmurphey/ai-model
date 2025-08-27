#!/usr/bin/env python3
"""
Team Structure Impact Analysis - Compare no-QA vs QA teams.
Shows how team composition affects AI tool ROI.
"""

import argparse
import sys
from tabulate import tabulate
from dataclasses import dataclass
from typing import Dict, List

from src.model.test_strategy import create_basic_test_strategy
from src.model.delivery_pipeline import create_standard_pipeline

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


@dataclass
class TeamStructure:
    """Team structure configuration with automation maturity focus."""
    name: str
    team_size: int
    test_automation_maturity: float  # 0-1, level of test automation sophistication
    tdd_adoption: float = 0.3        # 0-1, extent of TDD practice adoption
    junior_ratio: float = 0.4
    mid_ratio: float = 0.4
    senior_ratio: float = 0.2
    avg_salary: int = 120000
    
    # Legacy QA ratio for backward compatibility (calculated from automation maturity)
    qa_ratio: float = None


def analyze_team_structure(structure: TeamStructure, ai_adoption: float = 0.5) -> Dict:
    """Analyze AI impact with realistic senior developer constraints and technical debt."""
    
    # Calculate legacy QA ratio for backward compatibility
    if structure.qa_ratio is None:
        structure.qa_ratio = max(0.0, (1.0 - structure.test_automation_maturity) * 0.3)
    
    # Determine team type based on automation maturity
    if structure.test_automation_maturity >= 0.7:
        team_type = "enterprise"
    elif structure.test_automation_maturity >= 0.5:
        team_type = "balanced" 
    else:
        team_type = "startup"
    
    # Get test strategy with new automation focus
    test_strategy = create_basic_test_strategy(team_type)
    
    # Calculate team composition
    team_composition = {
        'junior': int(structure.team_size * structure.junior_ratio),
        'mid': int(structure.team_size * structure.mid_ratio),
        'senior': max(1, int(structure.team_size * structure.senior_ratio))  # At least 1 senior
    }
    
    # Senior developer constraint analysis - THE KEY INSIGHT
    senior_count = team_composition['senior']
    junior_count = team_composition['junior']
    
    # Code review capacity constraint (realistic senior limits)
    reviews_per_senior_per_month = 40
    max_review_capacity = senior_count * reviews_per_senior_per_month
    
    # Junior PR load increases with AI
    base_prs_per_junior = 8
    ai_pr_multiplier = 1 + ai_adoption * 0.5
    junior_pr_load = junior_count * base_prs_per_junior * ai_pr_multiplier
    
    # Review utilization and bottleneck detection
    total_prs = junior_pr_load + team_composition['mid'] * 6 + senior_count * 4
    review_utilization = total_prs / max_review_capacity if max_review_capacity > 0 else 0
    
    # Review bottleneck constraint on productivity
    if review_utilization > 1.0:
        # Review capacity constrains team - reduce effective productivity
        review_constraint_factor = min(1.0, max_review_capacity / total_prs)
    else:
        review_constraint_factor = 1.0
    
    # Calculate productivity with realistic constraints
    junior_productivity_gain = 1.8 * ai_adoption  # Juniors benefit most
    mid_productivity_gain = 1.3 * ai_adoption
    senior_productivity_gain = 1.1 * ai_adoption  # Seniors benefit least
    
    weighted_productivity_gain = (
        structure.junior_ratio * junior_productivity_gain +
        structure.mid_ratio * mid_productivity_gain +
        structure.senior_ratio * senior_productivity_gain
    ) * review_constraint_factor  # Apply review constraint
    
    # Technical debt impact for junior-heavy teams
    debt_accumulation_rate = (
        structure.junior_ratio * 2.0 +  # Juniors create more debt
        structure.mid_ratio * 1.0 +
        structure.senior_ratio * 0.3
    ) * (1 + ai_adoption * 0.5)  # AI can amplify poor decisions
    
    # Automation maturity reduces debt accumulation
    debt_prevention = structure.test_automation_maturity * 0.4
    net_debt_rate = max(0.1, debt_accumulation_rate - debt_prevention)
    
    # Quality impact based on automation maturity, not manual QA
    base_quality = (
        structure.test_automation_maturity * 0.4 +
        structure.tdd_adoption * 0.3 +
        (1.0 - structure.junior_ratio) * 0.3  # Senior presence helps quality
    )
    
    # AI disruption mitigated by automation and practices
    ai_quality_disruption = ai_adoption * (0.3 - structure.test_automation_maturity * 0.2)
    quality_multiplier = max(0.4, base_quality * (1 - ai_quality_disruption))
    
    # Calculate costs
    monthly_cost_per_seat = 100
    monthly_team_cost = structure.team_size * monthly_cost_per_seat * ai_adoption
    
    # Calculate value with constraints
    monthly_salary_cost = structure.team_size * structure.avg_salary / 12
    productivity_value = monthly_salary_cost * weighted_productivity_gain
    
    # AI testing value depends on automation gaps
    automation_gap = 1.0 - structure.test_automation_maturity
    ai_testing_value = (0.4 + automation_gap * 0.4) * (1 - ai_adoption * 0.2)  # Over-reliance risk
    testing_value = monthly_salary_cost * ai_testing_value * 0.15
    
    # Technical debt drag (major constraint for junior teams)
    debt_drag = net_debt_rate * monthly_salary_cost * 0.1
    
    # Mentoring overhead (senior time consumed by juniors)
    mentoring_overhead = (junior_count * 2000 * ai_adoption) if senior_count < junior_count else 0
    
    net_monthly_value = productivity_value + testing_value - debt_drag - mentoring_overhead
    monthly_profit = net_monthly_value - monthly_team_cost
    
    roi = (monthly_profit / monthly_team_cost * 100) if monthly_team_cost > 0 else 0
    
    return {
        'structure': structure,
        'team_composition': team_composition,
        'automation_maturity': structure.test_automation_maturity,
        'tdd_adoption': structure.tdd_adoption,
        'weighted_productivity_gain': weighted_productivity_gain,
        'review_constraint_factor': review_constraint_factor,
        'review_utilization': review_utilization,
        'max_review_capacity': max_review_capacity,
        'junior_pr_load': junior_pr_load,
        'debt_accumulation_rate': net_debt_rate,
        'quality_multiplier': quality_multiplier,
        'ai_testing_value': ai_testing_value,
        'monthly_cost': monthly_team_cost,
        'productivity_value': productivity_value,
        'testing_value': testing_value,
        'debt_drag': debt_drag,
        'mentoring_overhead': mentoring_overhead,
        'net_monthly_value': net_monthly_value,
        'monthly_profit': monthly_profit,
        'roi': roi,
        'payback_months': monthly_team_cost / monthly_profit if monthly_profit > 0 else 999,
        # Legacy compatibility
        'developer_testing_load': 0.20 + structure.tdd_adoption * 0.15,
        'quality_gate_strictness': structure.test_automation_maturity * 0.8
    }


def compare_team_structures(team_size: int, ai_adoption: float = 0.5) -> List[Dict]:
    """Compare different team structures based on automation maturity and seniority."""
    
    structures = [
        TeamStructure(
            name="Early Stage (Low Automation)",
            team_size=team_size,
            test_automation_maturity=0.3,  # Low automation maturity
            tdd_adoption=0.1,               # Minimal TDD
            junior_ratio=0.6,              # Junior-heavy
            mid_ratio=0.3,
            senior_ratio=0.1                # Few seniors - CONSTRAINT
        ),
        TeamStructure(
            name="Growing Team (Moderate Automation)",
            team_size=team_size,
            test_automation_maturity=0.5,  # Moderate automation
            tdd_adoption=0.25,              # Some TDD adoption
            junior_ratio=0.4,
            mid_ratio=0.4,
            senior_ratio=0.2
        ),
        TeamStructure(
            name="Mature Team (High Automation)",
            team_size=team_size,
            test_automation_maturity=0.8,  # High automation maturity
            tdd_adoption=0.4,               # Strong TDD practices
            junior_ratio=0.3,              # Fewer juniors
            mid_ratio=0.5,
            senior_ratio=0.2
        ),
        TeamStructure(
            name="Senior-Heavy Team (High Automation)",
            team_size=team_size,
            test_automation_maturity=0.8,  # High automation
            tdd_adoption=0.5,               # Very strong TDD
            junior_ratio=0.2,              # Fewer juniors
            mid_ratio=0.4,
            senior_ratio=0.4                # Many seniors - less constrained
        )
    ]
    
    results = []
    for structure in structures:
        result = analyze_team_structure(structure, ai_adoption)
        results.append(result)
    
    return results


def display_comparison(results: List[Dict], ai_adoption: float):
    """Display team structure comparison with realistic constraints."""
    
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}TEAM STRUCTURE IMPACT ANALYSIS WITH REALISTIC CONSTRAINTS{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")
    print(f"AI Adoption Rate: {ai_adoption:.0%}")
    print(f"Team Size: {results[0]['structure'].team_size} developers\n")
    
    # Summary table with new metrics
    summary_data = []
    for result in results:
        s = result['structure'] 
        comp = result['team_composition']
        
        summary_data.append([
            s.name,
            f"{comp['senior']}S/{comp['mid']}M/{comp['junior']}J",
            f"{result['automation_maturity']:.0%}",
            f"{result['review_utilization']:.0%}",
            f"{result['weighted_productivity_gain']:.1%}",
            f"${result['monthly_profit']:,.0f}",
            f"{result['roi']:.0f}%"
        ])
    
    print(f"{BOLD}TEAM STRUCTURE COMPARISON:{RESET}")
    headers = ["Team Type", "S/M/J Split", "Auto Maturity", "Review Load", "Net Productivity", "Monthly Profit", "ROI"]
    print(tabulate(summary_data, headers=headers, tablefmt='simple'))
    print()
    
    # Detailed analysis for each structure
    for result in results:
        s = result['structure']
        comp = result['team_composition']
        print(f"\n{BOLD}{s.name}:{RESET}")
        print(f"  Team: {comp['senior']} Senior, {comp['mid']} Mid, {comp['junior']} Junior")
        print(f"  Automation: {result['automation_maturity']:.0%}, TDD: {result['tdd_adoption']:.0%}")
        
        # Constraint analysis
        constraints = [
            ["Review Capacity", f"{result['max_review_capacity']:.0f} PRs/month"],
            ["Junior PR Load", f"{result['junior_pr_load']:.0f} PRs/month"],
            ["Review Utilization", f"{result['review_utilization']:.1%}"],
            ["Review Constraint Factor", f"{result['review_constraint_factor']:.1%}"],
            ["", ""],
            ["Debt Accumulation Rate", f"{result['debt_accumulation_rate']:.2f}/month"],
            ["Quality Multiplier", f"{result['quality_multiplier']:.2f}"],
            ["AI Testing Value", f"{result['ai_testing_value']:.1%}"],
        ]
        print(f"\n{BOLD}Constraints & Factors:{RESET}")
        print(tabulate(constraints, tablefmt='simple'))
        
        # Financial breakdown
        financial = [
            ["Productivity Value", f"${result['productivity_value']:,.0f}/month"],
            ["Testing Value", f"${result['testing_value']:,.0f}/month"],
            ["Debt Drag", f"-${result['debt_drag']:,.0f}/month"],
            ["Mentoring Overhead", f"-${result['mentoring_overhead']:,.0f}/month"],
            ["Net Value", f"${result['net_monthly_value']:,.0f}/month"],
            ["", ""],
            ["Monthly Cost", f"${result['monthly_cost']:,.0f}"],
            ["Monthly Profit", f"${result['monthly_profit']:,.0f}"],
            ["ROI", f"{result['roi']:.0f}%"]
        ]
        print(f"\n{BOLD}Financial Impact:{RESET}")
        print(tabulate(financial, tablefmt='simple'))
    
    # Key insights based on realistic constraints
    print(f"\n{BOLD}KEY INSIGHTS:{RESET}")
    
    best_roi = max(results, key=lambda r: r['roi'])
    best_profit = max(results, key=lambda r: r['monthly_profit'])
    most_constrained = max(results, key=lambda r: r['review_utilization'])
    highest_debt = max(results, key=lambda r: r['debt_accumulation_rate'])
    
    print(f"✅ Highest ROI: {GREEN}{best_roi['structure'].name}{RESET} at {best_roi['roi']:.0f}%")
    print(f"💰 Highest Profit: {GREEN}{best_profit['structure'].name}{RESET} at ${best_profit['monthly_profit']:,.0f}/month")
    print(f"⚠️  Most Review Constrained: {RED}{most_constrained['structure'].name}{RESET} at {most_constrained['review_utilization']:.0%} utilization")
    print(f"📈 Highest Debt Risk: {YELLOW}{highest_debt['structure'].name}{RESET} with {highest_debt['debt_accumulation_rate']:.1f} debt/month")
    
    # Constraint-specific insights
    junior_heavy = min(results, key=lambda r: r['team_composition']['senior'])
    senior_heavy = max(results, key=lambda r: r['team_composition']['senior'])
    
    print(f"\n{BOLD}SENIORITY CONSTRAINT ANALYSIS:{RESET}")
    print(f"• Junior-heavy teams ({junior_heavy['structure'].name}):")
    print(f"  → Review utilization: {junior_heavy['review_utilization']:.0%}")
    print(f"  → Constrained productivity: {junior_heavy['review_constraint_factor']:.1%}")
    print(f"  → High debt risk: {junior_heavy['debt_accumulation_rate']:.1f}/month")
    print(f"• Senior-heavy teams ({senior_heavy['structure'].name}):")
    print(f"  → Review utilization: {senior_heavy['review_utilization']:.0%}")
    print(f"  → Less constrained: {senior_heavy['review_constraint_factor']:.1%}")
    print(f"  → Lower debt risk: {senior_heavy['debt_accumulation_rate']:.1f}/month")
    
    print(f"\n{BOLD}AUTOMATION MATURITY IMPACT:{RESET}")
    high_auto = max(results, key=lambda r: r['automation_maturity'])
    low_auto = min(results, key=lambda r: r['automation_maturity'])
    
    print(f"• High automation ({high_auto['structure'].name}):")
    print(f"  → Better quality multiplier: {high_auto['quality_multiplier']:.2f}")
    print(f"  → Lower debt accumulation: {high_auto['debt_accumulation_rate']:.1f}/month")
    print(f"• Low automation ({low_auto['structure'].name}):")  
    print(f"  → Worse quality multiplier: {low_auto['quality_multiplier']:.2f}")
    print(f"  → Higher debt accumulation: {low_auto['debt_accumulation_rate']:.1f}/month")
    
    print(f"\n{BOLD}CRITICAL INSIGHT:{RESET}")
    print(f"🚨 {RED}Senior developer time is the primary constraint for junior-heavy teams{RESET}")
    print(f"📊 Automation maturity matters more than manual QA processes")
    print(f"⚖️  Technical debt accumulation creates long-term velocity drag")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze how team structure affects AI tool ROI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Compare different team structures:
- No QA: Developers handle all testing (common in startups)
- Minimal QA: 1-2 QA people for larger dev team  
- Embedded QA: QA integrated within development teams
- Dedicated QA: Separate QA department with formal processes

Examples:
  python analyze_team_structure.py --team 20
  python analyze_team_structure.py --team 50 --adoption 0.8
  python analyze_team_structure.py --team 100 --adoption 0.3
        """
    )
    
    parser.add_argument('--team', type=int, required=True, help='Team size')
    parser.add_argument('--adoption', type=float, default=0.5, 
                       help='AI adoption rate (0.0-1.0, default: 0.5)')
    
    args = parser.parse_args()
    
    if not 0.0 <= args.adoption <= 1.0:
        print(f"{RED}Error: Adoption rate must be between 0.0 and 1.0{RESET}")
        sys.exit(1)
    
    print(f"\n{BOLD}Analyzing team structure impact...{RESET}")
    
    results = compare_team_structures(args.team, args.adoption)
    display_comparison(results, args.adoption)
    
    sys.exit(0)


if __name__ == "__main__":
    main()