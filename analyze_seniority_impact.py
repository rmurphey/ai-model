#!/usr/bin/env python3
"""
Seniority Impact Analysis - Show how team seniority distribution affects AI ROI.
Demonstrates why junior-heavy teams often see higher AI value.
"""

import argparse
import sys
from tabulate import tabulate
from dataclasses import dataclass
from typing import Dict, List
import numpy as np

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
class SeniorityProfile:
    """Team seniority profile."""
    name: str
    junior_ratio: float
    mid_ratio: float  
    senior_ratio: float
    description: str


def calculate_seniority_impact(profile: SeniorityProfile, team_size: int, 
                               ai_adoption: float, cost_per_seat: float = 100) -> Dict:
    """Calculate AI impact with realistic senior developer constraints."""
    
    # Seniority-based AI effectiveness multipliers
    junior_ai_multiplier = 2.0  # Juniors get 100% productivity boost
    mid_ai_multiplier = 1.3     # Mid-level gets 30% boost
    senior_ai_multiplier = 1.1  # Seniors get 10% boost
    
    # Seniority-based salaries (affects value calculation)
    junior_salary = 90000
    mid_salary = 130000
    senior_salary = 180000
    
    # Calculate team composition
    junior_count = int(team_size * profile.junior_ratio)
    mid_count = int(team_size * profile.mid_ratio)
    senior_count = max(1, team_size - junior_count - mid_count)  # At least 1 senior
    
    # CRITICAL: Senior developer constraint analysis
    # Each senior can review ~40 PRs per month effectively
    reviews_per_senior_per_month = 40
    max_review_capacity = senior_count * reviews_per_senior_per_month
    
    # AI increases PR volume from juniors (they code faster with AI)
    base_prs_per_junior = 8  # PRs per junior per month
    ai_pr_multiplier = 1 + ai_adoption * 0.6  # AI increases PR volume by up to 60%
    junior_pr_load = junior_count * base_prs_per_junior * ai_pr_multiplier
    
    # Mid-level and senior PR loads (less affected by AI)
    mid_pr_load = mid_count * 6  # PRs per mid per month
    senior_pr_load = senior_count * 4  # PRs per senior per month
    
    total_pr_load = junior_pr_load + mid_pr_load + senior_pr_load
    review_utilization = total_pr_load / max_review_capacity if max_review_capacity > 0 else 0
    
    # Review constraint factor - reduces productivity when seniors are overloaded
    if review_utilization > 1.0:
        # Review capacity constrains team - major bottleneck for junior-heavy teams
        review_constraint_factor = max(0.3, max_review_capacity / total_pr_load)
    elif review_utilization > 0.8:
        # High utilization reduces review quality and slows reviews
        utilization_penalty = (review_utilization - 0.8) * 2  # Exponential penalty
        review_constraint_factor = 1.0 - utilization_penalty * 0.3
    else:
        review_constraint_factor = 1.0
    
    # AI effectiveness by level with constraint factor applied
    junior_productivity_gain = (junior_ai_multiplier - 1) * ai_adoption * review_constraint_factor
    mid_productivity_gain = (mid_ai_multiplier - 1) * ai_adoption * review_constraint_factor
    senior_productivity_gain = (senior_ai_multiplier - 1) * ai_adoption  # Seniors not as constrained
    
    # Weighted average productivity gain
    weighted_productivity = (
        profile.junior_ratio * junior_productivity_gain +
        profile.mid_ratio * mid_productivity_gain +
        profile.senior_ratio * senior_productivity_gain
    )
    
    # Value calculation based on salary-weighted productivity
    monthly_costs = {
        'junior': junior_count * junior_salary / 12,
        'mid': mid_count * mid_salary / 12,
        'senior': senior_count * senior_salary / 12
    }
    
    total_monthly_salary = sum(monthly_costs.values())
    
    # Productivity value by seniority level
    junior_value = monthly_costs['junior'] * junior_productivity_gain
    mid_value = monthly_costs['mid'] * mid_productivity_gain
    senior_value = monthly_costs['senior'] * senior_productivity_gain
    
    total_productivity_value = junior_value + mid_value + senior_value
    
    # AI adoption factors by seniority
    # Juniors adopt faster, seniors more resistant
    junior_adoption_rate = ai_adoption * 1.2  # 20% higher
    mid_adoption_rate = ai_adoption * 1.0     # Baseline
    senior_adoption_rate = ai_adoption * 0.7  # 30% lower
    
    # Effective team adoption (weighted by actual usage)
    effective_adoption = (
        profile.junior_ratio * junior_adoption_rate +
        profile.mid_ratio * mid_adoption_rate +
        profile.senior_ratio * senior_adoption_rate
    )
    
    # Technical debt accumulation (major factor for junior-heavy teams)
    debt_accumulation_rate = (
        profile.junior_ratio * 2.5 +  # Juniors create more debt
        profile.mid_ratio * 1.0 +     # Mid-level baseline
        profile.senior_ratio * 0.3    # Seniors create less debt
    ) * (1 + ai_adoption * 0.4)  # AI can amplify poor decisions
    
    # Technical debt drag on velocity (compounding over time)
    debt_drag = debt_accumulation_rate * total_monthly_salary * 0.12  # 12% velocity drag
    
    # Quality impact - seniors provide quality gates
    senior_quality_protection = profile.senior_ratio * 0.6  # Seniors catch mistakes
    base_quality_risk = 0.12 - senior_quality_protection  # Seniors reduce risk
    quality_penalty = total_productivity_value * max(0.02, base_quality_risk) * ai_adoption
    
    # Learning acceleration value (juniors benefit most from AI)
    # But constrained by review bottlenecks
    base_learning_value = (
        junior_count * 2000 * ai_adoption +  # $2k/month learning boost per junior
        mid_count * 500 * ai_adoption +      # $500/month for mid-level
        senior_count * 100 * ai_adoption     # $100/month for seniors
    )
    # Apply review constraint to learning value (can't learn if PRs are blocked)
    learning_value = base_learning_value * review_constraint_factor
    
    # Mentoring overhead - realistic constraint for junior-heavy teams
    if junior_count > senior_count:
        # Junior-heavy teams require significant mentoring 
        mentoring_hours_per_junior = 8  # hours per month per junior
        mentoring_cost_per_hour = senior_salary / (12 * 160)  # Senior hourly rate
        mentoring_overhead = junior_count * mentoring_hours_per_junior * mentoring_cost_per_hour * ai_adoption
    else:
        # Balanced teams have lower mentoring overhead
        mentoring_overhead = junior_count * 500 * ai_adoption
    
    # AI tool costs
    ai_cost = team_size * cost_per_seat * effective_adoption
    
    # Net calculations with all constraints
    gross_value = total_productivity_value + learning_value
    net_value = gross_value - debt_drag - quality_penalty - mentoring_overhead
    monthly_profit = net_value - ai_cost
    
    roi = (monthly_profit / ai_cost * 100) if ai_cost > 0 else 0
    
    return {
        'profile': profile,
        'team_composition': {
            'junior': junior_count,
            'mid': mid_count,  
            'senior': senior_count
        },
        'productivity_gains': {
            'junior': junior_productivity_gain,
            'mid': mid_productivity_gain,
            'senior': senior_productivity_gain,
            'weighted_average': weighted_productivity
        },
        'adoption_rates': {
            'junior': junior_adoption_rate,
            'mid': mid_adoption_rate,
            'senior': senior_adoption_rate,
            'effective': effective_adoption
        },
        'value_components': {
            'junior_value': junior_value,
            'mid_value': mid_value,
            'senior_value': senior_value,
            'productivity_value': total_productivity_value,
            'learning_value': learning_value,
            'gross_value': gross_value
        },
        'constraints': {
            'max_review_capacity': max_review_capacity,
            'junior_pr_load': junior_pr_load,
            'total_pr_load': total_pr_load,
            'review_utilization': review_utilization,
            'review_constraint_factor': review_constraint_factor,
            'debt_accumulation_rate': debt_accumulation_rate
        },
        'risk_factors': {
            'quality_penalty': quality_penalty,
            'debt_drag': debt_drag,
            'mentoring_overhead': mentoring_overhead,
            'senior_quality_protection': senior_quality_protection,
            'base_quality_risk': base_quality_risk
        },
        'financials': {
            'monthly_salary_cost': total_monthly_salary,
            'ai_cost': ai_cost,
            'net_value': net_value,
            'monthly_profit': monthly_profit,
            'roi': roi,
            'payback_months': ai_cost / monthly_profit if monthly_profit > 0 else 999
        }
    }


