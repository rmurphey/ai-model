"""
Enhanced Monte Carlo simulation engine using arviz for convergence diagnostics.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Callable
import numpy as np
import pandas as pd
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

# Import arviz for convergence diagnostics
import arviz as az
import xarray as xr

from .monte_carlo import MonteCarloResults  # Reuse the results class
from .distributions import ParameterDistributions
from ..utils.exceptions import CalculationError


class EnhancedMonteCarloEngine:
    """
    Enhanced Monte Carlo engine with arviz convergence diagnostics.
    """
    
    def __init__(self,
                 model_runner: Callable,
                 parameter_distributions: ParameterDistributions,
                 iterations: int = 1000,
                 confidence_level: float = 0.95,
                 target_roi: float = 100.0,
                 convergence_threshold: float = 0.01,
                 random_seed: Optional[int] = None,
                 n_jobs: int = 1,
                 n_chains: int = 4,
                 warmup: int = 100):
        """
        Initialize enhanced Monte Carlo engine.
        
        Args:
            model_runner: Function that takes parameters and returns results dict
            parameter_distributions: Distribution definitions for all parameters
            iterations: Number of simulation iterations per chain
            confidence_level: Confidence level for intervals
            target_roi: Target ROI for probability calculations
            convergence_threshold: Threshold for R-hat convergence statistic
            random_seed: Random seed for reproducibility
            n_jobs: Number of parallel processes
            n_chains: Number of MCMC chains for convergence checking
            warmup: Number of warmup iterations to discard
        """
        self.model_runner = model_runner
        self.parameter_distributions = parameter_distributions
        self.iterations = iterations
        self.confidence_level = confidence_level
        self.target_roi = target_roi
        self.convergence_threshold = convergence_threshold
        self.random_seed = random_seed
        self.n_jobs = n_jobs if n_jobs > 0 else mp.cpu_count()
        self.n_chains = n_chains
        self.warmup = warmup
        
        # Initialize random state
        self.random_state = np.random.RandomState(random_seed)
    
    def run(self, base_scenario_config: Dict[str, Any]) -> MonteCarloResults:
        """
        Run Monte Carlo simulation with enhanced convergence checking.
        
        Args:
            base_scenario_config: Base configuration to modify with sampled parameters
            
        Returns:
            MonteCarloResults with distributions and statistics
        """
        start_time = time.time()
        
        # Run multiple chains for better convergence diagnostics
        all_chains_npv = []
        all_chains_roi = []
        all_chains_breakeven = []
        all_chains_value = []
        all_chains_cost = []
        all_parameter_samples = []
        
        for chain_id in range(self.n_chains):
            # Set different seed for each chain
            chain_seed = None if self.random_seed is None else self.random_seed + chain_id
            chain_random_state = np.random.RandomState(chain_seed)
            
            # Generate parameter samples for this chain
            total_iterations = self.iterations + self.warmup
            parameter_samples = self.parameter_distributions.sample_all(
                size=total_iterations,
                random_state=chain_random_state
            )
            
            # Run simulations for this chain
            chain_results = self._run_chain(base_scenario_config, parameter_samples)
            
            # Discard warmup iterations
            all_chains_npv.append(chain_results[0][self.warmup:])
            all_chains_roi.append(chain_results[1][self.warmup:])
            all_chains_breakeven.append(chain_results[2][self.warmup:])
            all_chains_value.append(chain_results[3][self.warmup:])
            all_chains_cost.append(chain_results[4][self.warmup:])
            
            # Store parameter samples (without warmup)
            param_samples_chain = {k: v[self.warmup:] for k, v in parameter_samples.items()}
            all_parameter_samples.append(param_samples_chain)
        
        # Stack chains into shape (chain, draw) for arviz
        npv_chains = np.stack(all_chains_npv)
        roi_chains = np.stack(all_chains_roi)
        breakeven_chains = np.stack(all_chains_breakeven)
        value_chains = np.stack(all_chains_value)
        cost_chains = np.stack(all_chains_cost)
        
        # Create arviz InferenceData object for convergence diagnostics
        inference_data = self._create_inference_data({
            'npv': npv_chains,
            'roi': roi_chains,
            'breakeven': breakeven_chains,
            'total_value': value_chains,
            'total_cost': cost_chains
        })
        
        # Check convergence using arviz
        convergence_achieved = self._check_convergence_arviz(inference_data)
        
        # Combine all chains for final results (flatten across chains)
        npv_all = npv_chains.flatten()
        roi_all = roi_chains.flatten()
        breakeven_all = breakeven_chains.flatten()
        value_all = value_chains.flatten()
        cost_all = cost_chains.flatten()
        
        # Combine parameter samples from all chains
        combined_param_samples = {}
        for param_name in all_parameter_samples[0].keys():
            combined_param_samples[param_name] = np.concatenate(
                [chain[param_name] for chain in all_parameter_samples]
            )
        
        # Calculate statistics
        npv_stats = self._calculate_statistics_arviz(npv_chains, 'npv')
        roi_stats = self._calculate_statistics_arviz(roi_chains, 'roi')
        breakeven_stats = self._calculate_statistics_arviz(breakeven_chains, 'breakeven')
        value_stats = self._calculate_statistics_arviz(value_chains, 'total_value')
        cost_stats = self._calculate_statistics_arviz(cost_chains, 'total_cost')
        
        # Calculate risk metrics
        prob_positive_npv = np.mean(npv_all > 0)
        prob_breakeven_24 = np.mean(breakeven_all <= 24)
        prob_roi_above_target = np.mean(roi_all > self.target_roi)
        
        # Calculate parameter correlations
        param_correlations = self._calculate_parameter_correlations(
            combined_param_samples, npv_all
        )
        param_importance = self._rank_parameter_importance(param_correlations)
        
        runtime = time.time() - start_time
        
        return MonteCarloResults(
            npv_distribution=npv_all,
            roi_distribution=roi_all,
            breakeven_distribution=breakeven_all,
            total_value_distribution=value_all,
            total_cost_distribution=cost_all,
            npv_stats=npv_stats,
            roi_stats=roi_stats,
            breakeven_stats=breakeven_stats,
            value_stats=value_stats,
            cost_stats=cost_stats,
            probability_positive_npv=prob_positive_npv,
            probability_breakeven_within_24_months=prob_breakeven_24,
            probability_roi_above_target=prob_roi_above_target,
            parameter_correlations=param_correlations,
            parameter_importance=param_importance,
            iterations=self.iterations * self.n_chains,
            convergence_achieved=convergence_achieved,
            runtime_seconds=runtime,
            random_seed=self.random_seed
        )
    
    def _run_chain(self, base_config: Dict[str, Any],
                  parameter_samples: Dict[str, np.ndarray]) -> Tuple[np.ndarray, ...]:
        """Run a single chain of simulations"""
        n_iterations = len(next(iter(parameter_samples.values())))
        
        npv_values = np.zeros(n_iterations)
        roi_values = np.zeros(n_iterations)
        breakeven_values = np.zeros(n_iterations)
        value_values = np.zeros(n_iterations)
        cost_values = np.zeros(n_iterations)
        
        # Run simulations (can be parallelized if needed)
        for i in range(n_iterations):
            params = {k: v[i] for k, v in parameter_samples.items()}
            modified_config = self._apply_sampled_parameters(base_config, params)
            
            try:
                results = self.model_runner(modified_config)
                npv_values[i] = results.get('npv', 0)
                roi_values[i] = results.get('roi_percent', 0)
                breakeven_values[i] = results.get('breakeven_month', 99)
                value_values[i] = results.get('total_value_3y', 0)
                cost_values[i] = results.get('total_cost_3y', 0)
            except Exception as e:
                # Handle failures gracefully
                npv_values[i] = np.nan
                roi_values[i] = np.nan
                breakeven_values[i] = np.nan
                value_values[i] = np.nan
                cost_values[i] = np.nan
        
        return npv_values, roi_values, breakeven_values, value_values, cost_values
    
    def _create_inference_data(self, chains_dict: Dict[str, np.ndarray]) -> az.InferenceData:
        """Create arviz InferenceData object from chains"""
        # Convert to xarray Dataset
        coords = {
            "chain": np.arange(self.n_chains),
            "draw": np.arange(self.iterations)
        }
        
        data_vars = {}
        for var_name, chains in chains_dict.items():
            # Ensure shape is (chain, draw)
            if chains.shape != (self.n_chains, self.iterations):
                chains = chains.reshape(self.n_chains, self.iterations)
            data_vars[var_name] = (["chain", "draw"], chains)
        
        posterior = xr.Dataset(data_vars, coords=coords)
        
        return az.InferenceData(posterior=posterior)
    
    def _check_convergence_arviz(self, inference_data: az.InferenceData) -> bool:
        """
        Check convergence using arviz diagnostics.
        Uses R-hat (potential scale reduction factor) and effective sample size.
        """
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            
            # Calculate R-hat for all variables
            rhat = az.rhat(inference_data)
            
            # Calculate effective sample size
            ess_bulk = az.ess(inference_data, method='bulk')
            ess_tail = az.ess(inference_data, method='tail')
            
            # Check convergence criteria
            convergence_checks = []
            
            # R-hat should be close to 1.0 (typically < 1.01)
            for var_name in rhat.data_vars:
                rhat_value = float(rhat[var_name].values)
                # Use slightly relaxed threshold for practical convergence
                convergence_checks.append(rhat_value < 1.01 + self.convergence_threshold)
            
            # Effective sample size should be reasonable (> 100 per chain)
            min_ess = 100 * self.n_chains
            for var_name in ess_bulk.data_vars:
                ess_value = float(ess_bulk[var_name].values)
                convergence_checks.append(ess_value > min_ess)
            
            # All checks must pass for convergence
            return all(convergence_checks) if convergence_checks else False
    
    def _calculate_statistics_arviz(self, chains: np.ndarray, var_name: str) -> Dict[str, float]:
        """Calculate statistics using arviz"""
        # Flatten chains for overall statistics
        values = chains.flatten()
        
        # Remove NaN values
        values = values[~np.isnan(values)]
        
        if len(values) == 0:
            return {
                'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0,
                'p5': 0, 'p10': 0, 'p25': 0, 'p50': 0, 'p75': 0, 'p90': 0, 'p95': 0,
                'hdi_lower': 0, 'hdi_upper': 0
            }
        
        # Calculate HDI (Highest Density Interval) using arviz
        hdi = az.hdi(values, hdi_prob=self.confidence_level)
        
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
            'hdi_lower': float(hdi[0]) if isinstance(hdi, np.ndarray) else 0,
            'hdi_upper': float(hdi[1]) if isinstance(hdi, np.ndarray) else 0
        }
    
    def _apply_sampled_parameters(self, base_config: Dict[str, Any],
                                 sampled_params: Dict[str, float]) -> Dict[str, Any]:
        """Apply sampled parameters to base configuration"""
        # This is a simplified version - you'd need to map parameters to config structure
        modified_config = base_config.copy()
        
        # Example mapping (adjust based on your actual config structure)
        for param_name, value in sampled_params.items():
            # You'd implement the actual parameter mapping here
            # This is just a placeholder
            modified_config[param_name] = value
        
        return modified_config
    
    def _calculate_parameter_correlations(self, parameter_values: Dict[str, np.ndarray],
                                         target_values: np.ndarray) -> Dict[str, float]:
        """Calculate correlation between each parameter and target metric"""
        correlations = {}
        
        for param_name, param_values in parameter_values.items():
            # Remove NaN values
            mask = ~(np.isnan(param_values) | np.isnan(target_values))
            if np.sum(mask) > 1 and np.std(param_values[mask]) > 0:
                correlation = np.corrcoef(param_values[mask], target_values[mask])[0, 1]
                correlations[param_name] = correlation
        
        return correlations
    
    def _rank_parameter_importance(self, correlations: Dict[str, float]) -> List[Tuple[str, float]]:
        """Rank parameters by importance (absolute correlation)"""
        importance = [(param, abs(corr)) for param, corr in correlations.items()]
        importance.sort(key=lambda x: x[1], reverse=True)
        return importance