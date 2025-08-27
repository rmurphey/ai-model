#!/usr/bin/env python3
"""Simple test script for constraint solver."""

from src.constraints import ConstraintSolver, SolverStatus
from ortools.sat.python import cp_model

# Create solver
solver = ConstraintSolver(use_integer_solver=False)

# Add variables (scaled by 1000 for CP-SAT)
team_size = solver.add_variable('team_size', 10, 100, is_integer=True)
cost_per_seat = solver.add_variable('cost_per_seat', 30, 100, is_integer=True)

# For products, we need to create an intermediate variable
total_cost = solver.model.NewIntVar(10 * 30, 100 * 100, 'total_cost')
solver.model.AddMultiplicationEquality(total_cost, [team_size, cost_per_seat])

# Add constraint: total_cost <= 5000
budget = 5000
solver.add_constraint(total_cost <= budget, "budget_constraint")

# Objective: minimize total cost
solver.set_objective(total_cost, maximize=False)

# Solve
print("Solving optimization problem...")
result = solver.solve(time_limit_seconds=5)

print(f"\nStatus: {result.status}")
print(f"Message: {result.message}")

if result.is_successful:
    print(f"\nOptimal solution found:")
    print(f"  Team size: {result.optimal_values.get('team_size', 'N/A')}")
    print(f"  Cost per seat: ${result.optimal_values.get('cost_per_seat', 'N/A')}")
    total_cost = result.optimal_values['team_size'] * result.optimal_values['cost_per_seat']
    print(f"  Total monthly cost: ${total_cost:.0f}")
else:
    print("No feasible solution found")