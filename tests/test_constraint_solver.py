"""
Tests for constraint solver framework.
"""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from src.constraints import (
    ConstraintSolver,
    SolverStatus,
    OptimizationResult,
    BusinessConstraints,
    ConstraintType,
    OptimizationObjective,
    ObjectiveType,
    ConstraintValidator,
    ValidationStatus
)
from src.utils.exceptions import ValidationError


class TestConstraintSolver:
    """Test constraint solver functionality."""
    
    def test_solver_initialization(self):
        """Test solver initialization."""
        solver = ConstraintSolver(use_integer_solver=False)
        assert solver.variables == {}
        assert solver.constraints == []
        assert solver.objective is None
    
    def test_add_variable(self):
        """Test adding variables to solver."""
        solver = ConstraintSolver()
        
        # Add integer variable
        var1 = solver.add_variable('team_size', 1, 100, is_integer=True)
        assert 'team_size' in solver.variables
        assert solver.bounds['team_size'] == (1, 100)
        
        # Add continuous variable
        var2 = solver.add_variable('adoption_rate', 0.0, 1.0, is_integer=False)
        assert 'adoption_rate' in solver.variables
        
        # Test duplicate variable
        with pytest.raises(ValidationError) as exc_info:
            solver.add_variable('team_size', 1, 50)
        assert "already exists" in str(exc_info.value)
    
    def test_add_constraint(self):
        """Test adding constraints."""
        solver = ConstraintSolver()
        
        var1 = solver.add_variable('x', 0, 10)
        var2 = solver.add_variable('y', 0, 10)
        
        # Add simple constraint
        solver.add_constraint(var1 + var2 <= 15, name="sum_constraint")
        assert "sum_constraint" in solver.constraints
    
    def test_linear_constraint(self):
        """Test adding linear constraints."""
        solver = ConstraintSolver()
        
        solver.add_variable('x', 0, 10)
        solver.add_variable('y', 0, 10)
        
        # Add linear constraint: 2x + 3y <= 20
        solver.add_linear_constraint(
            {'x': 2, 'y': 3},
            '<=',
            20,
            name="linear_test"
        )
        assert "linear_test" in solver.constraints
        
        # Test invalid variable
        with pytest.raises(ValidationError) as exc_info:
            solver.add_linear_constraint({'z': 1}, '<=', 10)
        assert "not found" in str(exc_info.value)
        
        # Test invalid operator
        with pytest.raises(ValidationError) as exc_info:
            solver.add_linear_constraint({'x': 1}, '<>', 10)
        assert "valid operator" in str(exc_info.value)
    
    def test_solve_simple_optimization(self):
        """Test solving a simple optimization problem."""
        solver = ConstraintSolver()
        
        # Create simple problem: maximize x + y subject to x + y <= 10
        x = solver.add_variable('x', 0, 10)
        y = solver.add_variable('y', 0, 10)
        
        solver.add_constraint(x + y <= 10000)  # Scaled by 1000
        solver.set_objective(x + y, maximize=True)
        
        result = solver.solve(time_limit_seconds=10)
        
        assert result.status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE]
        assert result.is_successful
        assert 'x' in result.optimal_values
        assert 'y' in result.optimal_values
        
        # Sum should be close to 10 (accounting for scaling)
        total = result.optimal_values['x'] + result.optimal_values['y']
        assert 9.5 <= total / 1000 <= 10.5
    
    def test_infeasible_problem(self):
        """Test handling of infeasible problems."""
        solver = ConstraintSolver()
        
        x = solver.add_variable('x', 0, 10)
        
        # Add conflicting constraints
        solver.add_constraint(x >= 5000)  # x >= 5
        solver.add_constraint(x <= 3000)  # x <= 3
        
        solver.set_objective(x, maximize=True)
        result = solver.solve(time_limit_seconds=5)
        
        assert result.status == SolverStatus.INFEASIBLE
        assert not result.is_successful
        assert "No feasible solution" in result.message


