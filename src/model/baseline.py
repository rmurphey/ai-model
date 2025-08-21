"""
Baseline metrics for current state assessment.
Establishes the "before AI" state to measure improvements against.
"""

from dataclasses import dataclass, fields
from typing import Dict, List, Optional
import numpy as np
from ..utils.math_helpers import safe_divide, validate_positive, validate_ratio, validate_ratios_sum_to_one
from ..utils.exceptions import CalculationError, ValidationError
from ..config.constants import (
    WORKING_DAYS_PER_YEAR, WORKING_HOURS_PER_YEAR, DEFAULT_TURNOVER_RATE,
    CONTEXT_SWITCHING_PRODUCTIVITY_LOSS, RATIO_SUM_TOLERANCE
)

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
        """Validate all input parameters"""
        # Validate positive values
        validate_positive(self.team_size, "team_size")
        validate_positive(self.junior_flc, "junior_flc")
        validate_positive(self.mid_flc, "mid_flc")
        validate_positive(self.senior_flc, "senior_flc")
        validate_positive(self.avg_feature_cycle_days, "avg_feature_cycle_days")
        validate_positive(self.avg_bug_fix_hours, "avg_bug_fix_hours")
        validate_positive(self.onboarding_days, "onboarding_days")
        validate_positive(self.defect_escape_rate, "defect_escape_rate", allow_zero=True)
        validate_positive(self.production_incidents_per_month, "production_incidents_per_month", allow_zero=True)
        validate_positive(self.avg_incident_cost, "avg_incident_cost", allow_zero=True)
        validate_positive(self.avg_pr_review_hours, "avg_pr_review_hours", allow_zero=True)
        
        # Validate ratios
        validate_ratio(self.junior_ratio, "junior_ratio")
        validate_ratio(self.mid_ratio, "mid_ratio")
        validate_ratio(self.senior_ratio, "senior_ratio")
        validate_ratio(self.rework_percentage, "rework_percentage")
        validate_ratio(self.new_feature_percentage, "new_feature_percentage")
        validate_ratio(self.maintenance_percentage, "maintenance_percentage")
        validate_ratio(self.tech_debt_percentage, "tech_debt_percentage")
        validate_ratio(self.meetings_percentage, "meetings_percentage")
        validate_ratio(self.pr_rejection_rate, "pr_rejection_rate")
        
        # Validate ratio groups sum to 1.0
        team_ratios = {
            "junior_ratio": self.junior_ratio,
            "mid_ratio": self.mid_ratio,
            "senior_ratio": self.senior_ratio
        }
        validate_ratios_sum_to_one(team_ratios, RATIO_SUM_TOLERANCE, "team composition")
        
        capacity_ratios = {
            "new_feature_percentage": self.new_feature_percentage,
            "maintenance_percentage": self.maintenance_percentage,
            "tech_debt_percentage": self.tech_debt_percentage,
            "meetings_percentage": self.meetings_percentage
        }
        validate_ratios_sum_to_one(capacity_ratios, RATIO_SUM_TOLERANCE, "capacity allocation")
    
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
        # Assume working hours per year, minus meetings
        return WORKING_HOURS_PER_YEAR * (1 - self.meetings_percentage)
    
    @property
    def feature_delivery_rate(self) -> float:
        """Features delivered per developer per year"""
        # Calculate based on cycle time and capacity
        working_days = WORKING_DAYS_PER_YEAR
        features_per_dev = safe_divide(
            working_days,
            self.avg_feature_cycle_days,
            default=0.0,
            context="features per developer calculation"
        )
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
        total_features = self.team_size * self.feature_delivery_rate
        return {
            "cost_per_feature": safe_divide(
                self.total_team_cost,
                total_features,
                default=0.0,
                context="cost per feature calculation"
            ),
            "incidents_per_feature": safe_divide(
                self.production_incidents_per_month * 12,
                total_features,
                default=0.0,
                context="incidents per feature calculation"
            ),
            "effective_utilization": self.new_feature_percentage,
            "quality_cost_ratio": safe_divide(
                self.annual_incident_cost + self.annual_rework_cost,
                self.total_team_cost,
                default=0.0,
                context="quality cost ratio calculation"
            )
        }


