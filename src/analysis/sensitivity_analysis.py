"""
Advanced sensitivity analysis for understanding parameter importance and interactions.
Implements Sobol indices, partial dependence, and enhanced visualization.
"""

import numpy as np
from typing import Dict, List, Tuple, Callable, Optional, Any
from dataclasses import dataclass
import pandas as pd
from scipy import stats
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

from ..model.monte_carlo import MonteCarloEngine
from ..model.distributions import ParameterDistributions, Distribution
from ..utils.exceptions import CalculationError
from ..utils.cache import cached_result


@dataclass
class SensitivityResults:
    """Container for sensitivity analysis results"""
    
    # First-order Sobol indices (main effects)
    first_order_indices: Dict[str, float]
    
    # Total Sobol indices (including interactions)
    total_indices: Dict[str, float]
    
    # Second-order indices (pairwise interactions)
    second_order_indices: Dict[Tuple[str, str], float]
    
    # Partial dependence data
    partial_dependence: Dict[str, np.ndarray]
    
    # Parameter ranges tested
    parameter_ranges: Dict[str, Tuple[float, float]]
    
    # Convergence metrics
    convergence_achieved: bool
    variance_explained: float
    
    # Computation time
    computation_time: float


class SobolAnalyzer:
    """
    Implements Sobol sensitivity analysis for global sensitivity.
    Based on Saltelli's improved estimators for computational efficiency.
    """
    
    def __init__(self, model_func: Callable, parameter_distributions: ParameterDistributions):
        """
        Initialize Sobol analyzer.
        
        Args:
            model_func: Function that takes parameter dict and returns scalar output
            parameter_distributions: Distributions for all parameters
        """
        self.model_func = model_func
        self.distributions = parameter_distributions
        self.param_names = list(parameter_distributions.distributions.keys())
        self.n_params = len(self.param_names)
    
    def calculate_indices(self, n_samples: int = 1024, 
                         calc_second_order: bool = True) -> SensitivityResults:
        """
        Calculate Sobol sensitivity indices.
        
        Args:
            n_samples: Base sample size (total will be n_samples * (2n_params + 2))
            calc_second_order: Whether to calculate second-order indices
            
        Returns:
            SensitivityResults with all indices
        """
        start_time = time.time()
        
        # Generate sample matrices using Saltelli's scheme
        A, B, AB_matrices = self._generate_sample_matrices(n_samples)
        
        # Evaluate model for all sample points
        Y_A = self._evaluate_model(A)
        Y_B = self._evaluate_model(B)
        Y_AB = [self._evaluate_model(AB) for AB in AB_matrices]
        
        # Calculate variance
        total_variance = np.var(np.concatenate([Y_A, Y_B]))
        
        # Calculate first-order indices
        first_order = {}
        for i, param in enumerate(self.param_names):
            S_i = self._calculate_first_order_index(Y_A, Y_B, Y_AB[i])
            first_order[param] = S_i / total_variance if total_variance > 0 else 0
        
        # Calculate total indices
        total_indices = {}
        for i, param in enumerate(self.param_names):
            S_T = self._calculate_total_index(Y_A, Y_B, Y_AB[i])
            total_indices[param] = S_T / total_variance if total_variance > 0 else 0
        
        # Calculate second-order indices if requested
        second_order = {}
        if calc_second_order:
            for i in range(self.n_params):
                for j in range(i + 1, self.n_params):
                    param_i = self.param_names[i]
                    param_j = self.param_names[j]
                    S_ij = self._calculate_second_order_index(i, j, Y_A, Y_B, Y_AB)
                    S_ij_normalized = S_ij / total_variance if total_variance > 0 else 0
                    # Subtract first-order effects to get pure interaction
                    S_ij_interaction = S_ij_normalized - first_order[param_i] - first_order[param_j]
                    second_order[(param_i, param_j)] = max(0, S_ij_interaction)
        
        # Calculate partial dependence
        partial_dependence = self._calculate_partial_dependence(n_points=20)
        
        # Get parameter ranges
        parameter_ranges = self._get_parameter_ranges()
        
        # Check convergence
        variance_explained = sum(first_order.values())
        convergence_achieved = variance_explained > 0.7  # 70% variance explained
        
        computation_time = time.time() - start_time
        
        return SensitivityResults(
            first_order_indices=first_order,
            total_indices=total_indices,
            second_order_indices=second_order,
            partial_dependence=partial_dependence,
            parameter_ranges=parameter_ranges,
            convergence_achieved=convergence_achieved,
            variance_explained=variance_explained,
            computation_time=computation_time
        )
    
    def _generate_sample_matrices(self, n_samples: int) -> Tuple[np.ndarray, np.ndarray, List[np.ndarray]]:
        """Generate sample matrices using Saltelli's scheme"""
        # Generate two independent sample matrices
        A = np.zeros((n_samples, self.n_params))
        B = np.zeros((n_samples, self.n_params))
        
        # Sample from distributions
        for i, param in enumerate(self.param_names):
            dist = self.distributions.distributions[param]
            A[:, i] = dist.sample(n_samples)
            B[:, i] = dist.sample(n_samples)
        
        # Create AB matrices (A with column i from B)
        AB_matrices = []
        for i in range(self.n_params):
            AB = A.copy()
            AB[:, i] = B[:, i]
            AB_matrices.append(AB)
        
        return A, B, AB_matrices
    
    def _evaluate_model(self, samples: np.ndarray) -> np.ndarray:
        """Evaluate model for sample matrix"""
        n_samples = samples.shape[0]
        results = np.zeros(n_samples)
        
        for i in range(n_samples):
            # Create parameter dictionary
            params = {self.param_names[j]: samples[i, j] 
                     for j in range(self.n_params)}
            
            try:
                results[i] = self.model_func(params)
            except Exception as e:
                # Use mean if evaluation fails
                results[i] = np.nan
        
        # Replace NaN values with mean
        nan_mask = np.isnan(results)
        if np.any(nan_mask):
            results[nan_mask] = np.nanmean(results)
        
        return results
    
    def _calculate_first_order_index(self, Y_A: np.ndarray, Y_B: np.ndarray, 
                                    Y_AB_i: np.ndarray) -> float:
        """Calculate first-order Sobol index using Saltelli estimator"""
        return np.mean(Y_B * (Y_AB_i - Y_A))
    
    def _calculate_total_index(self, Y_A: np.ndarray, Y_B: np.ndarray, 
                               Y_AB_i: np.ndarray) -> float:
        """Calculate total Sobol index"""
        return 0.5 * np.mean((Y_A - Y_AB_i) ** 2)
    
    def _calculate_second_order_index(self, i: int, j: int, Y_A: np.ndarray, 
                                     Y_B: np.ndarray, Y_AB: List[np.ndarray]) -> float:
        """Calculate second-order interaction index"""
        # This is a simplified approach; full implementation would require additional samples
        return np.mean(Y_AB[i] * Y_AB[j]) - np.mean(Y_A) * np.mean(Y_B)
    
    def _calculate_partial_dependence(self, n_points: int = 20) -> Dict[str, np.ndarray]:
        """Calculate partial dependence for each parameter"""
        partial_dep = {}
        
        for param in self.param_names:
            # Get parameter range
            dist = self.distributions.distributions[param]
            if hasattr(dist, 'lower') and hasattr(dist, 'upper'):
                param_range = np.linspace(dist.lower, dist.upper, n_points)
            else:
                # Use percentiles for unbounded distributions
                samples = dist.sample(1000)
                param_range = np.linspace(np.percentile(samples, 5), 
                                        np.percentile(samples, 95), n_points)
            
            # Calculate average model output for each parameter value
            pd_values = np.zeros(n_points)
            for i, value in enumerate(param_range):
                # Fix parameter at value, sample others
                fixed_params = self._sample_other_parameters(param, value, n_samples=100)
                outputs = [self.model_func(params) for params in fixed_params]
                pd_values[i] = np.mean(outputs)
            
            partial_dep[param] = pd_values
        
        return partial_dep
    
    def _sample_other_parameters(self, fixed_param: str, fixed_value: float, 
                                n_samples: int) -> List[Dict[str, float]]:
        """Sample all parameters except one that is fixed"""
        samples = []
        
        for _ in range(n_samples):
            params = {}
            for param in self.param_names:
                if param == fixed_param:
                    params[param] = fixed_value
                else:
                    dist = self.distributions.distributions[param]
                    params[param] = dist.sample(1)[0]
            samples.append(params)
        
        return samples
    
    def _get_parameter_ranges(self) -> Dict[str, Tuple[float, float]]:
        """Get min/max range for each parameter"""
        ranges = {}
        
        for param in self.param_names:
            dist = self.distributions.distributions[param]
            if hasattr(dist, 'lower') and hasattr(dist, 'upper'):
                ranges[param] = (dist.lower, dist.upper)
            else:
                # Use percentiles for unbounded distributions
                samples = dist.sample(1000)
                ranges[param] = (np.percentile(samples, 1), np.percentile(samples, 99))
        
        return ranges


