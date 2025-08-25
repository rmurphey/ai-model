"""
Enhanced parameter distributions using copulas for correlation handling.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union, Any
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
import warnings
from scipy import stats
from copulas.multivariate import GaussianMultivariate
from copulas.univariate import GaussianKDE, Univariate

# Import existing distribution classes
from .distributions import (
    Distribution, Normal, Triangular, Beta, Uniform, 
    LogNormal, Deterministic, create_distribution_from_config
)


class EnhancedParameterDistributions:
    """
    Enhanced container for managing parameter distributions with copula-based correlation.
    Uses the copulas library for robust correlation handling.
    """
    
    def __init__(self):
        self.distributions: Dict[str, Distribution] = {}
        self.correlations: Dict[Tuple[str, str], float] = {}
        self._copula = None
        self._copula_fitted = False
        
    def add_distribution(self, name: str, distribution: Distribution):
        """Add a parameter distribution"""
        self.distributions[name] = distribution
        self._copula_fitted = False  # Reset copula when distributions change
        
    def add_correlation(self, param1: str, param2: str, correlation: float):
        """Add correlation between two parameters"""
        if param1 not in self.distributions or param2 not in self.distributions:
            raise ValueError(f"Both parameters must have distributions defined")
        
        if not -1 <= correlation <= 1:
            raise ValueError(f"Correlation must be between -1 and 1, got {correlation}")
        
        # Store both directions for easy lookup
        self.correlations[(param1, param2)] = correlation
        self.correlations[(param2, param1)] = correlation
        self._copula_fitted = False  # Reset copula when correlations change
    
    def _prepare_copula_data(self, n_samples: int = 10000, 
                            random_state: Optional[np.random.RandomState] = None) -> pd.DataFrame:
        """
        Prepare synthetic data that matches our distributions and correlations.
        This data will be used to fit the copula.
        """
        if random_state is None:
            random_state = np.random.RandomState()
        
        # First, identify correlated groups
        correlated_params = set()
        for (p1, p2) in self.correlations.keys():
            if p1 != p2:  # Avoid duplicates
                correlated_params.add(p1)
                correlated_params.add(p2)
        
        # Generate samples that respect correlations
        data = {}
        
        # For uncorrelated parameters, sample independently
        for param_name, dist in self.distributions.items():
            if param_name not in correlated_params:
                data[param_name] = dist.sample(n_samples, random_state)
        
        # For correlated parameters, we need to generate correlated samples
        # Group parameters by their correlation clusters
        correlation_groups = self._find_correlation_groups()
        
        for group in correlation_groups:
            if len(group) == 1:
                # Single parameter, no correlation
                param = group[0]
                if param not in data:
                    data[param] = self.distributions[param].sample(n_samples, random_state)
            else:
                # Multiple correlated parameters
                # Build correlation matrix for this group
                n_params = len(group)
                corr_matrix = np.eye(n_params)
                
                for i, p1 in enumerate(group):
                    for j, p2 in enumerate(group):
                        if i < j:
                            corr_value = self.correlations.get((p1, p2), 0)
                            corr_matrix[i, j] = corr_value
                            corr_matrix[j, i] = corr_value
                
                # Generate correlated normal samples
                mean = np.zeros(n_params)
                normal_samples = random_state.multivariate_normal(mean, corr_matrix, n_samples)
                
                # Transform to uniform [0,1] using normal CDF
                uniform_samples = stats.norm.cdf(normal_samples)
                
                # Transform to target distributions
                for idx, param in enumerate(group):
                    # Get the target distribution
                    dist = self.distributions[param]
                    
                    # Transform uniform samples to match the distribution
                    # This uses the inverse CDF (percent point function)
                    if hasattr(dist, 'percentile'):
                        data[param] = np.array([dist.percentile(u) for u in uniform_samples[:, idx]])
                    else:
                        # Fallback: use the distribution's own sampling
                        # This won't preserve correlations perfectly
                        data[param] = dist.sample(n_samples, random_state)
        
        return pd.DataFrame(data)
    
    def _find_correlation_groups(self) -> List[List[str]]:
        """Find groups of parameters that are correlated with each other"""
        groups = []
        visited = set()
        
        for param in self.distributions.keys():
            if param in visited:
                continue
            
            # Find all parameters correlated with this one
            group = [param]
            to_check = [param]
            visited.add(param)
            
            while to_check:
                current = to_check.pop()
                for (p1, p2), corr in self.correlations.items():
                    if corr != 0:  # Only consider non-zero correlations
                        if p1 == current and p2 not in visited:
                            group.append(p2)
                            visited.add(p2)
                            to_check.append(p2)
                        elif p2 == current and p1 not in visited:
                            group.append(p1)
                            visited.add(p1)
                            to_check.append(p1)
            
            groups.append(group)
        
        return groups
    
    def _fit_copula(self, n_fit_samples: int = 10000,
                    random_state: Optional[np.random.RandomState] = None):
        """Fit the copula model to synthetic data"""
        if self._copula_fitted and self._copula is not None:
            return  # Already fitted
        
        # Prepare synthetic data that matches our distributions
        data = self._prepare_copula_data(n_fit_samples, random_state)
        
        # Create and fit Gaussian copula
        self._copula = GaussianMultivariate()
        
        # Suppress warnings from copulas library during fitting
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            warnings.filterwarnings('ignore', message='.*iteration is not making good progress.*')
            self._copula.fit(data)
        
        self._copula_fitted = True
    
    def sample_all(self, size: int = 1, 
                  random_state: Optional[np.random.RandomState] = None) -> Dict[str, np.ndarray]:
        """
        Sample from all distributions, respecting correlations using copulas.
        
        Args:
            size: Number of samples to generate
            random_state: Random state for reproducibility
            
        Returns:
            Dictionary mapping parameter names to sampled values
        """
        if random_state is None:
            random_state = np.random.RandomState()
        
        # If no correlations, sample independently
        if not self.correlations:
            samples = {}
            for param_name, dist in self.distributions.items():
                samples[param_name] = dist.sample(size, random_state)
            return samples
        
        # Fit copula if not already fitted
        self._fit_copula(random_state=random_state)
        
        # Generate samples using the copula
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            warnings.filterwarnings('ignore', message='.*iteration is not making good progress.*')
            
            # Set random state for copula sampling
            # Note: copulas library uses numpy's global random state
            if random_state is not None:
                np.random.seed(random_state.randint(0, 2**32 - 1))
            
            copula_samples = self._copula.sample(size)
        
        # Convert DataFrame to dictionary of arrays
        samples = {}
        for param_name in self.distributions.keys():
            if param_name in copula_samples.columns:
                samples[param_name] = copula_samples[param_name].values
            else:
                # Parameter not in copula (shouldn't happen, but safe fallback)
                samples[param_name] = self.distributions[param_name].sample(size, random_state)
        
        return samples
    
    def get_correlation_matrix(self) -> pd.DataFrame:
        """Get the correlation matrix as a DataFrame"""
        param_names = list(self.distributions.keys())
        n = len(param_names)
        
        # Build correlation matrix
        corr_matrix = np.eye(n)
        for i, p1 in enumerate(param_names):
            for j, p2 in enumerate(param_names):
                if i != j:
                    corr_matrix[i, j] = self.correlations.get((p1, p2), 0)
        
        return pd.DataFrame(corr_matrix, index=param_names, columns=param_names)


# Create a compatibility layer that mimics the old ParameterDistributions class
class ParameterDistributions(EnhancedParameterDistributions):
    """
    Backward-compatible wrapper around EnhancedParameterDistributions.
    Maintains the same API as the original ParameterDistributions class.
    """
    pass