def create_industry_baseline(industry_or_params = "enterprise") -> BaselineMetrics:
    """Create baseline metrics based on industry benchmarks or custom parameters"""
    
    # If a dict is passed, check for 'profile' key or use dict directly
    if isinstance(industry_or_params, dict):
        if 'profile' in industry_or_params:
            industry = industry_or_params['profile']
        else:
            # Custom parameters provided - filter to valid fields only
            valid_fields = {f.name for f in fields(BaselineMetrics)}
            filtered_params = {k: v for k, v in industry_or_params.items() if k in valid_fields}
            
            # Handle 'other_percentage' as 'meetings_percentage' if present
            if 'other_percentage' in industry_or_params and 'meetings_percentage' not in filtered_params:
                filtered_params['meetings_percentage'] = industry_or_params['other_percentage']
            
            # Add default values for missing required fields
            defaults = {
                'meetings_percentage': 0.15,  # Default 15% time in meetings
                'pr_rejection_rate': 0.15      # Default 15% PR rejection rate
            }
            
            for field, default_value in defaults.items():
                if field not in filtered_params:
                    filtered_params[field] = default_value
            
            return BaselineMetrics(**filtered_params)
    else:
        industry = industry_or_params
    
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
            team_size=150,
            junior_ratio=0.25, mid_ratio=0.55, senior_ratio=0.2,
            junior_flc=140_000, mid_flc=190_000, senior_flc=275_000,
            avg_feature_cycle_days=28,
            avg_bug_fix_hours=8,
            onboarding_days=45,
            defect_escape_rate=4.0,
            production_incidents_per_month=12,
            avg_incident_cost=15_000,
            rework_percentage=0.12,
            new_feature_percentage=0.35,
            maintenance_percentage=0.45,
            tech_debt_percentage=0.10,
            meetings_percentage=0.10,
            avg_pr_review_hours=5,
            pr_rejection_rate=0.15
        ),
        
        "scale_up": BaselineMetrics(
            team_size=50,
            junior_ratio=0.35, mid_ratio=0.45, senior_ratio=0.2,
            junior_flc=125_000, mid_flc=170_000, senior_flc=235_000,
            avg_feature_cycle_days=20,
            avg_bug_fix_hours=5.5,
            onboarding_days=25,
            defect_escape_rate=5.5,
            production_incidents_per_month=7,
            avg_incident_cost=9_000,
            rework_percentage=0.16,
            new_feature_percentage=0.42,
            maintenance_percentage=0.38,
            tech_debt_percentage=0.13,
            meetings_percentage=0.07,
            avg_pr_review_hours=3.5,
            pr_rejection_rate=0.18
        )
    }
    
    return profiles.get(industry, profiles["enterprise"])


def calculate_opportunity_cost(baseline: BaselineMetrics) -> Dict[str, float]:
    """Calculate the opportunity cost of current inefficiencies"""
    
    # What could be gained if inefficiencies were eliminated?
    perfect_world_features = baseline.team_size * safe_divide(
        WORKING_DAYS_PER_YEAR,
        baseline.avg_feature_cycle_days,
        default=0.0,
        context="perfect world features calculation"
    )
    actual_features = baseline.team_size * baseline.feature_delivery_rate
    
    lost_features = perfect_world_features - actual_features
    lost_feature_value = lost_features * safe_divide(
        baseline.total_team_cost,
        actual_features,
        default=0.0,
        context="lost feature value calculation"
    )
    
    slow_onboarding_cost = safe_divide(
        baseline.onboarding_days,
        WORKING_DAYS_PER_YEAR,
        default=0.0,
        context="slow onboarding cost calculation"
    ) * baseline.weighted_avg_flc * (baseline.team_size * DEFAULT_TURNOVER_RATE)
    
    return {
        "lost_feature_value": lost_feature_value,
        "quality_costs": baseline.annual_incident_cost + baseline.annual_rework_cost,
        "slow_onboarding_cost": slow_onboarding_cost,
        "context_switching_cost": baseline.total_team_cost * CONTEXT_SWITCHING_PRODUCTIVITY_LOSS,
        "total_opportunity_cost": lost_feature_value + baseline.annual_incident_cost + 
                                 baseline.annual_rework_cost
    }