class TestBusinessConstraints:
    """Test business constraint definitions."""
    
    def test_budget_constraint(self):
        """Test budget constraint."""
        solver = ConstraintSolver()
        business = BusinessConstraints(solver)
        
        team_size = solver.add_variable('team_size', 1, 100)
        cost_per_seat = solver.add_variable('cost_per_seat', 10, 500)
        
        business.add_budget_constraint(10000, team_size, cost_per_seat)
        
        assert len(business.constraints) == 1
        assert business.constraints[0].type == ConstraintType.BUDGET
    
    def test_team_composition_constraint(self):
        """Test team composition constraint."""
        solver = ConstraintSolver()
        business = BusinessConstraints(solver)
        
        junior = solver.add_variable('junior_ratio', 50, 700)
        mid = solver.add_variable('mid_ratio', 100, 700)
        senior = solver.add_variable('senior_ratio', 50, 500)
        
        business.add_team_composition_constraint(junior, mid, senior)
        
        # Should add multiple constraints (sum to 1, bounds)
        assert "team_composition_unity" in solver.constraints
    
    def test_adoption_constraints(self):
        """Test adoption constraints."""
        solver = ConstraintSolver()
        business = BusinessConstraints(solver)
        
        initial = solver.add_variable('initial', 10, 300)
        plateau = solver.add_variable('plateau', 100, 950)
        dropout = solver.add_variable('dropout', 0, 100)
        
        business.add_adoption_constraints(initial, plateau, dropout)
        
        assert len(business.constraints) == 1
        assert business.constraints[0].type == ConstraintType.ADOPTION
    
    def test_validate_scenario(self):
        """Test scenario validation against constraints."""
        solver = ConstraintSolver()
        business = BusinessConstraints(solver)
        
        # Add budget constraint
        team_size = solver.add_variable('team_size', 1, 100)
        cost_per_seat = solver.add_variable('cost_per_seat', 10, 500)
        business.add_budget_constraint(5000, team_size, cost_per_seat)
        
        # Test valid scenario
        valid_scenario = {
            'team_size': 50,
            'cost_per_seat_month': 50  # Total: 2500 < 5000
        }
        is_valid, violations = business.validate_scenario(valid_scenario)
        assert is_valid
        assert len(violations) == 0
        
        # Test invalid scenario
        invalid_scenario = {
            'team_size': 100,
            'cost_per_seat_month': 100  # Total: 10000 > 5000
        }
        is_valid, violations = business.validate_scenario(invalid_scenario)
        assert not is_valid
        assert len(violations) > 0
        assert "Budget violation" in violations[0]


class TestOptimizationObjective:
    """Test optimization objective definitions."""
    
    def test_npv_maximization(self):
        """Test NPV maximization objective."""
        solver = ConstraintSolver()
        objective = OptimizationObjective(solver)
        
        value_vars = {
            'feature_value': solver.add_variable('feature', 0, 1000),
            'bug_value': solver.add_variable('bug', 0, 1000)
        }
        cost_vars = {
            'license_cost': solver.add_variable('cost', 0, 500)
        }
        
        objective.set_npv_maximization(value_vars, cost_vars, 24)
        
        assert objective.current_objective is not None
        assert objective.current_objective.type == ObjectiveType.MAX_NPV
        assert solver.objective is not None
    
    def test_roi_maximization(self):
        """Test ROI maximization objective."""
        solver = ConstraintSolver()
        objective = OptimizationObjective(solver)
        
        value_vars = {'value': solver.add_variable('value', 0, 1000)}
        cost_vars = {'cost': solver.add_variable('cost', 1, 500)}
        
        objective.set_roi_maximization(value_vars, cost_vars)
        
        assert objective.current_objective.type == ObjectiveType.MAX_ROI
    
    def test_balanced_scorecard(self):
        """Test balanced multi-objective optimization."""
        solver = ConstraintSolver()
        objective = OptimizationObjective(solver)
        
        value_vars = {'value': solver.add_variable('value', 0, 1000)}
        cost_vars = {'cost': solver.add_variable('cost', 1, 500)}
        adoption_vars = {'plateau': solver.add_variable('plateau', 100, 950)}
        
        objective.set_balanced_scorecard(
            npv_weight=0.4,
            roi_weight=0.3,
            adoption_weight=0.2,
            cost_weight=0.1,
            value_vars=value_vars,
            cost_vars=cost_vars,
            adoption_vars=adoption_vars
        )
        
        assert objective.current_objective.type == ObjectiveType.BALANCED
        assert 'npv_weight' in objective.current_objective.parameters


