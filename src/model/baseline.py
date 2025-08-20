"""
Baseline metrics for current state assessment.
Establishes the "before AI" state to measure improvements against.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

@dataclass
class BaselineMetrics:
    """Current state metrics before AI adoption"""
    
    # Team composition
    team_size: int
    junior_ratio: float  # % of team that is junior
    mid_ratio: float     # % of team that is mid-level
    senior_ratio: float  # % of team that is senior
    
    # Fully-loaded costs (annual)
    junior_flc: float    # Fully-loaded cost per junior dev
    mid_flc: float       # Fully-loaded cost per mid dev
    senior_flc: float    # Fully-loaded cost per senior dev
    
    # Time-to-value metrics
    avg_feature_cycle_days: float  # Days from requirement to production
    avg_bug_fix_hours: float       # Hours from report to fix
    onboarding_days: float          # Days for new dev to be productive
    
    # Quality metrics
    defect_escape_rate: float       # Defects per 1000 lines of code
    production_incidents_per_month: float
    avg_incident_cost: float        # Cost per production incident
    rework_percentage: float         # % of work that requires rework
    
    # Capacity allocation
    new_feature_percentage: float   # % time on new features
    maintenance_percentage: float    # % time on maintenance
    tech_debt_percentage: float      # % time on tech debt
    meetings_percentage: float       # % time in meetings/admin
    
    # Code review and collaboration
    avg_pr_review_hours: float      # Hours to review a PR
    pr_rejection_rate: float         # % of PRs requiring major rework
    
    def __post_init__(self):
        """Validate ratios sum to 1.0"""
        assert abs(self.junior_ratio + self.mid_ratio + self.senior_ratio - 1.0) < 0.01
        assert abs(self.new_feature_percentage + self.maintenance_percentage + 
                  self.tech_debt_percentage + self.meetings_percentage - 1.0) < 0.01
    
    @property
    def weighted_avg_flc(self) -> float:
        """Calculate weighted average fully-loaded cost"""
        return (self.junior_flc * self.junior_ratio +
                self.mid_flc * self.mid_ratio +
                self.senior_flc * self.senior_ratio)
    
    @property
    def total_team_cost(self) -> float:
        """Total annual cost for the team"""
        return self.team_size * self.weighted_avg_flc
    
    @property
    def effective_capacity_hours(self) -> float:
        """Effective annual coding hours per developer"""
        # Assume 2080 work hours/year, minus meetings
        return 2080 * (1 - self.meetings_percentage)
    
    @property
    def feature_delivery_rate(self) -> float:
        """Features delivered per developer per year"""
        # Calculate based on cycle time and capacity
        working_days = 260  # Typical working days per year
        features_per_dev = working_days / self.avg_feature_cycle_days
        # Adjust for time actually spent on features
        return features_per_dev * self.new_feature_percentage
    
    @property
    def annual_incident_cost(self) -> float:
        """Total annual cost of production incidents"""
        return self.production_incidents_per_month * 12 * self.avg_incident_cost
    
    @property
    def annual_rework_cost(self) -> float:
        """Annual cost of rework"""
        productive_cost = self.total_team_cost * (1 - self.meetings_percentage)
        return productive_cost * self.rework_percentage
    
    def calculate_baseline_efficiency(self) -> Dict[str, float]:
        """Calculate baseline efficiency metrics"""
        return {
            "cost_per_feature": self.total_team_cost / (self.team_size * self.feature_delivery_rate),
            "incidents_per_feature": (self.production_incidents_per_month * 12) / 
                                    (self.team_size * self.feature_delivery_rate),
            "effective_utilization": self.new_feature_percentage,
            "quality_cost_ratio": (self.annual_incident_cost + self.annual_rework_cost) / 
                                 self.total_team_cost
        }


def create_industry_baseline(industry: str = "enterprise") -> BaselineMetrics:
    """Create baseline metrics based on industry benchmarks"""
    
    profiles = {
        "startup": BaselineMetrics(
            team_size=10,
            junior_ratio=0.4, mid_ratio=0.4, senior_ratio=0.2,
            junior_flc=120_000, mid_flc=160_000, senior_flc=220_000,
            avg_feature_cycle_days=14,
            avg_bug_fix_hours=8,
            onboarding_days=30,
            defect_escape_rate=5.0,
            production_incidents_per_month=3,
            avg_incident_cost=5_000,
            rework_percentage=0.15,
            new_feature_percentage=0.60,
            maintenance_percentage=0.20,
            tech_debt_percentage=0.05,
            meetings_percentage=0.15,
            avg_pr_review_hours=2,
            pr_rejection_rate=0.20
        ),
        
        "enterprise": BaselineMetrics(
            team_size=50,
            junior_ratio=0.3, mid_ratio=0.5, senior_ratio=0.2,
            junior_flc=140_000, mid_flc=180_000, senior_flc=250_000,
            avg_feature_cycle_days=30,
            avg_bug_fix_hours=24,
            onboarding_days=60,
            defect_escape_rate=3.0,
            production_incidents_per_month=5,
            avg_incident_cost=15_000,
            rework_percentage=0.20,
            new_feature_percentage=0.40,
            maintenance_percentage=0.35,
            tech_debt_percentage=0.10,
            meetings_percentage=0.15,
            avg_pr_review_hours=4,
            pr_rejection_rate=0.25
        ),
        
        "scale_up": BaselineMetrics(
            team_size=25,
            junior_ratio=0.35, mid_ratio=0.45, senior_ratio=0.2,
            junior_flc=130_000, mid_flc=170_000, senior_flc=230_000,
            avg_feature_cycle_days=21,
            avg_bug_fix_hours=12,
            onboarding_days=45,
            defect_escape_rate=4.0,
            production_incidents_per_month=4,
            avg_incident_cost=10_000,
            rework_percentage=0.18,
            new_feature_percentage=0.50,
            maintenance_percentage=0.28,
            tech_debt_percentage=0.07,
            meetings_percentage=0.15,
            avg_pr_review_hours=3,
            pr_rejection_rate=0.22
        )
    }
    
    return profiles.get(industry, profiles["enterprise"])


def calculate_opportunity_cost(baseline: BaselineMetrics) -> Dict[str, float]:
    """Calculate the opportunity cost of current inefficiencies"""
    
    # What could be gained if inefficiencies were eliminated?
    perfect_world_features = baseline.team_size * 260 / baseline.avg_feature_cycle_days
    actual_features = baseline.team_size * baseline.feature_delivery_rate
    
    lost_features = perfect_world_features - actual_features
    lost_feature_value = lost_features * (baseline.total_team_cost / actual_features)
    
    return {
        "lost_feature_value": lost_feature_value,
        "quality_costs": baseline.annual_incident_cost + baseline.annual_rework_cost,
        "slow_onboarding_cost": (baseline.onboarding_days / 260) * baseline.weighted_avg_flc * 
                               (baseline.team_size * 0.2),  # Assume 20% turnover
        "context_switching_cost": baseline.total_team_cost * 0.1,  # Estimate 10% productivity loss
        "total_opportunity_cost": lost_feature_value + baseline.annual_incident_cost + 
                                 baseline.annual_rework_cost
    }