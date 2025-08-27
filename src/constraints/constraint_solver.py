"""
Main constraint solver interface using OR-Tools.
Provides optimization and constraint satisfaction capabilities for the AI impact model.
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np
from ortools.sat.python import cp_model
from ortools.linear_solver import pywraplp

from ..utils.exceptions import ValidationError, CalculationError


class SolverStatus(Enum):
    """Status of constraint solver execution."""
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class OptimizationResult:
    """Results from constraint optimization."""
    
    status: SolverStatus
    optimal_values: Dict[str, float]
    objective_value: Optional[float]
    constraints_satisfied: List[str]
    constraints_violated: List[str]
    solve_time_seconds: float
    iterations: int
    message: str
    
    @property
    def is_successful(self) -> bool:
        """Check if optimization was successful."""
        return self.status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE]


class ConstraintSolver:
    """
    Main constraint solver for AI impact model optimization.
    Uses OR-Tools CP-SAT solver for constraint programming.
    """
    
    def __init__(self, use_integer_solver: bool = False):
        """
        Initialize constraint solver.
        
        Args:
            use_integer_solver: Use mixed-integer programming instead of CP-SAT
        """
        self.use_integer_solver = use_integer_solver
        self.variables = {}
        self.constraints = []
        self.objective = None
        self.bounds = {}
        self.solution = None
        
        if use_integer_solver:
            # Use SCIP mixed-integer solver
            self.solver = pywraplp.Solver.CreateSolver('SCIP')
            if not self.solver:
                raise CalculationError(
                    "Failed to create OR-Tools solver",
                    {"solver_type": "SCIP"},
                    "Ensure OR-Tools is properly installed"
                )
        else:
            # Use CP-SAT constraint programming solver
            self.model = cp_model.CpModel()
            self.solver = cp_model.CpSolver()
    
    def add_variable(self, name: str, min_val: float, max_val: float, 
                     is_integer: bool = False) -> Any:
        """
        Add a decision variable to the model.
        
        Args:
            name: Variable name
            min_val: Minimum value
            max_val: Maximum value
            is_integer: Whether variable must be integer
            
        Returns:
            Variable object for use in constraints
        """
        if name in self.variables:
            raise ValidationError(
                field_name="variable_name",
                value=name,
                expected="unique variable name",
                suggestion=f"Variable '{name}' already exists"
            )
        
        self.bounds[name] = (min_val, max_val)
        
        if self.use_integer_solver:
            if is_integer:
                var = self.solver.IntVar(min_val, max_val, name)
            else:
                var = self.solver.NumVar(min_val, max_val, name)
        else:
            # CP-SAT uses integer domain, so scale floats by 1000
            scale = 1000 if not is_integer else 1
            var = self.model.NewIntVar(
                int(min_val * scale),
                int(max_val * scale),
                name
            )
            self.variables[name] = (var, scale)
            return var
        
        self.variables[name] = var
        return var
    
    def add_constraint(self, constraint: Any, name: str = "") -> None:
        """
        Add a constraint to the model.
        
        Args:
            constraint: Constraint expression
            name: Optional name for the constraint
        """
        if self.use_integer_solver:
            self.solver.Add(constraint)
        else:
            self.model.Add(constraint)
        
        if name:
            self.constraints.append(name)
    
    def set_objective(self, objective: Any, maximize: bool = True) -> None:
        """
        Set the optimization objective.
        
        Args:
            objective: Objective expression
            maximize: Whether to maximize (True) or minimize (False)
        """
        self.objective = objective
        
        if self.use_integer_solver:
            if maximize:
                self.solver.Maximize(objective)
            else:
                self.solver.Minimize(objective)
        else:
            if maximize:
                self.model.Maximize(objective)
            else:
                self.model.Minimize(objective)
    
    def solve(self, time_limit_seconds: int = 60) -> OptimizationResult:
        """
        Solve the constraint optimization problem.
        
        Args:
            time_limit_seconds: Maximum time to spend solving
            
        Returns:
            OptimizationResult with solution details
        """
        if self.use_integer_solver:
            return self._solve_mip(time_limit_seconds)
        else:
            return self._solve_cpsat(time_limit_seconds)
    
    def _solve_cpsat(self, time_limit_seconds: int) -> OptimizationResult:
        """Solve using CP-SAT solver."""
        self.solver.parameters.max_time_in_seconds = time_limit_seconds
        
        status = self.solver.Solve(self.model)
        
        # Map CP-SAT status to our status enum
        status_map = {
            cp_model.OPTIMAL: SolverStatus.OPTIMAL,
            cp_model.FEASIBLE: SolverStatus.FEASIBLE,
            cp_model.INFEASIBLE: SolverStatus.INFEASIBLE,
            cp_model.MODEL_INVALID: SolverStatus.ERROR,
            cp_model.UNKNOWN: SolverStatus.UNKNOWN
        }
        
        solver_status = status_map.get(status, SolverStatus.UNKNOWN)
        
        # Extract solution values
        optimal_values = {}
        if solver_status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE]:
            for name, (var, scale) in self.variables.items():
                optimal_values[name] = self.solver.Value(var) / scale
        
        # Get objective value
        objective_value = None
        if solver_status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE] and self.objective is not None:
            objective_value = self.solver.ObjectiveValue()
            # Scale back if needed
            if not self.use_integer_solver:
                objective_value = objective_value / 1000
        
        return OptimizationResult(
            status=solver_status,
            optimal_values=optimal_values,
            objective_value=objective_value,
            constraints_satisfied=self.constraints if solver_status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE] else [],
            constraints_violated=[] if solver_status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE] else self.constraints,
            solve_time_seconds=self.solver.WallTime(),
            iterations=self.solver.NumBranches(),
            message=self._get_status_message(solver_status)
        )
    
    def _solve_mip(self, time_limit_seconds: int) -> OptimizationResult:
        """Solve using mixed-integer programming solver."""
        self.solver.SetTimeLimit(time_limit_seconds * 1000)  # milliseconds
        
        result_status = self.solver.Solve()
        
        # Map MIP status to our status enum
        status_map = {
            pywraplp.Solver.OPTIMAL: SolverStatus.OPTIMAL,
            pywraplp.Solver.FEASIBLE: SolverStatus.FEASIBLE,
            pywraplp.Solver.INFEASIBLE: SolverStatus.INFEASIBLE,
            pywraplp.Solver.UNBOUNDED: SolverStatus.UNBOUNDED,
            pywraplp.Solver.ABNORMAL: SolverStatus.ERROR,
            pywraplp.Solver.NOT_SOLVED: SolverStatus.UNKNOWN
        }
        
        solver_status = status_map.get(result_status, SolverStatus.UNKNOWN)
        
        # Extract solution values
        optimal_values = {}
        if solver_status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE]:
            for name, var in self.variables.items():
                optimal_values[name] = var.solution_value()
        
        # Get objective value
        objective_value = None
        if solver_status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE]:
            objective_value = self.solver.Objective().Value()
        
        return OptimizationResult(
            status=solver_status,
            optimal_values=optimal_values,
            objective_value=objective_value,
            constraints_satisfied=self.constraints if solver_status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE] else [],
            constraints_violated=[] if solver_status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE] else self.constraints,
            solve_time_seconds=self.solver.WallTime() / 1000.0,
            iterations=self.solver.iterations(),
            message=self._get_status_message(solver_status)
        )
    
    def _get_status_message(self, status: SolverStatus) -> str:
        """Get human-readable message for solver status."""
        messages = {
            SolverStatus.OPTIMAL: "Found optimal solution",
            SolverStatus.FEASIBLE: "Found feasible solution (may not be optimal)",
            SolverStatus.INFEASIBLE: "No feasible solution exists with given constraints",
            SolverStatus.UNBOUNDED: "Problem is unbounded - check constraint definitions",
            SolverStatus.UNKNOWN: "Could not determine solution status",
            SolverStatus.ERROR: "Solver encountered an error"
        }
        return messages.get(status, "Unknown solver status")
    
    def add_linear_constraint(self, coefficients: Dict[str, float], 
                            operator: str, rhs: float, name: str = "") -> None:
        """
        Add a linear constraint of the form: sum(coef * var) operator rhs.
        
        Args:
            coefficients: Dictionary mapping variable names to coefficients
            operator: Constraint operator ('<=', '>=', '==')
            rhs: Right-hand side value
            name: Optional constraint name
        """
        if not coefficients:
            raise ValidationError(
                field_name="coefficients",
                value=coefficients,
                expected="non-empty dictionary",
                suggestion="Provide at least one variable-coefficient pair"
            )
        
        # Build linear expression
        expr = None
        for var_name, coef in coefficients.items():
            if var_name not in self.variables:
                raise ValidationError(
                    field_name="variable",
                    value=var_name,
                    expected="existing variable",
                    suggestion=f"Variable '{var_name}' not found. Add it first with add_variable()"
                )
            
            if self.use_integer_solver:
                var = self.variables[var_name]
                term = coef * var
            else:
                var, scale = self.variables[var_name]
                term = int(coef * scale) * var
                
            expr = term if expr is None else expr + term
        
        # Apply operator
        if self.use_integer_solver:
            if operator == '<=':
                constraint = expr <= rhs
            elif operator == '>=':
                constraint = expr >= rhs
            elif operator == '==':
                constraint = expr == rhs
            else:
                raise ValidationError(
                    field_name="operator",
                    value=operator,
                    expected="valid operator",
                    suggestion="Use one of: '<=', '>=', '=='"
                )
        else:
            # Scale RHS for CP-SAT
            rhs_scaled = int(rhs * 1000)
            if operator == '<=':
                constraint = expr <= rhs_scaled
            elif operator == '>=':
                constraint = expr >= rhs_scaled
            elif operator == '==':
                constraint = expr == rhs_scaled
            else:
                raise ValidationError(
                    field_name="operator",
                    value=operator,
                    expected="valid operator",
                    suggestion="Use one of: '<=', '>=', '=='"
                )
        
        self.add_constraint(constraint, name)
    
    def get_variable_value(self, name: str) -> Optional[float]:
        """
        Get the value of a variable from the solution.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value if solved, None otherwise
        """
        if not self.solution or name not in self.solution.optimal_values:
            return None
        return self.solution.optimal_values[name]