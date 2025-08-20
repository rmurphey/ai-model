"""
Business impact model for AI-assisted development.
Calculates the value created through various improvement vectors.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from .baseline import BaselineMetrics

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


@dataclass
class BusinessImpact:
    """Calculated business impact from AI adoption"""
    
    baseline: BaselineMetrics
    factors: ImpactFactors
    adoption_rate: float  # Overall adoption rate (0-1)
    
    def calculate_time_value(self) -> Dict[str, float]:
        """Calculate value from time-to-market improvements"""
        
        # Feature delivery acceleration
        new_cycle_days = self.baseline.avg_feature_cycle_days * (
            1 - self.factors.feature_cycle_reduction * self.adoption_rate
        )
        old_features_per_dev = self.baseline.feature_delivery_rate
        new_features_per_dev = 260 / new_cycle_days * self.baseline.new_feature_percentage
        
        # Additional features delivered
        additional_features = (new_features_per_dev - old_features_per_dev) * self.baseline.team_size
        
        # Value of additional features (using cost per feature as proxy)
        baseline_efficiency = self.baseline.calculate_baseline_efficiency()
        feature_value = additional_features * baseline_efficiency["cost_per_feature"]
        
        # Bug fix acceleration value (reduced downtime and customer impact)
        bug_fix_improvement = self.baseline.avg_bug_fix_hours * self.factors.bug_fix_reduction * self.adoption_rate
        annual_bugs = self.baseline.production_incidents_per_month * 12 * 3  # Assume 3 bugs per incident
        bug_fix_value = (bug_fix_improvement / 8) * (self.baseline.avg_incident_cost / 10) * annual_bugs
        
        # Onboarding acceleration (faster time to productivity)
        onboarding_improvement = self.baseline.onboarding_days * self.factors.onboarding_reduction * self.adoption_rate
        annual_hires = self.baseline.team_size * 0.2  # 20% turnover assumption
        onboarding_value = (onboarding_improvement / 260) * self.baseline.weighted_avg_flc * annual_hires
        
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
        # Assume each defect costs 10 hours to fix at weighted FLC
        defect_cost_per_kloc = defect_reduction * 10 * (self.baseline.weighted_avg_flc / 2080)
        # Assume team produces 100 KLOC per year
        defect_value = defect_cost_per_kloc * 100
        
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
        innovation_value = (innovation_hours / 2080) * self.baseline.weighted_avg_flc * self.baseline.team_size
        
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
    
    def calculate_total_impact(self) -> Dict[str, float]:
        """Calculate total business impact"""
        
        time_value = self.calculate_time_value()
        quality_value = self.calculate_quality_value()
        capacity_value = self.calculate_capacity_value()
        strategic_value = self.calculate_strategic_value()
        
        total_value = (
            time_value["total_time_value"] +
            quality_value["total_quality_value"] +
            capacity_value["total_capacity_value"] +
            strategic_value["total_strategic_value"]
        )
        
        return {
            "time_value": time_value["total_time_value"],
            "quality_value": quality_value["total_quality_value"],
            "capacity_value": capacity_value["total_capacity_value"],
            "strategic_value": strategic_value["total_strategic_value"],
            "total_annual_value": total_value,
            "value_per_developer": total_value / self.baseline.team_size,
            "value_as_percent_of_cost": (total_value / self.baseline.total_team_cost) * 100
        }


def create_impact_scenario(scenario: str = "moderate") -> ImpactFactors:
    """Create impact factors for different scenarios"""
    
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
        time_savings[task] = hours_saved * (baseline.weighted_avg_flc / 2080)
    
    return {
        "weighted_effectiveness": total_effectiveness,
        "task_time_savings": time_savings,
        "total_task_value": sum(time_savings.values()) * baseline.team_size
    }