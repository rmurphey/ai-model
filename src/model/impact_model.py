"""
Business impact model for AI-assisted development.
Calculates the value created through various improvement vectors.
Now integrated with delivery pipeline model for end-to-end value calculation.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
from .baseline import BaselineMetrics
from .delivery_pipeline import DeliveryPipeline, create_standard_pipeline
from .test_strategy import CompleteTestStrategy, create_basic_test_strategy
from ..utils.math_helpers import safe_divide, validate_positive, validate_ratio
from ..utils.exceptions import CalculationError, ValidationError
from ..config.constants import (
    WORKING_DAYS_PER_YEAR, WORKING_HOURS_PER_YEAR, DEFAULT_TURNOVER_RATE,
    TECH_DEBT_MULTIPLIER, INNOVATION_CAPACITY_PERCENTAGE, COMPETITIVE_VALUE_MULTIPLIER,
    BUGS_PER_INCIDENT, HOURS_PER_DEFECT_FIX, KLOC_PER_TEAM_PER_YEAR, JUNIOR_EFFECTIVENESS_BOOST,
    CONTEXT_SWITCHING_PRODUCTIVITY_LOSS, RETENTION_MULTIPLIER
)

@dataclass 
class ImpactFactors:
    """Impact multipliers for different aspects of development"""
    
    # Time-to-value improvements (as reduction ratios)
    feature_cycle_reduction: float      # e.g., 0.3 = 30% faster
    bug_fix_reduction: float            # e.g., 0.4 = 40% faster
    onboarding_reduction: float         # e.g., 0.5 = 50% faster
    pr_review_reduction: float          # e.g., 0.6 = 60% faster
    
    # Quality improvements (as reduction ratios)
    defect_reduction: float             # e.g., 0.4 = 40% fewer defects
    incident_reduction: float           # e.g., 0.3 = 30% fewer incidents
    rework_reduction: float             # e.g., 0.5 = 50% less rework
    
    # Capacity reallocation (percentage point changes)
    feature_capacity_gain: float        # e.g., 0.1 = 10pp more on features
    tech_debt_capacity_gain: float      # e.g., 0.05 = 5pp more on tech debt
    
    # Task-specific adoption effectiveness
    boilerplate_effectiveness: float    # How well AI handles boilerplate
    test_generation_effectiveness: float # How well AI generates tests
    documentation_effectiveness: float   # How well AI writes docs
    code_review_effectiveness: float     # How well AI assists reviews
    debugging_effectiveness: float       # How well AI helps debug
    
    # Developer segment multipliers
    junior_multiplier: float            # Impact multiplier for juniors
    mid_multiplier: float               # Impact multiplier for mid-level
    senior_multiplier: float            # Impact multiplier for seniors
    
    def __post_init__(self):
        """Validate all impact factors"""
        # Validate reduction ratios (0-1)
        validate_ratio(self.feature_cycle_reduction, "feature_cycle_reduction")
        validate_ratio(self.bug_fix_reduction, "bug_fix_reduction")
        validate_ratio(self.onboarding_reduction, "onboarding_reduction")
        validate_ratio(self.pr_review_reduction, "pr_review_reduction")
        validate_ratio(self.defect_reduction, "defect_reduction")
        validate_ratio(self.incident_reduction, "incident_reduction")
        validate_ratio(self.rework_reduction, "rework_reduction")
        
        # Validate capacity gains (can be negative, but reasonable bounds)
        validate_ratio(self.feature_capacity_gain, "feature_capacity_gain", min_val=-0.5, max_val=0.5)
        validate_ratio(self.tech_debt_capacity_gain, "tech_debt_capacity_gain", min_val=-0.5, max_val=0.5)
        
        # Validate effectiveness ratios (0-1)
        validate_ratio(self.boilerplate_effectiveness, "boilerplate_effectiveness")
        validate_ratio(self.test_generation_effectiveness, "test_generation_effectiveness")
        validate_ratio(self.documentation_effectiveness, "documentation_effectiveness")
        validate_ratio(self.code_review_effectiveness, "code_review_effectiveness")
        validate_ratio(self.debugging_effectiveness, "debugging_effectiveness")
        
        # Validate multipliers (should be positive, typically 0.5-3.0)
        validate_ratio(self.junior_multiplier, "junior_multiplier", min_val=0.1, max_val=5.0)
        validate_ratio(self.mid_multiplier, "mid_multiplier", min_val=0.1, max_val=5.0)
        validate_ratio(self.senior_multiplier, "senior_multiplier", min_val=0.1, max_val=5.0)


@dataclass
class BusinessImpact:
    """Calculated business impact from AI adoption"""
    
    baseline: BaselineMetrics
    factors: ImpactFactors
    adoption_rate: float  # Overall adoption rate (0-1)
    pipeline: Optional[DeliveryPipeline] = None  # Optional delivery pipeline
    test_strategy: Optional[CompleteTestStrategy] = None  # Optional test strategy
    
    def calculate_time_value(self) -> Dict[str, float]:
        """Calculate value from time-to-market improvements"""
        
        # Feature delivery acceleration
        new_cycle_days = self.baseline.avg_feature_cycle_days * (
            1 - self.factors.feature_cycle_reduction * self.adoption_rate
        )
        old_features_per_dev = self.baseline.feature_delivery_rate
        new_features_per_dev = safe_divide(
            WORKING_DAYS_PER_YEAR * self.baseline.new_feature_percentage,
            new_cycle_days,
            default=0.0,
            context="new features per developer calculation"
        )
        
        # Additional features delivered
        additional_features = (new_features_per_dev - old_features_per_dev) * self.baseline.team_size
        
        # Value of additional features (using cost per feature as proxy)
        baseline_efficiency = self.baseline.calculate_baseline_efficiency()
        feature_value = additional_features * baseline_efficiency["cost_per_feature"]
        
        # Bug fix acceleration value (reduced downtime and customer impact)
        bug_fix_improvement = self.baseline.avg_bug_fix_hours * self.factors.bug_fix_reduction * self.adoption_rate
        annual_bugs = self.baseline.production_incidents_per_month * 12 * BUGS_PER_INCIDENT
        bug_fix_value = safe_divide(
            bug_fix_improvement * self.baseline.avg_incident_cost * annual_bugs,
            80,  # 8 hours * 10 (denominator factor)
            default=0.0,
            context="bug fix value calculation"
        )
        
        # Onboarding acceleration (faster time to productivity)
        onboarding_improvement = self.baseline.onboarding_days * self.factors.onboarding_reduction * self.adoption_rate
        annual_hires = self.baseline.team_size * DEFAULT_TURNOVER_RATE
        onboarding_value = safe_divide(
            onboarding_improvement * self.baseline.weighted_avg_flc * annual_hires,
            WORKING_DAYS_PER_YEAR,
            default=0.0,
            context="onboarding value calculation"
        )
        
        return {
            "feature_acceleration_value": feature_value,
            "bug_fix_acceleration_value": bug_fix_value,
            "onboarding_acceleration_value": onboarding_value,
            "total_time_value": feature_value + bug_fix_value + onboarding_value
        }
    
    def calculate_quality_value(self) -> Dict[str, float]:
        """Calculate value from quality improvements"""
        
        # Reduced defects
        defect_reduction = self.baseline.defect_escape_rate * self.factors.defect_reduction * self.adoption_rate
        # Each defect costs hours to fix at weighted FLC
        defect_cost_per_kloc = defect_reduction * HOURS_PER_DEFECT_FIX * safe_divide(
            self.baseline.weighted_avg_flc,
            WORKING_HOURS_PER_YEAR,
            default=0.0,
            context="defect cost per KLOC calculation"
        )
        # Team produces KLOC per year
        defect_value = defect_cost_per_kloc * KLOC_PER_TEAM_PER_YEAR
        
        # Reduced incidents
        incident_reduction = self.baseline.production_incidents_per_month * self.factors.incident_reduction * self.adoption_rate
        incident_value = incident_reduction * 12 * self.baseline.avg_incident_cost
        
        # Reduced rework
        rework_reduction = self.baseline.rework_percentage * self.factors.rework_reduction * self.adoption_rate
        rework_value = self.baseline.total_team_cost * rework_reduction
        
        return {
            "defect_reduction_value": defect_value,
            "incident_reduction_value": incident_value,
            "rework_reduction_value": rework_value,
            "total_quality_value": defect_value + incident_value + rework_value
        }
    
    def calculate_capacity_value(self) -> Dict[str, float]:
        """Calculate value from capacity reallocation"""
        
        # More time on features
        feature_capacity_value = (
            self.factors.feature_capacity_gain * 
            self.adoption_rate * 
            self.baseline.total_team_cost
        )
        
        # More time on tech debt (prevents future costs)
        tech_debt_value = (
            self.factors.tech_debt_capacity_gain * 
            self.adoption_rate * 
            self.baseline.total_team_cost * 
            1.5  # Tech debt work has 1.5x multiplier for future value
        )
        
        # Less time in low-value activities
        context_switch_reduction = self.baseline.total_team_cost * 0.05 * self.adoption_rate
        
        return {
            "feature_capacity_value": feature_capacity_value,
            "tech_debt_value": tech_debt_value,
            "context_switch_value": context_switch_reduction,
            "total_capacity_value": feature_capacity_value + tech_debt_value + context_switch_reduction
        }
    
    def calculate_strategic_value(self) -> Dict[str, float]:
        """Calculate strategic and hard-to-quantify value"""
        
        # Developer satisfaction and retention
        # Assume 1% reduction in turnover saves 1 FTE replacement cost
        retention_value = self.baseline.weighted_avg_flc * 0.01 * self.adoption_rate * self.baseline.team_size
        
        # Innovation capacity (freed time for experimentation)
        innovation_hours = self.baseline.effective_capacity_hours * 0.1 * self.adoption_rate
        innovation_value = safe_divide(
            innovation_hours * self.baseline.weighted_avg_flc * self.baseline.team_size,
            2080,  # Working hours per year
            default=0.0,
            context="innovation value calculation"
        )
        
        # Competitive advantage (ability to ship faster than competitors)
        # Model as option value - worth 10% of feature acceleration value
        competitive_value = self.calculate_time_value()["feature_acceleration_value"] * 0.1
        
        # Knowledge democratization (juniors more effective)
        junior_boost = (
            self.baseline.junior_ratio * 
            self.baseline.team_size * 
            (self.factors.junior_multiplier - 1) * 
            self.adoption_rate * 
            self.baseline.junior_flc * 
            0.2  # 20% effectiveness boost
        )
        
        return {
            "retention_value": retention_value,
            "innovation_value": innovation_value,
            "competitive_value": competitive_value,
            "junior_boost_value": junior_boost,
            "total_strategic_value": retention_value + innovation_value + competitive_value + junior_boost
        }
    
    def calculate_pipeline_value(self) -> Dict[str, float]:
        """Calculate value using delivery pipeline model (true end-to-end value)"""
        if not self.pipeline:
            # Create default pipeline if not provided
            self.pipeline = create_standard_pipeline(
                team_size=self.baseline.team_size,
                test_automation=0.3,
                deployment_frequency="weekly"
            )
        
        # Calculate throughput metrics
        throughput = self.pipeline.calculate_throughput(self.adoption_rate)
        
        # Calculate lead time
        lead_time = self.pipeline.calculate_lead_time(self.adoption_rate)
        
        # Calculate quality impact
        quality = self.pipeline.calculate_quality_impact(self.adoption_rate)
        
        # Calculate value delivery
        value_delivery = self.pipeline.calculate_value_delivery(
            self.adoption_rate,
            feature_value=self.baseline.weighted_avg_flc / 12  # Monthly FLC as proxy for feature value
        )
        
        return {
            "throughput_per_day": throughput["throughput_per_day"],
            "bottleneck_stage": throughput["bottleneck_stage"],
            "total_lead_time_days": lead_time["total_lead_time_days"],
            "defects_in_production": quality["defects_in_production_per_100"],
            "net_value_per_day": value_delivery["net_value_per_day"],
            "value_efficiency": value_delivery["value_efficiency"],
            "annual_pipeline_value": value_delivery["value_after_incidents"] * WORKING_DAYS_PER_YEAR
        }
    
    def calculate_test_impact(self) -> Dict[str, float]:
        """Calculate impact of testing strategy on value delivery"""
        if not self.test_strategy:
            # Create default test strategy if not provided
            team_type = "startup" if self.baseline.team_size < 20 else \
                       "enterprise" if self.baseline.team_size > 100 else "balanced"
            self.test_strategy = create_basic_test_strategy(team_type)
        
        # Calculate comprehensive testing impact
        test_impact = self.test_strategy.calculate_comprehensive_impact(
            ai_adoption=self.adoption_rate,
            code_volume=1.0  # Normalized volume
        )
        
        return {
            "total_test_time": test_impact["total_cycle_time"],
            "defect_escape_rate": test_impact["defect_escape_rate"],
            "testing_confidence": test_impact["testing_confidence"],
            "testing_roi": test_impact["testing_roi"],
            "quality_score": test_impact["quality_score"]
        }
    
    def calculate_total_impact(self) -> Dict[str, float]:
        """Calculate total business impact"""
        
        # Traditional value calculations
        time_value = self.calculate_time_value()
        quality_value = self.calculate_quality_value()
        capacity_value = self.calculate_capacity_value()
        strategic_value = self.calculate_strategic_value()
        
        # Pipeline-based value (if available)
        pipeline_value = {}
        if self.pipeline:
            pipeline_value = self.calculate_pipeline_value()
        
        # Test impact (if available)
        test_impact = {}
        if self.test_strategy:
            test_impact = self.calculate_test_impact()
        
        # Use pipeline value if available, otherwise traditional calculation
        if pipeline_value:
            total_value = pipeline_value["annual_pipeline_value"]
        else:
            total_value = (
                time_value["total_time_value"] +
                quality_value["total_quality_value"] +
                capacity_value["total_capacity_value"] +
                strategic_value["total_strategic_value"]
            )
        
        result = {
            "time_value": time_value["total_time_value"],
            "quality_value": quality_value["total_quality_value"],
            "capacity_value": capacity_value["total_capacity_value"],
            "strategic_value": strategic_value["total_strategic_value"],
            "total_annual_value": total_value,
            "value_per_developer": safe_divide(
                total_value,
                self.baseline.team_size,
                default=0.0,
                context="value per developer calculation"
            ),
            "value_as_percent_of_cost": safe_divide(
                total_value * 100,
                self.baseline.total_team_cost,
                default=0.0,
                context="value as percent of cost calculation"
            )
        }
        
        # Add pipeline metrics if available
        if pipeline_value:
            result["pipeline_metrics"] = pipeline_value
        
        # Add test metrics if available
        if test_impact:
            result["test_metrics"] = test_impact
        
        return result
    
    def calculate_value(self, effective_adoption: np.ndarray, months: int) -> np.ndarray:
        """
        Calculate monthly value based on adoption curve.
        
        Args:
            effective_adoption: Array of monthly effective adoption rates
            months: Number of months to calculate
            
        Returns:
            Array of monthly value generated
        """
        monthly_value = np.zeros(months)
        
        for month in range(months):
            # Update adoption rate for this month
            self.adoption_rate = effective_adoption[month]
            
            # Calculate total impact for this month
            impact = self.calculate_total_impact()
            
            # Convert annual value to monthly value
            monthly_value[month] = impact["total_annual_value"] / 12
        
        return monthly_value
    
    def get_impact_breakdown(self, adoption_rate: float) -> Dict[str, float]:
        """
        Get detailed impact breakdown for a specific adoption rate.
        
        Args:
            adoption_rate: Adoption rate to calculate impact for
            
        Returns:
            Dictionary with detailed impact breakdown
        """
        # Update adoption rate
        self.adoption_rate = adoption_rate
        
        # Calculate and return total impact
        return self.calculate_total_impact()


def create_impact_scenario(scenario_or_params = "moderate") -> ImpactFactors:
    """Create impact factors for different scenarios or custom parameters"""
    
    # If a dict is passed, check for 'scenario' key or use dict directly
    if isinstance(scenario_or_params, dict):
        if 'scenario' in scenario_or_params:
            scenario = scenario_or_params['scenario']
        else:
            # Custom parameters provided - create directly
            return ImpactFactors(**scenario_or_params)
    else:
        scenario = scenario_or_params
    
    scenarios = {
        "conservative": ImpactFactors(
            feature_cycle_reduction=0.10,
            bug_fix_reduction=0.15,
            onboarding_reduction=0.20,
            pr_review_reduction=0.30,
            defect_reduction=0.15,
            incident_reduction=0.10,
            rework_reduction=0.20,
            feature_capacity_gain=0.05,
            tech_debt_capacity_gain=0.02,
            boilerplate_effectiveness=0.70,
            test_generation_effectiveness=0.50,
            documentation_effectiveness=0.60,
            code_review_effectiveness=0.40,
            debugging_effectiveness=0.30,
            junior_multiplier=1.3,
            mid_multiplier=1.2,
            senior_multiplier=1.1
        ),
        
        "moderate": ImpactFactors(
            feature_cycle_reduction=0.25,
            bug_fix_reduction=0.35,
            onboarding_reduction=0.40,
            pr_review_reduction=0.50,
            defect_reduction=0.30,
            incident_reduction=0.25,
            rework_reduction=0.40,
            feature_capacity_gain=0.10,
            tech_debt_capacity_gain=0.05,
            boilerplate_effectiveness=0.85,
            test_generation_effectiveness=0.70,
            documentation_effectiveness=0.80,
            code_review_effectiveness=0.60,
            debugging_effectiveness=0.50,
            junior_multiplier=1.5,
            mid_multiplier=1.3,
            senior_multiplier=1.2
        ),
        
        "aggressive": ImpactFactors(
            feature_cycle_reduction=0.40,
            bug_fix_reduction=0.50,
            onboarding_reduction=0.60,
            pr_review_reduction=0.70,
            defect_reduction=0.45,
            incident_reduction=0.40,
            rework_reduction=0.60,
            feature_capacity_gain=0.15,
            tech_debt_capacity_gain=0.08,
            boilerplate_effectiveness=0.95,
            test_generation_effectiveness=0.85,
            documentation_effectiveness=0.90,
            code_review_effectiveness=0.75,
            debugging_effectiveness=0.70,
            junior_multiplier=1.8,
            mid_multiplier=1.5,
            senior_multiplier=1.3
        ),
        
        "realistic": ImpactFactors(
            feature_cycle_reduction=0.075,  # 7.5% average improvement
            bug_fix_reduction=0.10,         # 10% for bug fixes
            onboarding_reduction=0.05,      # 5% for onboarding
            pr_review_reduction=0.15,       # 15% for PR reviews
            defect_reduction=0.05,          # 5% quality improvement
            incident_reduction=0.03,        # 3% fewer incidents
            rework_reduction=0.08,          # 8% less rework
            feature_capacity_gain=0.02,     # 2% capacity gain
            tech_debt_capacity_gain=0.01,   # 1% tech debt capacity
            boilerplate_effectiveness=0.80, # 80% for highly automatable tasks
            test_generation_effectiveness=0.60,  # 60% for simple tests
            documentation_effectiveness=0.40,     # 40% for docs
            code_review_effectiveness=0.20,       # 20% for review assistance
            debugging_effectiveness=0.10,         # 10% for debugging
            junior_multiplier=1.2,          # Juniors benefit more
            mid_multiplier=1.0,             # Mids see baseline impact
            senior_multiplier=0.9           # Seniors benefit less
        )
    }
    
    return scenarios.get(scenario, scenarios["moderate"])


def calculate_task_specific_impact(
    baseline: BaselineMetrics,
    factors: ImpactFactors,
    task_distribution: Dict[str, float]
) -> Dict[str, float]:
    """Calculate impact based on task-specific effectiveness"""
    
    # Map tasks to effectiveness factors
    task_effectiveness = {
        "boilerplate": factors.boilerplate_effectiveness,
        "testing": factors.test_generation_effectiveness,
        "documentation": factors.documentation_effectiveness,
        "code_review": factors.code_review_effectiveness,
        "debugging": factors.debugging_effectiveness,
        "feature_development": 0.5,  # Average effectiveness
        "refactoring": 0.4,
        "architecture": 0.3
    }
    
    # Calculate weighted effectiveness
    total_effectiveness = sum(
        task_distribution.get(task, 0) * effectiveness
        for task, effectiveness in task_effectiveness.items()
    )
    
    # Calculate task-specific time savings
    time_savings = {}
    for task, percentage in task_distribution.items():
        effectiveness = task_effectiveness.get(task, 0.3)
        hours_on_task = baseline.effective_capacity_hours * percentage
        hours_saved = hours_on_task * effectiveness
        time_savings[task] = hours_saved * safe_divide(
            baseline.weighted_avg_flc,
            WORKING_HOURS_PER_YEAR,
            default=0.0,
            context=f"time savings calculation for {task}"
        )
    
    return {
        "weighted_effectiveness": total_effectiveness,
        "task_time_savings": time_savings,
        "total_task_value": sum(time_savings.values()) * baseline.team_size
    }