class LocalSensitivityAnalyzer:
    """
    Performs local sensitivity analysis around a baseline point.
    Useful for understanding parameter importance at specific scenarios.
    """
    
    def __init__(self, model_func: Callable, baseline_params: Dict[str, float]):
        """
        Initialize local sensitivity analyzer.
        
        Args:
            model_func: Function that takes parameter dict and returns scalar
            baseline_params: Baseline parameter values
        """
        self.model_func = model_func
        self.baseline_params = baseline_params
        self.baseline_output = model_func(baseline_params)
    
    def calculate_elasticities(self, perturbation: float = 0.01) -> Dict[str, float]:
        """
        Calculate elasticities (percentage change in output per percentage change in input).
        
        Args:
            perturbation: Fraction to perturb parameters (e.g., 0.01 = 1%)
            
        Returns:
            Dictionary of elasticities for each parameter
        """
        elasticities = {}
        
        for param, base_value in self.baseline_params.items():
            # Perturb parameter
            perturbed_params = self.baseline_params.copy()
            perturbed_value = base_value * (1 + perturbation)
            perturbed_params[param] = perturbed_value
            
            # Calculate output change
            try:
                perturbed_output = self.model_func(perturbed_params)
                
                # Calculate elasticity
                output_change = (perturbed_output - self.baseline_output) / self.baseline_output
                input_change = perturbation
                
                elasticity = output_change / input_change if input_change != 0 else 0
                elasticities[param] = elasticity
                
            except Exception:
                elasticities[param] = 0.0
        
        return elasticities
    
    def calculate_gradients(self, epsilon: float = 1e-6) -> Dict[str, float]:
        """
        Calculate numerical gradients using finite differences.
        
        Args:
            epsilon: Small value for numerical differentiation
            
        Returns:
            Dictionary of gradients for each parameter
        """
        gradients = {}
        
        for param, base_value in self.baseline_params.items():
            # Forward difference
            forward_params = self.baseline_params.copy()
            forward_params[param] = base_value + epsilon
            
            try:
                forward_output = self.model_func(forward_params)
                gradient = (forward_output - self.baseline_output) / epsilon
                gradients[param] = gradient
            except Exception:
                gradients[param] = 0.0
        
        return gradients


