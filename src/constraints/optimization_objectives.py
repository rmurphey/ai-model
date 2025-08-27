"""
Optimization objective definitions for AI impact model.
Defines various goals for optimization (maximize NPV, ROI, adoption, etc.).
"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
import numpy as np

from .constraint_solver import ConstraintSolver
from ..model.financial_calculations import calculate_npv_monthly, calculate_roi
from ..config.constants import DEFAULT_DISCOUNT_RATE_ANNUAL


class ObjectiveType(Enum):
    """Types of optimization objectives."""
    MAX_NPV = "maximize_npv"
    MAX_ROI = "maximize_roi"
    MIN_COST = "minimize_cost"
    MAX_ADOPTION = "maximize_adoption"
    MIN_BREAKEVEN = "minimize_breakeven_time"
    MAX_VALUE = "maximize_total_value"
    BALANCED = "balanced_scorecard"
    CUSTOM = "custom"


@dataclass
class ObjectiveDefinition:
    """Definition of an optimization objective."""
    
    name: str
    type: ObjectiveType
    description: str
    weight: float = 1.0
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class OptimizationObjective:
    """
    Manages optimization objectives for AI impact model.
    """
    
    def __init__(self, solver: ConstraintSolver):
        """
        Initialize optimization objective manager.
        
        Args:
            solver: Constraint solver instance
        """
        self.solver = solver
        self.objectives = []
        self.current_objective = None
    
    def set_npv_maximization(self, value_vars: Dict[str, Any], cost_vars: Dict[str, Any],
                            timeframe_months: int, discount_rate: float = DEFAULT_DISCOUNT_RATE_ANNUAL) -> None:
        """
        Set objective to maximize NPV.
        
        Args:
            value_vars: Dictionary of value-generating variables
            cost_vars: Dictionary of cost variables
            timeframe_months: Analysis timeframe
            discount_rate: Annual discount rate
        """
        # Build NPV expression
        # Simplified NPV = sum(discounted_value) - sum(discounted_costs)
        
        monthly_discount = (1 + discount_rate) ** (1/12) - 1
        
        # Create NPV expression
        npv_expr = None
        
        # Add value components
        for var_name, var in value_vars.items():
            if npv_expr is None:
                npv_expr = var
            else:
                npv_expr += var
        
        # Subtract cost components
        for var_name, var in cost_vars.items():
            npv_expr -= var
        
        # Apply time discount (simplified)
        discount_factor = sum(1 / (1 + monthly_discount) ** m for m in range(timeframe_months))
        npv_expr = npv_expr * int(discount_factor * 100)  # Scale for integer solver
        
        self.solver.set_objective(npv_expr, maximize=True)
        
        self.current_objective = ObjectiveDefinition(
            name="maximize_npv",
            type=ObjectiveType.MAX_NPV,
            description=f"Maximize Net Present Value over {timeframe_months} months",
            parameters={
                "timeframe_months": timeframe_months,
                "discount_rate": discount_rate
            }
        )
        self.objectives.append(self.current_objective)
    
    def set_roi_maximization(self, value_vars: Dict[str, Any], cost_vars: Dict[str, Any]) -> None:
        """
        Set objective to maximize ROI.
        
        Args:
            value_vars: Dictionary of value-generating variables
            cost_vars: Dictionary of cost variables
        """
        # ROI = (total_value - total_cost) / total_cost
        # To maximize ROI, we maximize: total_value / total_cost
        # For linear solver, we can maximize: total_value - k * total_cost
        # where k is a weight factor
        
        roi_expr = None
        
        # Add value components
        for var_name, var in value_vars.items():
            if roi_expr is None:
                roi_expr = var * 100  # Scale up
            else:
                roi_expr += var * 100
        
        # Subtract weighted costs (higher weight = prefer lower cost)
        for var_name, var in cost_vars.items():
            roi_expr -= var * 50  # Weight factor
        
        self.solver.set_objective(roi_expr, maximize=True)
        
        self.current_objective = ObjectiveDefinition(
            name="maximize_roi",
            type=ObjectiveType.MAX_ROI,
            description="Maximize Return on Investment",
            parameters={}
        )
        self.objectives.append(self.current_objective)
    
    def set_cost_minimization(self, cost_vars: Dict[str, Any]) -> None:
        """
        Set objective to minimize total costs.
        
        Args:
            cost_vars: Dictionary of cost variables
        """
        cost_expr = None
        
        for var_name, var in cost_vars.items():
            if cost_expr is None:
                cost_expr = var
            else:
                cost_expr += var
        
        self.solver.set_objective(cost_expr, maximize=False)
        
        self.current_objective = ObjectiveDefinition(
            name="minimize_cost",
            type=ObjectiveType.MIN_COST,
            description="Minimize total costs",
            parameters={}
        )
        self.objectives.append(self.current_objective)
    
    def set_adoption_maximization(self, adoption_vars: Dict[str, Any]) -> None:
        """
        Set objective to maximize adoption metrics.
        
        Args:
            adoption_vars: Dictionary of adoption-related variables
        """
        adoption_expr = None
        
        # Focus on plateau efficiency and minimize dropout
        if 'plateau_efficiency' in adoption_vars:
            adoption_expr = adoption_vars['plateau_efficiency'] * 100
        
        if 'dropout_rate' in adoption_vars:
            if adoption_expr is None:
                adoption_expr = -adoption_vars['dropout_rate'] * 50
            else:
                adoption_expr -= adoption_vars['dropout_rate'] * 50
        
        if 'initial_adopters' in adoption_vars:
            if adoption_expr is None:
                adoption_expr = adoption_vars['initial_adopters'] * 20
            else:
                adoption_expr += adoption_vars['initial_adopters'] * 20
        
        self.solver.set_objective(adoption_expr, maximize=True)
        
        self.current_objective = ObjectiveDefinition(
            name="maximize_adoption",
            type=ObjectiveType.MAX_ADOPTION,
            description="Maximize adoption success metrics",
            parameters={}
        )
        self.objectives.append(self.current_objective)
    
    def set_balanced_scorecard(self, npv_weight: float = 0.4, roi_weight: float = 0.3,
                              adoption_weight: float = 0.2, cost_weight: float = 0.1,
                              value_vars: Dict[str, Any] = None,
                              cost_vars: Dict[str, Any] = None,
                              adoption_vars: Dict[str, Any] = None) -> None:
        """
        Set a balanced multi-objective optimization.
        
        Args:
            npv_weight: Weight for NPV component
            roi_weight: Weight for ROI component
            adoption_weight: Weight for adoption component
            cost_weight: Weight for cost minimization
            value_vars: Value-generating variables
            cost_vars: Cost variables
            adoption_vars: Adoption variables
        """
        # Normalize weights
        total_weight = npv_weight + roi_weight + adoption_weight + cost_weight
        npv_weight /= total_weight
        roi_weight /= total_weight
        adoption_weight /= total_weight
        cost_weight /= total_weight
        
        balanced_expr = None
        
        # NPV component
        if value_vars and cost_vars and npv_weight > 0:
            for var in value_vars.values():
                if balanced_expr is None:
                    balanced_expr = var * int(npv_weight * 1000)
                else:
                    balanced_expr += var * int(npv_weight * 1000)
            
            for var in cost_vars.values():
                balanced_expr -= var * int(npv_weight * 500)
        
        # ROI component (value/cost ratio proxy)
        if value_vars and roi_weight > 0:
            for var in value_vars.values():
                if balanced_expr is None:
                    balanced_expr = var * int(roi_weight * 2000)
                else:
                    balanced_expr += var * int(roi_weight * 2000)
        
        # Adoption component
        if adoption_vars and adoption_weight > 0:
            if 'plateau_efficiency' in adoption_vars:
                if balanced_expr is None:
                    balanced_expr = adoption_vars['plateau_efficiency'] * int(adoption_weight * 1000)
                else:
                    balanced_expr += adoption_vars['plateau_efficiency'] * int(adoption_weight * 1000)
        
        # Cost minimization component (negative contribution)
        if cost_vars and cost_weight > 0:
            for var in cost_vars.values():
                if balanced_expr is None:
                    balanced_expr = -var * int(cost_weight * 1000)
                else:
                    balanced_expr -= var * int(cost_weight * 1000)
        
        self.solver.set_objective(balanced_expr, maximize=True)
        
        self.current_objective = ObjectiveDefinition(
            name="balanced_scorecard",
            type=ObjectiveType.BALANCED,
            description="Balanced optimization across multiple objectives",
            parameters={
                "npv_weight": npv_weight,
                "roi_weight": roi_weight,
                "adoption_weight": adoption_weight,
                "cost_weight": cost_weight
            }
        )
        self.objectives.append(self.current_objective)
    
    def set_custom_objective(self, name: str, description: str,
                           objective_func: Callable[[ConstraintSolver], Any],
                           maximize: bool = True) -> None:
        """
        Set a custom optimization objective.
        
        Args:
            name: Objective name
            description: Human-readable description
            objective_func: Function that returns objective expression
            maximize: Whether to maximize or minimize
        """
        objective_expr = objective_func(self.solver)
        self.solver.set_objective(objective_expr, maximize=maximize)
        
        self.current_objective = ObjectiveDefinition(
            name=name,
            type=ObjectiveType.CUSTOM,
            description=description,
            parameters={"maximize": maximize}
        )
        self.objectives.append(self.current_objective)
    
    def get_current_objective(self) -> Optional[ObjectiveDefinition]:
        """Get the currently active objective."""
        return self.current_objective
    
    def get_all_objectives(self) -> List[ObjectiveDefinition]:
        """Get list of all defined objectives."""
        return self.objectives
    
    def calculate_objective_value(self, solution: Dict[str, float]) -> float:
        """
        Calculate the objective value for a given solution.
        
        Args:
            solution: Dictionary of variable values
            
        Returns:
            Objective function value
        """
        if not self.current_objective:
            return 0.0
        
        # This would need to be implemented based on the specific objective
        # For now, return a placeholder
        return 0.0