def create_seniority_profiles() -> List[SeniorityProfile]:
    """Create different seniority profiles for comparison."""
    return [
        SeniorityProfile(
            name="Junior Heavy",
            junior_ratio=0.6,
            mid_ratio=0.3,
            senior_ratio=0.1,
            description="Startup/growth team, lots of new grads"
        ),
        SeniorityProfile(
            name="Balanced Team", 
            junior_ratio=0.3,
            mid_ratio=0.5,
            senior_ratio=0.2,
            description="Mature product team, mixed experience"
        ),
        SeniorityProfile(
            name="Senior Heavy",
            junior_ratio=0.1,
            mid_ratio=0.3,
            senior_ratio=0.6,
            description="Specialized/legacy team, experienced developers"
        ),
        SeniorityProfile(
            name="Mid-Level Focus",
            junior_ratio=0.2,
            mid_ratio=0.6,
            senior_ratio=0.2,
            description="Scale-up team, experienced but not senior-heavy"
        )
    ]


def display_seniority_analysis(results: List[Dict], team_size: int, ai_adoption: float):
    """Display seniority impact analysis with realistic constraints."""
    
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}SENIORITY IMPACT ANALYSIS WITH SENIOR DEVELOPER CONSTRAINTS{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")
    print(f"Team Size: {team_size} developers")
    print(f"AI Adoption Rate: {ai_adoption:.0%}\n")
    
    # Summary comparison with constraint metrics
    summary_data = []
    for result in results:
        p = result['profile']
        comp = result['team_composition']
        cons = result['constraints']
        
        summary_data.append([
            p.name,
            f"{comp['junior']}J/{comp['mid']}M/{comp['senior']}S",
            f"{cons['review_utilization']:.0%}",
            f"{cons['review_constraint_factor']:.1%}",
            f"{result['productivity_gains']['weighted_average']:.1%}",
            f"${result['financials']['monthly_profit']:,.0f}",
            f"{result['financials']['roi']:.0f}%"
        ])
    
    print(f"{BOLD}SENIORITY CONSTRAINT COMPARISON:{RESET}")
    headers = ["Profile", "Composition", "Review Load", "Constraint Factor", "Net Productivity", "Monthly Profit", "ROI"]
    print(tabulate(summary_data, headers=headers, tablefmt='simple'))
    print()
    
    # Detailed analysis
    for result in results:
        p = result['profile']
        comp = result['team_composition']
        cons = result['constraints']
        print(f"\n{BOLD}{p.name}:{RESET} {p.description}")
        print(f"  Team: {comp['senior']} Senior, {comp['mid']} Mid, {comp['junior']} Junior")
        
        # Constraint analysis first - this is the key insight
        print(f"\n{BOLD}Senior Developer Constraints:{RESET}")
        constraint_data = [
            ["Review Capacity", f"{cons['max_review_capacity']:.0f} PRs/month"],
            ["Junior PR Load", f"{cons['junior_pr_load']:.0f} PRs/month"],
            ["Total PR Load", f"{cons['total_pr_load']:.0f} PRs/month"],
            ["Review Utilization", f"{cons['review_utilization']:.1%}"],
            ["Constraint Factor", f"{cons['review_constraint_factor']:.1%}"],
            ["Debt Accumulation", f"{cons['debt_accumulation_rate']:.2f}/month"]
        ]
        print(tabulate(constraint_data, tablefmt='simple'))
        
        # Productivity by level (after constraints)
        prod = result['productivity_gains']
        print(f"\n{BOLD}Constrained Productivity Gains:{RESET}")
        prod_data = [
            ["Junior", f"{prod['junior']:.1%}"],
            ["Mid-level", f"{prod['mid']:.1%}"],  
            ["Senior", f"{prod['senior']:.1%}"],
            ["Weighted Average", f"{prod['weighted_average']:.1%}"]
        ]
        print(tabulate(prod_data, tablefmt='simple'))
        
        # Financial impact with all constraints  
        val = result['value_components']
        risk = result['risk_factors']
        fin = result['financials']
        
        print(f"\n{BOLD}Financial Impact:{RESET}")
        value_data = [
            ["Productivity Value", f"${val['productivity_value']:,.0f}"],
            ["Learning Value (Constrained)", f"${val['learning_value']:,.0f}"],
            ["Gross Value", f"${val['gross_value']:,.0f}"],
            ["", ""],
            ["Technical Debt Drag", f"-${risk['debt_drag']:,.0f}"],
            ["Quality Penalty", f"-${risk['quality_penalty']:,.0f}"],
            ["Mentoring Overhead", f"-${risk['mentoring_overhead']:,.0f}"],
            ["Net Value", f"${fin['net_value']:,.0f}"],
            ["", ""],
            ["AI Tool Cost", f"${fin['ai_cost']:,.0f}"],
            ["Monthly Profit", f"${fin['monthly_profit']:,.0f}"],
            ["ROI", f"{fin['roi']:.0f}%"]
        ]
        print(tabulate(value_data, tablefmt='simple'))
    
    # Key insights with constraint focus
    print(f"\n{BOLD}KEY CONSTRAINT INSIGHTS:{RESET}")
    
    best_roi = max(results, key=lambda r: r['financials']['roi'])
    best_profit = max(results, key=lambda r: r['financials']['monthly_profit'])
    most_constrained = max(results, key=lambda r: r['constraints']['review_utilization'])
    highest_debt = max(results, key=lambda r: r['constraints']['debt_accumulation_rate'])
    
    print(f"✅ Highest ROI: {GREEN}{best_roi['profile'].name}{RESET} at {best_roi['financials']['roi']:.0f}%")
    print(f"💰 Highest Profit: {GREEN}{best_profit['profile'].name}{RESET} at ${best_profit['financials']['monthly_profit']:,.0f}/month")  
    print(f"⚠️  Most Constrained: {RED}{most_constrained['profile'].name}{RESET} with {most_constrained['constraints']['review_utilization']:.0%} review utilization")
    print(f"📈 Highest Debt Risk: {YELLOW}{highest_debt['profile'].name}{RESET} with {highest_debt['constraints']['debt_accumulation_rate']:.1f} debt/month")
    
    # Constraint-specific insights
    junior_heavy = next(r for r in results if r['profile'].name == "Junior Heavy")
    senior_heavy = next(r for r in results if r['profile'].name == "Senior Heavy")
    
    print(f"\n{BOLD}SENIOR DEVELOPER CONSTRAINT REALITY:{RESET}")
    print(f"🚨 {RED}Junior-heavy teams are severely constrained by senior review capacity{RESET}")
    print(f"   • Junior-heavy review utilization: {junior_heavy['constraints']['review_utilization']:.0%}")
    print(f"   • Constraint factor reduces productivity to: {junior_heavy['constraints']['review_constraint_factor']:.1%}")
    print(f"   • Technical debt accumulation: {junior_heavy['constraints']['debt_accumulation_rate']:.1f}/month")
    
    print(f"\n📊 Senior-heavy teams have capacity buffer:")
    print(f"   • Senior-heavy review utilization: {senior_heavy['constraints']['review_utilization']:.0%}")
    print(f"   • Less productivity constraint: {senior_heavy['constraints']['review_constraint_factor']:.1%}")
    print(f"   • Lower technical debt risk: {senior_heavy['constraints']['debt_accumulation_rate']:.1f}/month")
    
    print(f"\n💡 {BOLD}CRITICAL FINDING:{RESET}")
    print(f"The common belief that 'junior-heavy teams achieve higher AI ROI' is often false")
    print(f"due to senior developer review capacity constraints and technical debt accumulation.")
    print(f"ROI difference after constraints: {abs(junior_heavy['financials']['roi'] - senior_heavy['financials']['roi']):.0f} percentage points")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze how team seniority affects AI tool ROI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Shows how different seniority distributions affect AI tool value:

Junior Heavy (60% junior): High ROI due to learning acceleration
Balanced Team (30% junior): Moderate ROI with balanced risk
Senior Heavy (10% junior): Lower ROI but better quality control  
Mid-Level Focus (20% junior): Good balance of productivity and stability

Examples:
  python analyze_seniority_impact.py --team 25
  python analyze_seniority_impact.py --team 50 --adoption 0.7
  python analyze_seniority_impact.py --team 100 --cost 150
        """
    )
    
    parser.add_argument('--team', type=int, required=True, help='Team size')
    parser.add_argument('--adoption', type=float, default=0.5,
                       help='AI adoption rate (0.0-1.0, default: 0.5)')
    parser.add_argument('--cost', type=float, default=100,
                       help='AI tool cost per seat/month (default: $100)')
    
    args = parser.parse_args()
    
    if not 0.0 <= args.adoption <= 1.0:
        print(f"{RED}Error: Adoption rate must be between 0.0 and 1.0{RESET}")
        sys.exit(1)
    
    print(f"\n{BOLD}Analyzing seniority impact on AI ROI...{RESET}")
    
    profiles = create_seniority_profiles()
    results = []
    
    for profile in profiles:
        result = calculate_seniority_impact(profile, args.team, args.adoption, args.cost)
        results.append(result)
    
    display_seniority_analysis(results, args.team, args.adoption)
    
    sys.exit(0)


if __name__ == "__main__":
    main()