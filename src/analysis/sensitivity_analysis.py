"""
Sensitivity analysis for AI impact model using SALib.
Uses Sobol and Morris methods for global sensitivity analysis.
"""

import numpy as np
import pandas as pd
import time
from typing import Dict, List, Any, Callable, Tuple, Optional
from dataclasses import dataclass

# Import SALib components
from SALib.sample import saltelli
from SALib.analyze import sobol

from ..model.distributions import ParameterDistributions, Distribution


@dataclass
class SensitivityResults:
    """Results from sensitivity analysis"""
    
    # First-order indices (main effects)
    first_order_indices: Dict[str, float]
    
    # Total indices (including interactions)
    total_indices: Dict[str, float]
    
    # Second-order indices (pairwise interactions)
    second_order_indices: Dict[Tuple[str, str], float]
    
    # Confidence intervals
    first_order_conf: Optional[Dict[str, Tuple[float, float]]]
    total_conf: Optional[Dict[str, Tuple[float, float]]]
    
    # Additional metadata
    n_samples: int
    n_params: int
    
    # Model evaluation statistics
    model_outputs_mean: float
    model_outputs_std: float
    
    # Partial dependence data (optional, not computed by default)
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
    Implements Sobol sensitivity analysis using SALib.
    Provides a clean interface while leveraging SALib's robust implementation.
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
        
        # Build SALib problem definition
        self.problem = self._build_problem_definition()
    
    def _build_problem_definition(self) -> Dict[str, Any]:
        """Build SALib problem definition from parameter distributions"""
        bounds = []
        
        for param_name in self.param_names:
            dist = self.distributions.distributions[param_name]
            
            # Extract bounds from distribution
            if hasattr(dist, 'min_val') and hasattr(dist, 'max_val') and dist.min_val is not None and dist.max_val is not None:
                # Uniform or bounded distribution
                bounds.append([dist.min_val, dist.max_val])
            elif hasattr(dist, 'mean_val') and hasattr(dist, 'std_val'):
                # Normal distribution - use 3 sigma bounds
                mean = dist.mean_val
                std = dist.std_val
                bounds.append([mean - 3*std, mean + 3*std])
            elif hasattr(dist, 'lower') and hasattr(dist, 'upper'):
                # Generic bounded distribution
                bounds.append([dist.lower, dist.upper])
            else:
                # Default bounds for unbounded distributions
                # Sample to estimate reasonable bounds
                samples = [dist.sample(1)[0] for _ in range(1000)]
                lower = np.percentile(samples, 1)
                upper = np.percentile(samples, 99)
                bounds.append([lower, upper])
        
        return {
            'num_vars': self.n_params,
            'names': self.param_names,
            'bounds': bounds
        }
    
    def calculate_indices(self, n_samples: int = 1024, 
                         calc_second_order: bool = True,
                         conf_level: float = 0.95) -> SensitivityResults:
        """
        Calculate Sobol sensitivity indices using SALib.
        
        Args:
            n_samples: Base sample size for Saltelli sampling
            calc_second_order: Whether to calculate second-order indices
            conf_level: Confidence level for bootstrap intervals
            
        Returns:
            SensitivityResults with all indices and confidence intervals
        """
        start_time = time.time()
        
        # Generate samples using Saltelli's scheme
        param_values = saltelli.sample(self.problem, n_samples, 
                                      calc_second_order=calc_second_order)
        
        # Evaluate model for all sample points
        Y = np.zeros(param_values.shape[0])
        for i, params in enumerate(param_values):
            # Convert array to dict for model function
            param_dict = {name: val for name, val in zip(self.param_names, params)}
            try:
                Y[i] = self.model_func(param_dict)
            except Exception as e:
                # Handle model failures gracefully
                Y[i] = np.nan
        
        # Remove NaN values
        valid_mask = ~np.isnan(Y)
        if not np.any(valid_mask):
            # All evaluations failed
            return self._empty_results(start_time)
        
        Y_valid = Y[valid_mask]
        param_values_valid = param_values[valid_mask]
        
        # Perform Sobol analysis
        Si = sobol.analyze(self.problem, Y_valid, 
                          calc_second_order=calc_second_order,
                          conf_level=conf_level)
        
        # Extract results
        first_order = {name: Si['S1'][i] for i, name in enumerate(self.param_names)}
        total_indices = {name: Si['ST'][i] for i, name in enumerate(self.param_names)}
        
        # Extract confidence intervals if available
        first_conf = None
        total_conf = None
        if 'S1_conf' in Si:
            first_conf = {name: (Si['S1'][i] - Si['S1_conf'][i], 
                                Si['S1'][i] + Si['S1_conf'][i]) 
                         for i, name in enumerate(self.param_names)}
        if 'ST_conf' in Si:
            total_conf = {name: (Si['ST'][i] - Si['ST_conf'][i],
                                Si['ST'][i] + Si['ST_conf'][i])
                         for i, name in enumerate(self.param_names)}
        
        # Extract second-order indices if calculated
        second_order = {}
        if calc_second_order and 'S2' in Si:
            idx = 0
            for i in range(self.n_params):
                for j in range(i + 1, self.n_params):
                    second_order[(self.param_names[i], self.param_names[j])] = Si['S2'][i, j]
        
        # Calculate convergence and variance explained
        # Convergence: check if confidence intervals are reasonably tight
        convergence_achieved = True
        if first_conf:
            for name in self.param_names:
                conf_width = first_conf[name][1] - first_conf[name][0]
                if conf_width > 0.1:  # If confidence interval > 0.1, not converged
                    convergence_achieved = False
                    break
        
        # Variance explained by first-order indices
        variance_explained = sum(first_order.values())
        
        # Get parameter ranges
        parameter_ranges = {name: tuple(bounds) 
                          for name, bounds in zip(self.param_names, self.problem['bounds'])}
        
        # Calculate partial dependence (empty for now, can be added if needed)
        partial_dependence = {}
        
        computation_time = time.time() - start_time
        
        return SensitivityResults(
            first_order_indices=first_order,
            total_indices=total_indices,
            second_order_indices=second_order,
            first_order_conf=first_conf,
            total_conf=total_conf,
            n_samples=n_samples,
            n_params=self.n_params,
            model_outputs_mean=float(np.mean(Y_valid)),
            model_outputs_std=float(np.std(Y_valid)),
            partial_dependence=partial_dependence,
            parameter_ranges=parameter_ranges,
            convergence_achieved=convergence_achieved,
            variance_explained=variance_explained,
            computation_time=computation_time
        )
    
    def _empty_results(self, start_time: float) -> SensitivityResults:
        """Return empty results when all model evaluations fail"""
        empty_dict = {name: 0.0 for name in self.param_names}
        return SensitivityResults(
            first_order_indices=empty_dict,
            total_indices=empty_dict,
            second_order_indices={},
            first_order_conf=None,
            total_conf=None,
            n_samples=0,
            n_params=self.n_params,
            model_outputs_mean=0.0,
            model_outputs_std=0.0,
            partial_dependence={},
            parameter_ranges={name: (0.0, 0.0) for name in self.param_names},
            convergence_achieved=False,
            variance_explained=0.0,
            computation_time=time.time() - start_time
        )


