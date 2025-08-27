"""
Business constraint definitions for AI impact model.
Defines realistic bounds and relationships between parameters including capacity constraints.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

from .constraint_solver import ConstraintSolver


class ConstraintType(Enum):
    """Types of business constraints."""
    BUDGET = "budget"
    TEAM = "team"
    ADOPTION = "adoption"
    IMPACT = "impact"
    TIME = "time"
    ROI = "roi"
    CAPACITY = "capacity"
    PIPELINE = "pipeline"
    CUSTOM = "custom"


@dataclass
class ConstraintDefinition:
    """Definition of a business constraint."""
    
    name: str
    type: ConstraintType
    description: str
    parameters: Dict[str, Any]
    is_hard: bool = True  # Hard constraints must be satisfied


class BusinessConstraints:
    """
    Manages business constraints for AI impact model optimization.
    """
    
    def __init__(self, solver: ConstraintSolver):
        """
        Initialize business constraints manager.
        
        Args:
            solver: Constraint solver instance
        """
        self.solver = solver
        self.constraints = []
        self.variables = {}
    
    def add_budget_constraint(self, max_monthly_budget: float, 
                             team_size_var: Any, cost_per_seat_var: Any,
                             token_cost_var: Optional[Any] = None) -> None:
        """
        Add budget constraint: total_cost <= max_budget.
        
        Args:
            max_monthly_budget: Maximum monthly budget
            team_size_var: Team size variable
            cost_per_seat_var: Cost per seat variable
            token_cost_var: Optional token cost variable
        """
        # For CP-SAT solver, directly use variables
        # team_size * cost_per_seat <= budget (scaled by 1000)
        constraint = team_size_var * cost_per_seat_var <= max_monthly_budget * 1000
        self.solver.add_constraint(
            constraint,
            name=f"budget_constraint_{max_monthly_budget}"
        )
        
        self.constraints.append(
            ConstraintDefinition(
                name=f"budget_limit_{max_monthly_budget}",
                type=ConstraintType.BUDGET,
                description=f"Total monthly cost must not exceed ${max_monthly_budget}",
                parameters={"max_monthly_budget": max_monthly_budget}
            )
        )
    
    def add_team_size_constraint(self, team_size_var: Any, 
                                min_size: int = 1, max_size: int = 1000) -> None:
        """
        Add team size bounds constraint.
        
        Args:
            team_size_var: Team size variable
            min_size: Minimum team size
            max_size: Maximum team size
        """
        # These are typically handled by variable bounds, but we can add explicit constraints
        self.solver.add_constraint(
            team_size_var >= min_size,
            name=f"min_team_size_{min_size}"
        )
        self.solver.add_constraint(
            team_size_var <= max_size,
            name=f"max_team_size_{max_size}"
        )
        
        self.constraints.append(
            ConstraintDefinition(
                name=f"team_size_bounds_{min_size}_{max_size}",
                type=ConstraintType.TEAM,
                description=f"Team size must be between {min_size} and {max_size}",
                parameters={"min_size": min_size, "max_size": max_size}
            )
        )
    
    def add_team_composition_constraint(self, junior_ratio_var: Any,
                                       mid_ratio_var: Any,
                                       senior_ratio_var: Any) -> None:
        """
        Add constraint that team ratios sum to 1.0.
        
        Args:
            junior_ratio_var: Junior developer ratio variable
            mid_ratio_var: Mid-level developer ratio variable
            senior_ratio_var: Senior developer ratio variable
        """
        # Ratios must sum to 1.0
        constraint = junior_ratio_var + mid_ratio_var + senior_ratio_var == 1000  # Scaled by 1000
        self.solver.add_constraint(
            constraint,
            name="team_composition_unity"
        )
        
        # Realistic bounds on each ratio
        self.solver.add_constraint(junior_ratio_var >= 50, name="min_junior_ratio")  # >= 0.05
        self.solver.add_constraint(junior_ratio_var <= 700, name="max_junior_ratio")  # <= 0.70
        self.solver.add_constraint(mid_ratio_var >= 100, name="min_mid_ratio")  # >= 0.10
        self.solver.add_constraint(mid_ratio_var <= 700, name="max_mid_ratio")  # <= 0.70
        self.solver.add_constraint(senior_ratio_var >= 50, name="min_senior_ratio")  # >= 0.05
        self.solver.add_constraint(senior_ratio_var <= 500, name="max_senior_ratio")  # <= 0.50
        
        self.constraints.append(
            ConstraintDefinition(
                name="team_composition",
                type=ConstraintType.TEAM,
                description="Team composition ratios must sum to 1.0 with realistic bounds",
                parameters={"constraint": "junior + mid + senior = 1.0"}
            )
        )
    
    def add_adoption_constraints(self, initial_adopters_var: Any,
                                plateau_efficiency_var: Any,
                                dropout_rate_var: Any) -> None:
        """
        Add realistic adoption constraints.
        
        Args:
            initial_adopters_var: Initial adoption rate variable
            plateau_efficiency_var: Maximum adoption plateau variable
            dropout_rate_var: Monthly dropout rate variable
        """
        # Initial adoption must be positive but small
        self.solver.add_constraint(
            initial_adopters_var >= 10,  # >= 0.01 (1%)
            name="min_initial_adoption"
        )
        self.solver.add_constraint(
            initial_adopters_var <= 300,  # <= 0.30 (30%)
            name="max_initial_adoption"
        )
        
        # Plateau must be higher than initial
        self.solver.add_constraint(
            plateau_efficiency_var >= initial_adopters_var * 2,
            name="plateau_higher_than_initial"
        )
        
        # Plateau can't exceed realistic maximum
        self.solver.add_constraint(
            plateau_efficiency_var <= 950,  # <= 0.95 (95%)
            name="max_plateau_efficiency"
        )
        
        # Dropout rate bounds
        self.solver.add_constraint(
            dropout_rate_var >= 0,  # >= 0%
            name="min_dropout_rate"
        )
        self.solver.add_constraint(
            dropout_rate_var <= 100,  # <= 0.10 (10% per month)
            name="max_dropout_rate"
        )
        
        self.constraints.append(
            ConstraintDefinition(
                name="adoption_realism",
                type=ConstraintType.ADOPTION,
                description="Adoption parameters must follow realistic patterns",
                parameters={
                    "initial_range": "1%-30%",
                    "plateau_range": "2x initial to 95%",
                    "dropout_range": "0%-10%"
                }
            )
        )
    
    def add_impact_constraints(self, impact_vars: Dict[str, Any]) -> None:
        """
        Add realistic impact improvement constraints.
        
        Args:
            impact_vars: Dictionary of impact variable names to variable objects
        """
        # Define realistic maximum improvements
        impact_limits = {
            'feature_cycle_reduction': 500,  # Max 50% reduction
            'bug_fix_reduction': 600,  # Max 60% reduction
            'defect_reduction': 400,  # Max 40% reduction
            'incident_reduction': 500,  # Max 50% reduction
            'onboarding_reduction': 700,  # Max 70% reduction
            'pr_review_reduction': 800,  # Max 80% reduction
            'rework_reduction': 600,  # Max 60% reduction
        }
        
        for var_name, var in impact_vars.items():
            if var_name in impact_limits:
                max_val = impact_limits[var_name]
                self.solver.add_constraint(
                    var <= max_val,
                    name=f"max_{var_name}"
                )
                # All impacts must be non-negative
                self.solver.add_constraint(
                    var >= 0,
                    name=f"min_{var_name}"
                )
        
        # Some impacts are correlated
        if 'defect_reduction' in impact_vars and 'incident_reduction' in impact_vars:
            # Incident reduction should not exceed defect reduction significantly
            self.solver.add_constraint(
                impact_vars['incident_reduction'] <= impact_vars['defect_reduction'] * 1500 / 1000,
                name="incident_defect_correlation"
            )
        
        if 'feature_cycle_reduction' in impact_vars and 'bug_fix_reduction' in impact_vars:
            # Bug fix should improve at least as much as features
            self.solver.add_constraint(
                impact_vars['bug_fix_reduction'] >= impact_vars['feature_cycle_reduction'] * 800 / 1000,
                name="bugfix_feature_correlation"
            )
        
        self.constraints.append(
            ConstraintDefinition(
                name="impact_realism",
                type=ConstraintType.IMPACT,
                description="Impact improvements must be realistic and correlated",
                parameters={"limits": impact_limits}
            )
        )
    
    def add_roi_constraint(self, min_roi: float, roi_var: Any) -> None:
        """
        Add minimum ROI constraint.
        
        Args:
            min_roi: Minimum required ROI (as ratio, e.g., 1.5 for 150%)
            roi_var: ROI variable
        """
        self.solver.add_constraint(
            roi_var >= int(min_roi * 1000),
            name=f"min_roi_{min_roi}"
        )
        
        self.constraints.append(
            ConstraintDefinition(
                name=f"minimum_roi_{min_roi}",
                type=ConstraintType.ROI,
                description=f"ROI must be at least {min_roi * 100}%",
                parameters={"min_roi": min_roi}
            )
        )
    
    def add_timeframe_constraint(self, timeframe_var: Any,
                                min_months: int = 6, max_months: int = 60) -> None:
        """
        Add analysis timeframe constraints.
        
        Args:
            timeframe_var: Timeframe variable (in months)
            min_months: Minimum analysis period
            max_months: Maximum analysis period
        """
        self.solver.add_constraint(
            timeframe_var >= min_months,
            name=f"min_timeframe_{min_months}"
        )
        self.solver.add_constraint(
            timeframe_var <= max_months,
            name=f"max_timeframe_{max_months}"
        )
        
        self.constraints.append(
            ConstraintDefinition(
                name=f"timeframe_bounds_{min_months}_{max_months}",
                type=ConstraintType.TIME,
                description=f"Analysis timeframe must be between {min_months} and {max_months} months",
                parameters={"min_months": min_months, "max_months": max_months}
            )
        )
    
    def add_capacity_constraints(self, team_size_var: Any,
                                throughput_var: Any,
                                wip_limit_multiplier: float = 2.0) -> None:
        """
        Add capacity and WIP (Work In Progress) constraints.
        
        Args:
            team_size_var: Team size variable
            throughput_var: Throughput variable
            wip_limit_multiplier: WIP limit as multiplier of team size
        """
        # WIP limit constraint - can't have too much work in progress
        max_wip = team_size_var * int(wip_limit_multiplier * 1000)
        self.solver.add_constraint(
            throughput_var * 30 <= max_wip,  # Monthly throughput limited by WIP
            name=f"wip_limit_{wip_limit_multiplier}"
        )
        
        # Throughput can't exceed team capacity
        max_throughput_per_dev = 100  # Max 10 items per dev per month (scaled by 1000)
        self.solver.add_constraint(
            throughput_var <= team_size_var * max_throughput_per_dev,
            name="max_throughput_capacity"
        )
        
        self.constraints.append(
            ConstraintDefinition(
                name=f"capacity_wip_{wip_limit_multiplier}",
                type=ConstraintType.CAPACITY,
                description=f"Capacity and WIP constraints with multiplier {wip_limit_multiplier}",
                parameters={
                    "wip_limit_multiplier": wip_limit_multiplier,
                    "max_throughput_per_dev": max_throughput_per_dev / 1000
                }
            )
        )
    
    def add_pipeline_constraints(self, pipeline_vars: Dict[str, Any]) -> None:
        """
        Add delivery pipeline constraints (bottlenecks, review capacity, etc).
        
        Args:
            pipeline_vars: Dictionary of pipeline stage variables
        """
        # Code review capacity constraint
        if 'review_capacity' in pipeline_vars and 'coding_throughput' in pipeline_vars:
            # Review capacity must be >= coding throughput (review is often bottleneck)
            self.solver.add_constraint(
                pipeline_vars['review_capacity'] >= pipeline_vars['coding_throughput'] * 800 / 1000,
                name="review_bottleneck"
            )
        
        # Testing capacity constraint
        if 'test_capacity' in pipeline_vars and 'coding_throughput' in pipeline_vars:
            # Test capacity needs to keep up with coding
            self.solver.add_constraint(
                pipeline_vars['test_capacity'] >= pipeline_vars['coding_throughput'] * 700 / 1000,
                name="test_bottleneck"
            )
        
        # Deployment frequency constraint
        if 'deployment_frequency' in pipeline_vars:
            # Deployment frequency bounds (daily=30, weekly=4, monthly=1 per month)
            self.solver.add_constraint(
                pipeline_vars['deployment_frequency'] >= 1,  # At least monthly
                name="min_deployment_frequency"
            )
            self.solver.add_constraint(
                pipeline_vars['deployment_frequency'] <= 30,  # At most daily
                name="max_deployment_frequency"
            )
        
        # Lead time constraint
        if 'lead_time_days' in pipeline_vars:
            # Lead time should be reasonable
            self.solver.add_constraint(
                pipeline_vars['lead_time_days'] >= 1,  # At least 1 day
                name="min_lead_time"
            )
            self.solver.add_constraint(
                pipeline_vars['lead_time_days'] <= 90,  # At most 90 days
                name="max_lead_time"
            )
        
        self.constraints.append(
            ConstraintDefinition(
                name="pipeline_flow",
                type=ConstraintType.PIPELINE,
                description="Delivery pipeline flow and bottleneck constraints",
                parameters={"stages": list(pipeline_vars.keys())}
            )
        )
    
    def add_testing_constraints(self, automation_coverage_var: Any,
                               test_quality_var: Any,
                               defect_escape_var: Any) -> None:
        """
        Add testing strategy constraints.
        
        Args:
            automation_coverage_var: Test automation coverage variable (0-1000)
            test_quality_var: Test quality variable (0-1000)
            defect_escape_var: Defect escape rate variable (0-1000)
        """
        # Test automation coverage bounds
        self.solver.add_constraint(
            automation_coverage_var >= 100,  # At least 10% automation
            name="min_test_automation"
        )
        self.solver.add_constraint(
            automation_coverage_var <= 900,  # At most 90% automation
            name="max_test_automation"
        )
        
        # Test quality inversely relates to defect escape
        # Higher quality -> lower escape rate
        self.solver.add_constraint(
            test_quality_var + defect_escape_var <= 1200,  # Sum constraint
            name="quality_escape_tradeoff"
        )
        
        # Minimum test quality
        self.solver.add_constraint(
            test_quality_var >= 300,  # At least 30% quality
            name="min_test_quality"
        )
        
        self.constraints.append(
            ConstraintDefinition(
                name="testing_strategy",
                type=ConstraintType.PIPELINE,
                description="Testing strategy and quality constraints",
                parameters={
                    "min_automation": 0.1,
                    "max_automation": 0.9,
                    "min_quality": 0.3
                }
            )
        )
    
    def add_custom_constraint(self, name: str, description: str,
                            constraint_func: Any) -> None:
        """
        Add a custom constraint.
        
        Args:
            name: Constraint name
            description: Human-readable description
            constraint_func: Function that adds constraint to solver
        """
        constraint_func(self.solver)
        
        self.constraints.append(
            ConstraintDefinition(
                name=name,
                type=ConstraintType.CUSTOM,
                description=description,
                parameters={"custom": True}
            )
        )
    
    def get_all_constraints(self) -> List[ConstraintDefinition]:
        """Get list of all defined constraints."""
        return self.constraints
    
    def validate_scenario(self, scenario_params: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate if a scenario satisfies all constraints.
        
        Args:
            scenario_params: Dictionary of parameter values
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Check each constraint type
        for constraint in self.constraints:
            if constraint.type == ConstraintType.BUDGET:
                # Check budget constraint
                if 'team_size' in scenario_params and 'cost_per_seat_month' in scenario_params:
                    total_cost = scenario_params['team_size'] * scenario_params['cost_per_seat_month']
                    max_budget = constraint.parameters.get('max_monthly_budget', float('inf'))
                    if total_cost > max_budget:
                        violations.append(
                            f"Budget violation: ${total_cost:.2f} > ${max_budget:.2f}"
                        )
            
            elif constraint.type == ConstraintType.TEAM:
                # Check team size bounds
                if 'team_size' in scenario_params:
                    team_size = scenario_params['team_size']
                    min_size = constraint.parameters.get('min_size', 1)
                    max_size = constraint.parameters.get('max_size', float('inf'))
                    if team_size < min_size or team_size > max_size:
                        violations.append(
                            f"Team size violation: {team_size} not in [{min_size}, {max_size}]"
                        )
            
            elif constraint.type == ConstraintType.ADOPTION:
                # Check adoption parameters
                if 'initial_adopters' in scenario_params:
                    initial = scenario_params['initial_adopters']
                    if initial < 0.01 or initial > 0.30:
                        violations.append(
                            f"Initial adoption violation: {initial:.2%} not in [1%, 30%]"
                        )
            
            elif constraint.type == ConstraintType.IMPACT:
                # Check impact limits
                limits = constraint.parameters.get('limits', {})
                for param, max_val in limits.items():
                    if param in scenario_params:
                        value = scenario_params[param]
                        if value > max_val / 1000:  # Unscale
                            violations.append(
                                f"Impact violation: {param}={value:.2%} > {max_val/1000:.2%}"
                            )
        
        return len(violations) == 0, violations