def create_sensitivity_report(results: SensitivityResults) -> str:
    """
    Create a formatted sensitivity analysis report.
    
    Args:
        results: Sensitivity analysis results
        
    Returns:
        Formatted markdown report
    """
    report = []
    report.append("# Sensitivity Analysis Report\n")
    report.append(f"**Analysis completed in {results.computation_time:.2f} seconds**\n")
    report.append(f"**Variance explained: {results.variance_explained:.1%}**\n")
    report.append(f"**Convergence achieved: {'Yes' if results.convergence_achieved else 'No'}**\n")
    
    # First-order indices (main effects)
    report.append("\n## Main Effects (First-Order Sobol Indices)\n")
    report.append("| Parameter | Sensitivity Index | Importance |")
    report.append("|-----------|------------------|------------|")
    
    sorted_first = sorted(results.first_order_indices.items(), 
                         key=lambda x: x[1], reverse=True)
    
    for param, index in sorted_first[:10]:  # Top 10
        importance = "🔴 High" if index > 0.1 else "🟡 Medium" if index > 0.01 else "🟢 Low"
        report.append(f"| {param:<30} | {index:>6.3f} | {importance} |")
    
    # Total indices (including interactions)
    report.append("\n## Total Effects (Including Interactions)\n")
    report.append("| Parameter | Total Index | Interaction Strength |")
    report.append("|-----------|-------------|---------------------|")
    
    for param, total in sorted(results.total_indices.items(), 
                               key=lambda x: x[1], reverse=True)[:10]:
        first = results.first_order_indices.get(param, 0)
        interaction = total - first
        strength = "Strong" if interaction > 0.05 else "Moderate" if interaction > 0.01 else "Weak"
        report.append(f"| {param:<30} | {total:>6.3f} | {strength} ({interaction:.3f}) |")
    
    # Important interactions
    if results.second_order_indices:
        report.append("\n## Important Parameter Interactions\n")
        report.append("| Parameter 1 | Parameter 2 | Interaction Index |")
        report.append("|-------------|-------------|-------------------|")
        
        sorted_interactions = sorted(results.second_order_indices.items(), 
                                   key=lambda x: x[1], reverse=True)
        
        for (param1, param2), index in sorted_interactions[:5]:  # Top 5
            if index > 0.001:  # Only show meaningful interactions
                report.append(f"| {param1:<20} | {param2:<20} | {index:>6.4f} |")
    
    return "\n".join(report)


@cached_result(ttl_seconds=7200)  # Cache for 2 hours
def perform_sensitivity_analysis(scenario_name: str, model_func: Callable,
                                parameter_distributions: ParameterDistributions,
                                n_samples: int = 512) -> SensitivityResults:
    """
    Perform comprehensive sensitivity analysis for a scenario.
    
    Args:
        scenario_name: Name of scenario for caching
        model_func: Function to analyze
        parameter_distributions: Parameter distributions
        n_samples: Number of samples for Sobol analysis
        
    Returns:
        Complete sensitivity analysis results
    """
    analyzer = SobolAnalyzer(model_func, parameter_distributions)
    return analyzer.calculate_indices(n_samples, calc_second_order=True)