def format_sensitivity_report(results: SensitivityResults) -> str:
    """
    Format sensitivity analysis results as a readable report.
    
    Args:
        results: SensitivityResults from analysis
        
    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 60)
    report.append("SENSITIVITY ANALYSIS REPORT")
    report.append("=" * 60)
    
    # Summary statistics
    report.append(f"\nAnalysis Summary:")
    report.append(f"  Parameters analyzed: {results.n_params}")
    report.append(f"  Sample size: {results.n_samples}")
    report.append(f"  Computation time: {results.computation_time:.2f} seconds")
    report.append(f"  Model output mean: {results.model_outputs_mean:.4f}")
    report.append(f"  Model output std: {results.model_outputs_std:.4f}")
    report.append(f"  Variance explained (first-order): {results.variance_explained:.1%}")
    report.append(f"  Convergence achieved: {results.convergence_achieved}")
    
    # First-order indices (sorted by importance)
    report.append("\n" + "-" * 40)
    report.append("FIRST-ORDER SENSITIVITY INDICES")
    report.append("(Direct parameter influence)")
    report.append("-" * 40)
    
    sorted_first = sorted(results.first_order_indices.items(), 
                         key=lambda x: abs(x[1]), reverse=True)
    
    for param, value in sorted_first:
        conf_str = ""
        if results.first_order_conf and param in results.first_order_conf:
            conf = results.first_order_conf[param]
            conf_str = f" [{conf[0]:.3f}, {conf[1]:.3f}]"
        report.append(f"  {param:20s}: {value:7.4f}{conf_str}")
    
    # Total indices
    report.append("\n" + "-" * 40)
    report.append("TOTAL SENSITIVITY INDICES")
    report.append("(Including interaction effects)")
    report.append("-" * 40)
    
    sorted_total = sorted(results.total_indices.items(),
                         key=lambda x: abs(x[1]), reverse=True)
    
    for param, value in sorted_total:
        conf_str = ""
        if results.total_conf and param in results.total_conf:
            conf = results.total_conf[param]
            conf_str = f" [{conf[0]:.3f}, {conf[1]:.3f}]"
        report.append(f"  {param:20s}: {value:7.4f}{conf_str}")
    
    # Interaction effects (difference between total and first-order)
    report.append("\n" + "-" * 40)
    report.append("INTERACTION EFFECTS")
    report.append("(Total - First Order)")
    report.append("-" * 40)
    
    interactions = {}
    for param in results.first_order_indices:
        interactions[param] = results.total_indices[param] - results.first_order_indices[param]
    
    sorted_interactions = sorted(interactions.items(),
                                key=lambda x: abs(x[1]), reverse=True)
    
    for param, value in sorted_interactions[:10]:
        report.append(f"  {param:20s}: {value:7.4f}")
    
    # Second-order indices if available
    if results.second_order_indices:
        report.append("\n" + "-" * 40)
        report.append("TOP PAIRWISE INTERACTIONS")
        report.append("-" * 40)
        
        sorted_second = sorted(results.second_order_indices.items(),
                              key=lambda x: abs(x[1]), reverse=True)
        
        for (param1, param2), value in sorted_second[:10]:
            if abs(value) > 0.01:  # Only show significant interactions
                report.append(f"  {param1} × {param2}: {value:.4f}")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)


def run_sobol_analysis(model_func: Callable,
                       parameter_distributions: ParameterDistributions,
                       n_samples: int = 1024,
                       calc_second_order: bool = True) -> SensitivityResults:
    """
    Convenience function to run Sobol sensitivity analysis.
    
    Args:
        model_func: Function mapping parameters to output
        parameter_distributions: Parameter distributions
        n_samples: Number of samples for analysis
        calc_second_order: Whether to calculate second-order indices
        
    Returns:
        SensitivityResults with indices and statistics
    """
    analyzer = SobolAnalyzer(model_func, parameter_distributions)
    return analyzer.calculate_indices(n_samples, calc_second_order=calc_second_order)


# Aliases for backward compatibility
create_sensitivity_report = format_sensitivity_report
perform_sensitivity_analysis = run_sobol_analysis


def run_sensitivity_analysis(scenario_name: str, n_samples: int = 512) -> Dict[str, Any]:
    """
    Run sensitivity analysis for a specific scenario.
    
    This is a convenience function for batch processing that wraps the full
    sensitivity analysis pipeline.
    
    Args:
        scenario_name: Name of the scenario to analyze
        n_samples: Number of samples for Sobol analysis
        
    Returns:
        Dictionary with ranked parameters and variance explained
    """
    from main import AIImpactModel
    from ..scenarios.scenario_loader import ScenarioLoader
    
    # Load scenario configuration
    loader = ScenarioLoader()
    scenario_config = loader.load_scenario(scenario_name)
    
    # Add key parameters with reasonable variation ranges
    base_params = {
        'adoption_rate': scenario_config.get('adoption', {}).get('early_adopters', 0.15),
        'feature_cycle_reduction': scenario_config.get('impact', {}).get('feature_cycle_reduction', 0.25),
        'defect_reduction': scenario_config.get('impact', {}).get('defect_reduction', 0.30),
        'cost_per_seat': scenario_config.get('costs', {}).get('cost_per_seat_month', 50),
        'token_price': scenario_config.get('costs', {}).get('token_price_per_million', 8),
    }
    
    # Create distributions with ±30% variation
    from ..model.distributions import Uniform
    param_distributions = ParameterDistributions()
    for param_name, base_value in base_params.items():
        # Handle negative values correctly
        if base_value >= 0:
            min_val = base_value * 0.7
            max_val = base_value * 1.3
        else:
            # For negative values, reverse the order
            min_val = base_value * 1.3
            max_val = base_value * 0.7
        
        # Handle zero values
        if abs(base_value) < 0.001:
            min_val = -0.1
            max_val = 0.1
            
        param_distributions.add_distribution(
            param_name,
            Uniform(min_val=min_val, max_val=max_val)
        )
    
    # Define model function for sensitivity analysis
    def model_function(params: Dict[str, float]) -> float:
        """Evaluate model with given parameters and return NPV"""
        model = AIImpactModel()
        
        # Override scenario parameters
        modified_config = scenario_config.copy()
        modified_config.setdefault('adoption', {})['early_adopters'] = params['adoption_rate']
        modified_config.setdefault('impact', {})['feature_cycle_reduction'] = params['feature_cycle_reduction']
        modified_config.setdefault('impact', {})['defect_reduction'] = params['defect_reduction']
        modified_config.setdefault('costs', {})['cost_per_seat_month'] = params['cost_per_seat']
        modified_config.setdefault('costs', {})['token_price_per_million'] = params['token_price']
        
        # Run analysis
        try:
            results = model._run_scenario_cached(scenario_name, custom_config=modified_config)
            return results.get('npv', 0)
        except Exception:
            return 0
    
    # Run sensitivity analysis
    sensitivity_results = run_sobol_analysis(
        model_function,
        param_distributions,
        n_samples=n_samples,
        calc_second_order=True
    )
    
    # Format results for batch processing
    ranked_params = sorted(
        sensitivity_results.first_order_indices.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return {
        'ranked_parameters': [
            {'name': param, 'importance': float(value)}
            for param, value in ranked_params
        ],
        'variance_explained': sensitivity_results.variance_explained
    }