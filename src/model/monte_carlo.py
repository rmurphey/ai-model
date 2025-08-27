"""
Monte Carlo simulation engine for probabilistic business impact analysis.
Runs multiple iterations with sampled parameters to generate confidence intervals.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Callable
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

from .distributions import (
    ParameterDistributions, Distribution, Deterministic, create_distribution_from_config,
    Triangular, Beta, Uniform, LogNormal, Normal
)
from .baseline import BaselineMetrics
from .impact_model import ImpactFactors
from .adoption_dynamics import AdoptionParameters
from .cost_structure import AIToolCosts
from ..utils.exceptions import CalculationError, ValidationError
from ..config.constants import DEFAULT_DISCOUNT_RATE_ANNUAL


@dataclass
class MonteCarloResults:
    """Container for Monte Carlo simulation results"""
    
    # Core metrics distributions
    npv_distribution: np.ndarray
    roi_distribution: np.ndarray
    breakeven_distribution: np.ndarray
    total_value_distribution: np.ndarray
    total_cost_distribution: np.ndarray
    
    # Statistical summaries
    npv_stats: Dict[str, float]  # mean, std, p10, p50, p90, etc.
    roi_stats: Dict[str, float]
    breakeven_stats: Dict[str, float]
    value_stats: Dict[str, float]
    cost_stats: Dict[str, float]
    
    # Risk metrics
    probability_positive_npv: float
    probability_breakeven_within_24_months: float
    probability_roi_above_target: float
    
    # Sensitivity analysis
    parameter_correlations: Dict[str, float]  # Correlation with NPV
    parameter_importance: List[Tuple[str, float]]  # Ranked by impact
    
    # Metadata
    iterations: int
    convergence_achieved: bool
    runtime_seconds: float
    random_seed: Optional[int]
    
    def get_confidence_interval(self, metric: str, confidence: float = 0.95) -> Tuple[float, float]:
        """Get confidence interval for a specific metric"""
        alpha = (1 - confidence) / 2
        
        if metric == 'npv':
            dist = self.npv_distribution
        elif metric == 'roi':
            dist = self.roi_distribution
        elif metric == 'breakeven':
            dist = self.breakeven_distribution
        elif metric == 'value':
            dist = self.total_value_distribution
        elif metric == 'cost':
            dist = self.total_cost_distribution
        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        lower = np.percentile(dist, alpha * 100)
        upper = np.percentile(dist, (1 - alpha) * 100)
        
        return (lower, upper)


class MonteCarloEngine:
    """Engine for running Monte Carlo simulations on the AI impact model"""
    
    def __init__(self, 
                 model_runner: Callable,
                 parameter_distributions: ParameterDistributions,
                 iterations: int = 1000,
                 confidence_level: float = 0.95,
                 target_roi: float = 100.0,
                 convergence_threshold: float = 0.01,
                 random_seed: Optional[int] = None,
                 n_jobs: int = 1):
        """
        Initialize Monte Carlo engine.
        
        Args:
            model_runner: Function that takes parameters and returns results dict
            parameter_distributions: Distribution definitions for all parameters
            iterations: Number of simulation iterations
            confidence_level: Confidence level for intervals (e.g., 0.95 for 95%)
            target_roi: Target ROI for probability calculations
            convergence_threshold: Threshold for convergence checking
            random_seed: Random seed for reproducibility
            n_jobs: Number of parallel processes (-1 for all CPUs)
        """
        self.model_runner = model_runner
        self.parameter_distributions = parameter_distributions
        self.iterations = iterations
        self.confidence_level = confidence_level
        self.target_roi = target_roi
        self.convergence_threshold = convergence_threshold
        self.random_seed = random_seed
        self.n_jobs = n_jobs if n_jobs > 0 else mp.cpu_count()
        
        # Initialize random state
        self.random_state = np.random.RandomState(random_seed)
    
    def run(self, base_scenario_config: Dict[str, Any]) -> MonteCarloResults:
        """
        Run Monte Carlo simulation.
        
        Args:
            base_scenario_config: Base configuration to modify with sampled parameters
            
        Returns:
            MonteCarloResults with distributions and statistics
        """
        start_time = time.time()
        
        # Generate parameter samples for all iterations
        parameter_samples = self.parameter_distributions.sample_all(
            size=self.iterations, 
            random_state=self.random_state
        )
        
        # Storage for results
        npv_values = np.zeros(self.iterations)
        roi_values = np.zeros(self.iterations)
        breakeven_values = np.zeros(self.iterations)
        value_values = np.zeros(self.iterations)
        cost_values = np.zeros(self.iterations)
        
        # Track parameters for sensitivity analysis
        parameter_values = {param: samples for param, samples in parameter_samples.items()}
        
        # Run simulations
        if self.n_jobs == 1:
            # Sequential execution
            for i in range(self.iterations):
                params = {k: v[i] for k, v in parameter_samples.items()}
                results = self._run_single_iteration(base_scenario_config, params, i)
                
                npv_values[i] = results['npv']
                roi_values[i] = results['roi_percent']
                breakeven_values[i] = results['breakeven_month']
                value_values[i] = results['total_value_3y']
                cost_values[i] = results['total_cost_3y']
        else:
            # Parallel execution
            npv_values, roi_values, breakeven_values, value_values, cost_values = \
                self._run_parallel_simulations(base_scenario_config, parameter_samples)
        
        # Check convergence
        convergence_achieved = self._check_convergence(npv_values)
        
        # Calculate statistics
        npv_stats = self._calculate_statistics(npv_values)
        roi_stats = self._calculate_statistics(roi_values)
        breakeven_stats = self._calculate_statistics(breakeven_values)
        value_stats = self._calculate_statistics(value_values)
        cost_stats = self._calculate_statistics(cost_values)
        
        # Calculate risk metrics
        prob_positive_npv = np.mean(npv_values > 0)
        prob_breakeven_24 = np.mean(breakeven_values <= 24)
        prob_roi_target = np.mean(roi_values >= self.target_roi)
        
        # Sensitivity analysis
        param_correlations = self._calculate_parameter_correlations(parameter_values, npv_values)
        param_importance = self._rank_parameter_importance(param_correlations)
        
        runtime = time.time() - start_time
        
        return MonteCarloResults(
            npv_distribution=npv_values,
            roi_distribution=roi_values,
            breakeven_distribution=breakeven_values,
            total_value_distribution=value_values,
            total_cost_distribution=cost_values,
            npv_stats=npv_stats,
            roi_stats=roi_stats,
            breakeven_stats=breakeven_stats,
            value_stats=value_stats,
            cost_stats=cost_stats,
            probability_positive_npv=prob_positive_npv,
            probability_breakeven_within_24_months=prob_breakeven_24,
            probability_roi_above_target=prob_roi_target,
            parameter_correlations=param_correlations,
            parameter_importance=param_importance,
            iterations=self.iterations,
            convergence_achieved=convergence_achieved,
            runtime_seconds=runtime,
            random_seed=self.random_seed
        )
    
    def _run_single_iteration(self, base_config: Dict[str, Any], 
                            sampled_params: Dict[str, float], 
                            iteration_num: int) -> Dict[str, Any]:
        """Run a single iteration with sampled parameters"""
        # Create modified configuration with sampled parameters
        modified_config = self._apply_sampled_parameters(base_config, sampled_params)
        
        # Run the model
        try:
            results = self.model_runner(modified_config)
            return results
        except Exception as e:
            raise CalculationError(
                f"Monte Carlo iteration {iteration_num} failed: {e}",
                "monte_carlo_iteration"
            )
    
    def _run_parallel_simulations(self, base_config: Dict[str, Any],
                                 parameter_samples: Dict[str, np.ndarray]) -> Tuple[np.ndarray, ...]:
        """Run simulations in parallel"""
        npv_values = np.zeros(self.iterations)
        roi_values = np.zeros(self.iterations)
        breakeven_values = np.zeros(self.iterations)
        value_values = np.zeros(self.iterations)
        cost_values = np.zeros(self.iterations)
        
        with ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
            # Submit all tasks
            futures = {}
            for i in range(self.iterations):
                params = {k: v[i] for k, v in parameter_samples.items()}
                future = executor.submit(self._run_single_iteration, base_config, params, i)
                futures[future] = i
            
            # Collect results as they complete
            for future in as_completed(futures):
                i = futures[future]
                try:
                    results = future.result()
                    npv_values[i] = results['npv']
                    roi_values[i] = results['roi_percent']
                    breakeven_values[i] = results['breakeven_month']
                    value_values[i] = results['total_value_3y']
                    cost_values[i] = results['total_cost_3y']
                except Exception as e:
                    raise CalculationError(f"Parallel execution failed at iteration {i}: {e}", "parallel_monte_carlo")
        
        return npv_values, roi_values, breakeven_values, value_values, cost_values
    
    def _apply_sampled_parameters(self, base_config: Dict[str, Any], 
                                 sampled_params: Dict[str, float]) -> Dict[str, Any]:
        """
        Apply sampled parameters to base configuration.
        Assumes base_config has clean, simple values (not dicts with 'value' keys).
        """
        import copy
        modified_config = copy.deepcopy(base_config)
        
        # Map sampled parameters to configuration structure
        for param_name, value in sampled_params.items():
            # Parse parameter path (e.g., "impact.feature_cycle_reduction")
            path_parts = param_name.split('.')
            
            # Navigate to the correct location in config
            current = modified_config
            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value directly (config should have clean values)
            final_key = path_parts[-1]
            current[final_key] = value
        
        return modified_config
    
    def _check_convergence(self, values: np.ndarray) -> bool:
        """Check if simulation has converged using proper Monte Carlo standard error"""
        if len(values) < 100:
            return False
        
        # Method 1: Monte Carlo Standard Error
        n = len(values)
        mean = np.mean(values)
        std = np.std(values, ddof=1)
        
        # Monte Carlo standard error: σ/√n
        mc_std_error = std / np.sqrt(n)
        
        # Check relative error
        if mean != 0:
            relative_error = mc_std_error / abs(mean)
        else:
            # For zero mean, use absolute error
            relative_error = mc_std_error
        
        # Method 2: Batch Means for additional validation
        # Split into batches to check variance between batch means
        batch_size = min(100, n // 10)
        if batch_size >= 10:  # Need reasonable batch size
            n_batches = n // batch_size
            batches = values[:n_batches * batch_size].reshape(n_batches, batch_size)
            batch_means = np.mean(batches, axis=1)
            
            # Check if batch means are stable
            batch_mean_std = np.std(batch_means, ddof=1)
            overall_mean = np.mean(batch_means)
            
            if overall_mean != 0:
                batch_relative_error = batch_mean_std / abs(overall_mean)
                # Use the more conservative estimate
                relative_error = max(relative_error, batch_relative_error)
        
        return relative_error < self.convergence_threshold
    
    def _calculate_statistics(self, values: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive statistics for a distribution"""
        return {
            'mean': np.mean(values),
            'median': np.median(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'p5': np.percentile(values, 5),
            'p10': np.percentile(values, 10),
            'p25': np.percentile(values, 25),
            'p50': np.percentile(values, 50),
            'p75': np.percentile(values, 75),
            'p90': np.percentile(values, 90),
            'p95': np.percentile(values, 95),
            'skewness': self._calculate_skewness(values),
            'kurtosis': self._calculate_kurtosis(values)
        }
    
    def _calculate_skewness(self, values: np.ndarray) -> float:
        """Calculate skewness of distribution"""
        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            return 0
        return np.mean(((values - mean) / std) ** 3)
    
    def _calculate_kurtosis(self, values: np.ndarray) -> float:
        """Calculate kurtosis of distribution"""
        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            return 0
        return np.mean(((values - mean) / std) ** 4) - 3
    
    def _calculate_parameter_correlations(self, parameter_values: Dict[str, np.ndarray], 
                                        target_values: np.ndarray) -> Dict[str, float]:
        """Calculate correlation between each parameter and the target metric"""
        correlations = {}
        
        for param_name, param_values in parameter_values.items():
            if np.std(param_values) > 0:  # Only calculate if parameter varies
                correlation = np.corrcoef(param_values, target_values)[0, 1]
                correlations[param_name] = correlation
        
        return correlations
    
    def _rank_parameter_importance(self, correlations: Dict[str, float]) -> List[Tuple[str, float]]:
        """Rank parameters by their importance (absolute correlation)"""
        importance = [(param, abs(corr)) for param, corr in correlations.items()]
        importance.sort(key=lambda x: x[1], reverse=True)
        return importance


def auto_generate_distribution(param_name: str, value: float, section: str = "") -> Distribution:
    """
    Auto-generate an appropriate distribution based on parameter name and value.
    
    Args:
        param_name: Name of the parameter
        value: Central value for the distribution
        section: Section name (baseline, adoption, impact, costs) for context
        
    Returns:
        An appropriate Distribution object
    """
    # Normalize parameter name for matching
    param_lower = param_name.lower()
    
    # Percentages/rates (0-1 range)
    if any(term in param_lower for term in ['rate', 'percentage', 'ratio', 'efficiency', 'multiplier']):
        # Use Beta distribution for bounded percentages
        if 0 <= value <= 1:
            # Shape parameters to give reasonable variance around the value
            if value <= 0.1:  # Low percentages - allow more upward variance
                alpha = 2
                beta = 18
            elif value >= 0.9:  # High percentages - allow more downward variance  
                alpha = 18
                beta = 2
            else:  # Middle range - symmetric variance
                mean_target = value
                variance_target = 0.01  # Modest variance
                alpha = mean_target * ((mean_target * (1 - mean_target) / variance_target) - 1)
                beta = (1 - mean_target) * ((mean_target * (1 - mean_target) / variance_target) - 1)
                alpha = max(1, min(alpha, 20))  # Keep reasonable bounds
                beta = max(1, min(beta, 20))
            
            min_val = max(0, value - 0.2)
            max_val = min(1, value + 0.2)
            return Beta(alpha=alpha, beta=beta, min_val=min_val, max_val=max_val)
        else:
            # For multipliers > 1, use triangular
            return Triangular(
                min_val=value * 0.8,
                mode=value,
                max_val=value * 1.3
            )
    
    # Time-based parameters (days, hours, months)
    elif any(term in param_lower for term in ['days', 'hours', 'time', 'cycle', 'month', 'week']):
        # Triangular with asymmetric bounds (delays more likely than speedups)
        return Triangular(
            min_val=value * 0.75,
            mode=value,
            max_val=value * 1.5
        )
    
    # Count-based parameters (team size, incidents)
    elif any(term in param_lower for term in ['size', 'count', 'number', 'incidents']):
        if value >= 20:  # Larger counts - use uniform
            return Uniform(min_val=value * 0.7, max_val=value * 1.3)
        else:  # Smaller counts - use triangular for more control
            return Triangular(
                min_val=max(1, value * 0.5),
                mode=value,
                max_val=value * 1.5
            )
    
    # Cost/financial parameters
    elif any(term in param_lower for term in ['cost', 'price', 'budget', 'spend']) or section == 'costs':
        # LogNormal for costs (can't be negative, long tail for overruns)
        std_log = 0.2  # 20% coefficient of variation
        mean_log = np.log(value)
        return LogNormal(mean_log=mean_log, std_log=std_log, min_val=value * 0.5, max_val=value * 2.0)
    
    # Quality metrics
    elif any(term in param_lower for term in ['defect', 'quality', 'error']):
        # Normal distribution with bounds
        return Normal(mean=value, std=value * 0.2, min_val=max(0, value * 0.5), max_val=value * 1.5)
    
    # Default: Triangular with ±20% bounds
    else:
        return Triangular(
            min_val=value * 0.8,
            mode=value,
            max_val=value * 1.2
        )


def create_parameter_distributions_from_scenario(scenario_config: Dict[str, Any],
                                                auto_generate: bool = False) -> ParameterDistributions:
    """
    Create parameter distributions from scenario configuration.
    
    If a parameter has a distribution definition, use it.
    If auto_generate=True, create appropriate distributions for values without them.
    Otherwise, create a deterministic distribution from the point value.
    """
    distributions = ParameterDistributions()
    
    # Process each section of the configuration
    for section_name, section_config in scenario_config.items():
        if isinstance(section_config, dict):
            for param_name, param_value in section_config.items():
                full_param_name = f"{section_name}.{param_name}"
                
                if isinstance(param_value, dict) and 'distribution' in param_value:
                    # Parameter has distribution definition - use it
                    dist_config = param_value['distribution']
                    distribution = create_distribution_from_config(dist_config)
                elif isinstance(param_value, dict) and 'value' in param_value:
                    # Parameter has a value field but no distribution
                    value = float(param_value['value'])
                    if auto_generate:
                        distribution = auto_generate_distribution(param_name, value, section_name)
                    else:
                        distribution = Deterministic(value=value)
                else:
                    # Raw value (number or string)
                    if isinstance(param_value, (int, float)):
                        value = float(param_value)
                        if auto_generate:
                            distribution = auto_generate_distribution(param_name, value, section_name)
                        else:
                            distribution = Deterministic(value=value)
                    else:
                        continue  # Skip non-numeric parameters (e.g., 'scenario' references)
                
                distributions.add_distribution(full_param_name, distribution)
    
    # Add correlations if defined
    if 'correlations' in scenario_config:
        for corr_def in scenario_config['correlations']:
            param1 = corr_def['param1']
            param2 = corr_def['param2']
            correlation = corr_def['correlation']
            distributions.add_correlation(param1, param2, correlation)
    
    return distributions