class TestConstraintValidator:
    """Test constraint validation functionality."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = ConstraintValidator()
        assert validator.constraint_rules is not None
        assert 'budget' in validator.constraint_rules
        assert 'team_size' in validator.constraint_rules
    
    def test_validate_valid_scenario(self):
        """Test validation of valid scenario."""
        validator = ConstraintValidator()
        
        valid_scenario = {
            'baseline': {'team_size': 50},
            'costs': {'cost_per_seat_month': 50},
            'adoption': {
                'initial_adopters': 0.05,
                'plateau_efficiency': 0.75,
                'dropout_rate_month': 0.02
            },
            'impact': {
                'feature_cycle_reduction': 0.25,
                'bug_fix_reduction': 0.30
            },
            'timeframe_months': 24
        }
        
        result = validator.validate_scenario(valid_scenario, "test_scenario")
        
        assert result.status == ValidationStatus.VALID
        assert result.is_valid
        assert len(result.violations) == 0
    
    def test_validate_scenario_with_violations(self):
        """Test validation with constraint violations."""
        validator = ConstraintValidator()
        
        invalid_scenario = {
            'baseline': {'team_size': -5},  # Invalid: negative
            'costs': {'cost_per_seat_month': 1000},  # Invalid: too high
            'adoption': {
                'initial_adopters': 0.5,  # Invalid: > 0.30
                'plateau_efficiency': 0.4,  # Valid but low
                'dropout_rate_month': 0.5  # Invalid: > 0.10
            },
            'timeframe_months': 1  # Invalid: too short
        }
        
        result = validator.validate_scenario(invalid_scenario, "invalid_test")
        
        assert result.status == ValidationStatus.INVALID
        assert not result.is_valid
        assert len(result.violations) > 0
        assert "Team size" in result.violations[0]
    
    def test_validate_scenario_with_warnings(self):
        """Test validation with warnings."""
        validator = ConstraintValidator()
        
        warning_scenario = {
            'baseline': {'team_size': 2},  # Valid but very small
            'costs': {'cost_per_seat_month': 250},  # Valid but high
            'adoption': {
                'initial_adopters': 0.05,
                'plateau_efficiency': 0.75,
                'dropout_rate_month': 0.02
            },
            'impact': {
                'feature_cycle_reduction': 0.45  # Valid but very optimistic
            },
            'timeframe_months': 24
        }
        
        result = validator.validate_scenario(warning_scenario, "warning_test")
        
        assert result.status == ValidationStatus.WARNING
        assert result.is_valid
        assert len(result.warnings) > 0
    
    def test_extract_value(self):
        """Test value extraction from different formats."""
        validator = ConstraintValidator()
        
        # Test direct value
        assert validator._extract_value(10) == 10.0
        assert validator._extract_value(0.5) == 0.5
        
        # Test distribution with 'value'
        assert validator._extract_value({'value': 20}) == 20.0
        
        # Test distribution with 'mean'
        assert validator._extract_value({'mean': 30}) == 30.0
        
        # Test invalid format
        with pytest.raises(ValidationError):
            validator._extract_value("invalid")
    
    def test_validation_report(self):
        """Test generation of validation report."""
        validator = ConstraintValidator()
        
        scenario = {
            'baseline': {'team_size': 50},
            'costs': {'cost_per_seat_month': 50},
            'timeframe_months': 24
        }
        
        result = validator.validate_scenario(scenario, "test")
        report = result.get_report()
        
        assert "Validation Report" in report
        assert "Status:" in report
        assert "Parameters checked:" in report


class TestIntegration:
    """Integration tests for constraint solver system."""
    
    def test_end_to_end_optimization(self):
        """Test complete optimization workflow."""
        # Create solver
        solver = ConstraintSolver()
        
        # Add variables
        team_size = solver.add_variable('team_size', 10, 100, is_integer=True)
        cost_per_seat = solver.add_variable('cost_per_seat', 30, 100)
        adoption = solver.add_variable('adoption', 100, 900)  # 0.1 to 0.9
        
        # Add business constraints
        business = BusinessConstraints(solver)
        business.add_budget_constraint(3000, team_size, cost_per_seat)
        
        # Set objective
        objective = OptimizationObjective(solver)
        value_vars = {'team_value': team_size * adoption}
        cost_vars = {'total_cost': team_size * cost_per_seat}
        objective.set_roi_maximization(value_vars, cost_vars)
        
        # Solve
        result = solver.solve(time_limit_seconds=10)
        
        assert result.is_successful
        assert 'team_size' in result.optimal_values
        assert 'cost_per_seat' in result.optimal_values
        assert 'adoption' in result.optimal_values
        
        # Check budget constraint is satisfied
        total_cost = (result.optimal_values['team_size'] * 
                     result.optimal_values['cost_per_seat'])
        assert total_cost <= 3000 * 1000  # Account for scaling
    
    def test_scenario_validation_integration(self):
        """Test scenario validation with real constraints."""
        validator = ConstraintValidator()
        
        # Create a borderline scenario
        scenario = {
            'baseline': {
                'team_size': 100,
                'junior_ratio': 0.4,
                'mid_ratio': 0.4,
                'senior_ratio': 0.2
            },
            'adoption': {
                'initial_adopters': 0.15,
                'early_adopters': 0.20,
                'plateau_efficiency': 0.85,
                'dropout_rate_month': 0.05
            },
            'impact': {
                'feature_cycle_reduction': 0.35,
                'bug_fix_reduction': 0.40,
                'defect_reduction': 0.30
            },
            'costs': {
                'cost_per_seat_month': 75
            },
            'timeframe_months': 36
        }
        
        result = validator.validate_scenario(scenario)
        
        # Should be valid or have only warnings
        assert result.status in [ValidationStatus.VALID, ValidationStatus.WARNING]
        assert len(result.parameters_checked) > 0