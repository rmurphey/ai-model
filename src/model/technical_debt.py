"""
Technical debt accumulation and impact modeling.
Models how technical debt affects team velocity and requires senior developer time to resolve.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

from ..utils.math_helpers import safe_divide, validate_positive, validate_ratio
from ..utils.exceptions import ValidationError


class DebtType(Enum):
    """Types of technical debt."""
    ARCHITECTURAL = "architectural"
    CODE_QUALITY = "code_quality" 
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DEPENDENCY = "dependency"
    AI_GENERATED = "ai_generated"


@dataclass
class DebtAccumulation:
    """Models technical debt accumulation rates."""
    
    # Base accumulation rates by seniority (debt units per month per developer)
    junior_base_rate: float = 2.0  # Juniors create more debt
    mid_base_rate: float = 1.0     # Mid-level baseline
    senior_base_rate: float = 0.3  # Seniors create less debt
    
    # AI impact on debt accumulation
    ai_amplification_factor: float = 1.5  # AI can amplify poor decisions
    ai_code_quality_penalty: float = 0.8  # AI code may lack context
    
    # Code review effectiveness in preventing debt
    review_prevention_factor: float = 0.6  # Good reviews prevent 60% of debt
    senior_review_effectiveness: float = 0.8  # Senior reviews are more effective
    
    def calculate_monthly_debt_accumulation(self, 
                                          team_composition: Dict[str, int],
                                          ai_adoption: float,
                                          review_coverage: float,
                                          senior_review_ratio: float) -> Dict[DebtType, float]:
        """
        Calculate monthly technical debt accumulation.
        
        Args:
            team_composition: Dict with 'junior', 'mid', 'senior' counts
            ai_adoption: AI adoption rate (0-1)
            review_coverage: Fraction of code that gets reviewed (0-1)  
            senior_review_ratio: Fraction of reviews done by seniors (0-1)
            
        Returns:
            Dict mapping debt types to accumulation rates
        """
        validate_ratio(ai_adoption, "ai_adoption")
        validate_ratio(review_coverage, "review_coverage")
        validate_ratio(senior_review_ratio, "senior_review_ratio")
        
        # Base debt accumulation by seniority
        base_debt = (
            team_composition.get('junior', 0) * self.junior_base_rate +
            team_composition.get('mid', 0) * self.mid_base_rate +
            team_composition.get('senior', 0) * self.senior_base_rate
        )
        
        # AI amplification effects
        ai_multiplier = 1 + (self.ai_amplification_factor - 1) * ai_adoption
        ai_quality_debt = base_debt * ai_adoption * self.ai_code_quality_penalty
        
        # Review mitigation
        review_effectiveness = (
            self.review_prevention_factor * 
            (1 + (self.senior_review_effectiveness - 1) * senior_review_ratio)
        )
        review_prevented_debt = base_debt * review_coverage * review_effectiveness
        
        # Net debt accumulation
        net_base_debt = max(0.1, base_debt * ai_multiplier - review_prevented_debt)
        
        # Distribute debt across types
        return {
            DebtType.ARCHITECTURAL: net_base_debt * 0.25,  # 25% architectural
            DebtType.CODE_QUALITY: net_base_debt * 0.30,   # 30% code quality
            DebtType.TESTING: net_base_debt * 0.20,        # 20% testing gaps
            DebtType.DOCUMENTATION: net_base_debt * 0.10,  # 10% docs
            DebtType.PERFORMANCE: net_base_debt * 0.08,    # 8% performance
            DebtType.SECURITY: net_base_debt * 0.05,       # 5% security
            DebtType.DEPENDENCY: net_base_debt * 0.02,     # 2% dependencies
            DebtType.AI_GENERATED: ai_quality_debt         # AI-specific debt
        }


@dataclass
class DebtImpact:
    """Models the impact of accumulated technical debt."""
    
    # Velocity impact factors
    velocity_drag_coefficient: float = 0.15  # 15% velocity loss per debt unit
    max_velocity_impact: float = 0.6         # Maximum 60% velocity loss
    
    # Quality impact
    quality_degradation_rate: float = 0.10   # Quality drops with debt
    
    # Maintenance burden
    maintenance_overhead_factor: float = 0.08 # Extra maintenance time per debt unit
    
    def calculate_velocity_impact(self, accumulated_debt: float) -> float:
        """
        Calculate velocity impact from accumulated technical debt.
        
        Args:
            accumulated_debt: Total debt units accumulated
            
        Returns:
            Velocity multiplier (0.4 to 1.0, where 1.0 = no impact)
        """
        validate_positive(accumulated_debt, "accumulated_debt")
        
        velocity_reduction = min(
            self.max_velocity_impact,
            accumulated_debt * self.velocity_drag_coefficient
        )
        
        return 1.0 - velocity_reduction
    
    def calculate_quality_impact(self, accumulated_debt: float) -> float:
        """Calculate quality degradation from technical debt."""
        quality_reduction = min(0.4, accumulated_debt * self.quality_degradation_rate)
        return 1.0 - quality_reduction
    
    def calculate_maintenance_overhead(self, accumulated_debt: float) -> float:
        """Calculate additional maintenance time required."""
        return accumulated_debt * self.maintenance_overhead_factor


@dataclass  
class DebtResolution:
    """Models technical debt resolution requirements."""
    
    # Senior developer time required to resolve debt (hours per debt unit)
    senior_resolution_time: float = 4.0      # 4 hours per unit for seniors
    mid_resolution_time: float = 8.0         # 8 hours for mid-level 
    junior_resolution_time: float = 16.0     # 16 hours for juniors (if capable)
    
    # Some debt types require senior developers
    senior_required_debt_types = {
        DebtType.ARCHITECTURAL,
        DebtType.PERFORMANCE, 
        DebtType.SECURITY
    }
    
    # Resolution effectiveness by seniority
    senior_resolution_effectiveness: float = 0.9  # Seniors resolve 90% permanently
    mid_resolution_effectiveness: float = 0.7     # Mid-level 70%
    junior_resolution_effectiveness: float = 0.4  # Juniors 40% (may create new debt)
    
    def calculate_resolution_requirements(self, 
                                        debt_by_type: Dict[DebtType, float]) -> Dict[str, float]:
        """
        Calculate senior developer time required to resolve accumulated debt.
        
        Args:
            debt_by_type: Current debt levels by type
            
        Returns:
            Dict with senior, mid, junior resolution hours required
        """
        senior_hours = 0.0
        mid_hours = 0.0  
        junior_hours = 0.0
        
        for debt_type, debt_amount in debt_by_type.items():
            if debt_type in self.senior_required_debt_types:
                # Must be resolved by seniors
                senior_hours += debt_amount * self.senior_resolution_time
            else:
                # Can be distributed, but seniors are most effective
                # Optimal strategy: 70% senior, 20% mid, 10% junior
                senior_hours += debt_amount * 0.7 * self.senior_resolution_time
                mid_hours += debt_amount * 0.2 * self.mid_resolution_time
                junior_hours += debt_amount * 0.1 * self.junior_resolution_time
                
        return {
            'senior_hours': senior_hours,
            'mid_hours': mid_hours, 
            'junior_hours': junior_hours
        }
    
    def calculate_monthly_resolution_capacity(self, 
                                            team_composition: Dict[str, int],
                                            debt_resolution_time_allocation: float = 0.2) -> float:
        """
        Calculate how much debt can be resolved per month.
        
        Args:
            team_composition: Dict with 'junior', 'mid', 'senior' counts
            debt_resolution_time_allocation: Fraction of time allocated to debt (0-1)
            
        Returns:
            Debt units that can be resolved per month
        """
        validate_ratio(debt_resolution_time_allocation, "debt_resolution_time_allocation")
        
        # Available hours per month (assuming 160 work hours)
        monthly_hours = 160
        
        # Calculate resolution capacity
        senior_capacity = (
            team_composition.get('senior', 0) * 
            monthly_hours * 
            debt_resolution_time_allocation / 
            self.senior_resolution_time
        )
        
        mid_capacity = (
            team_composition.get('mid', 0) * 
            monthly_hours * 
            debt_resolution_time_allocation / 
            self.mid_resolution_time
        )
        
        # Junior capacity is limited and less effective
        junior_capacity = (
            team_composition.get('junior', 0) * 
            monthly_hours * 
            debt_resolution_time_allocation * 0.5 /  # Only 50% of juniors on debt work
            self.junior_resolution_time
        )
        
        return senior_capacity + mid_capacity * 0.7 + junior_capacity * 0.4


@dataclass
class TechnicalDebtModel:
    """Complete technical debt model combining accumulation, impact, and resolution."""
    
    accumulation: DebtAccumulation
    impact: DebtImpact  
    resolution: DebtResolution
    current_debt: float = 0.0
    debt_by_type: Dict[DebtType, float] = None
    
    def __post_init__(self):
        """Initialize debt tracking."""
        if self.debt_by_type is None:
            self.debt_by_type = {debt_type: 0.0 for debt_type in DebtType}
    
    def simulate_month(self,
                      team_composition: Dict[str, int],
                      ai_adoption: float,
                      review_coverage: float,
                      senior_review_ratio: float,
                      debt_resolution_allocation: float = 0.2) -> Dict[str, float]:
        """
        Simulate one month of debt accumulation and resolution.
        
        Args:
            team_composition: Team composition by seniority
            ai_adoption: AI adoption rate
            review_coverage: Code review coverage  
            senior_review_ratio: Fraction of reviews by seniors
            debt_resolution_allocation: Time allocated to debt resolution
            
        Returns:
            Dict with debt metrics for the month
        """
        # Calculate debt accumulation for this month
        monthly_accumulation = self.accumulation.calculate_monthly_debt_accumulation(
            team_composition, ai_adoption, review_coverage, senior_review_ratio
        )
        
        # Calculate resolution capacity  
        resolution_capacity = self.resolution.calculate_monthly_resolution_capacity(
            team_composition, debt_resolution_allocation
        )
        
        # Update debt levels
        total_new_debt = sum(monthly_accumulation.values())
        for debt_type, new_debt in monthly_accumulation.items():
            self.debt_by_type[debt_type] += new_debt
            
        self.current_debt += total_new_debt
        
        # Apply resolution
        debt_resolved = min(resolution_capacity, self.current_debt)
        resolution_ratio = safe_divide(debt_resolved, self.current_debt)
        
        # Reduce debt proportionally across types
        for debt_type in self.debt_by_type:
            resolved_amount = self.debt_by_type[debt_type] * resolution_ratio
            self.debt_by_type[debt_type] = max(0, self.debt_by_type[debt_type] - resolved_amount)
            
        self.current_debt = max(0, self.current_debt - debt_resolved)
        
        # Calculate impacts
        velocity_impact = self.impact.calculate_velocity_impact(self.current_debt)
        quality_impact = self.impact.calculate_quality_impact(self.current_debt) 
        maintenance_overhead = self.impact.calculate_maintenance_overhead(self.current_debt)
        
        # Calculate senior time requirements
        resolution_requirements = self.resolution.calculate_resolution_requirements(self.debt_by_type)
        
        return {
            'debt_accumulated': total_new_debt,
            'debt_resolved': debt_resolved,
            'total_debt': self.current_debt,
            'velocity_multiplier': velocity_impact,
            'quality_multiplier': quality_impact,
            'maintenance_overhead_hours': maintenance_overhead * 160,  # Convert to hours
            'senior_hours_required': resolution_requirements['senior_hours'],
            'resolution_capacity': resolution_capacity,
            'debt_by_type': dict(self.debt_by_type)
        }


def create_debt_model(team_type: str = "balanced") -> TechnicalDebtModel:
    """Create a technical debt model based on team maturity."""
    
    if team_type == "startup" or team_type == "startup_no_qa":
        # High debt accumulation, limited resolution capacity
        accumulation = DebtAccumulation(
            junior_base_rate=2.5,
            ai_amplification_factor=1.8,
            review_prevention_factor=0.4  # Less effective reviews
        )
        impact = DebtImpact(
            velocity_drag_coefficient=0.18,
            max_velocity_impact=0.7
        )
        resolution = DebtResolution(
            senior_resolution_time=5.0  # Less experienced seniors
        )
    
    elif team_type == "enterprise":
        # Lower debt accumulation, better resolution
        accumulation = DebtAccumulation(
            junior_base_rate=1.5,
            ai_amplification_factor=1.2,
            review_prevention_factor=0.8  # More effective processes
        )
        impact = DebtImpact(
            velocity_drag_coefficient=0.12,
            max_velocity_impact=0.5
        )
        resolution = DebtResolution(
            senior_resolution_time=3.0  # More experienced seniors
        )
    
    else:  # balanced
        accumulation = DebtAccumulation()
        impact = DebtImpact()
        resolution = DebtResolution()
    
    return TechnicalDebtModel(
        accumulation=accumulation,
        impact=impact,
        resolution=resolution
    )