"""
Parameter distribution framework for Monte Carlo simulations.
Provides various probability distributions for modeling uncertainty in business parameters.
"""

from dataclasses import dataclass
from typing import Union, Optional, Dict, Any, List, Tuple
import numpy as np
from scipy import stats
from abc import ABC, abstractmethod
from ..utils.exceptions import ValidationError


class Distribution(ABC):
    """Base class for all probability distributions"""
    
    @abstractmethod
    def sample(self, size: int = 1, random_state: Optional[np.random.RandomState] = None) -> np.ndarray:
        """Generate random samples from the distribution"""
        pass
    
    @abstractmethod
    def mean(self) -> float:
        """Return the expected value of the distribution"""
        pass
    
    @abstractmethod
    def std(self) -> float:
        """Return the standard deviation of the distribution"""
        pass
    
    @abstractmethod
    def percentile(self, q: float) -> float:
        """Return the q-th percentile of the distribution"""
        pass
    
    def confidence_interval(self, confidence: float = 0.95) -> Tuple[float, float]:
        """Return the confidence interval for the distribution"""
        alpha = 1 - confidence
        lower = self.percentile(alpha / 2)
        upper = self.percentile(1 - alpha / 2)
        return (lower, upper)


@dataclass
class Normal(Distribution):
    """Normal (Gaussian) distribution"""
    mean_val: float
    std_val: float
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    
    def __post_init__(self):
        if self.std_val <= 0:
            raise ValidationError("std_val", self.std_val, "positive number", "Standard deviation must be greater than 0")
    
    def sample(self, size: int = 1, random_state: Optional[np.random.RandomState] = None) -> np.ndarray:
        if random_state is None:
            random_state = np.random.RandomState()
        
        samples = random_state.normal(self.mean_val, self.std_val, size)
        
        # Apply bounds if specified
        if self.min_val is not None:
            samples = np.maximum(samples, self.min_val)
        if self.max_val is not None:
            samples = np.minimum(samples, self.max_val)
        
        return samples
    
    def mean(self) -> float:
        return self.mean_val
    
    def std(self) -> float:
        return self.std_val
    
    def percentile(self, q: float) -> float:
        value = stats.norm.ppf(q, loc=self.mean_val, scale=self.std_val)
        if self.min_val is not None:
            value = max(value, self.min_val)
        if self.max_val is not None:
            value = min(value, self.max_val)
        return value


@dataclass
class Triangular(Distribution):
    """Triangular distribution - useful when min, max, and most likely values are known"""
    min_val: float
    mode_val: float  # Most likely value
    max_val: float
    
    def __post_init__(self):
        if not (self.min_val <= self.mode_val <= self.max_val):
            raise ValidationError(
                "triangular_parameters", 
                f"min={self.min_val}, mode={self.mode_val}, max={self.max_val}",
                "min <= mode <= max",
                f"Ensure {self.min_val} <= {self.mode_val} <= {self.max_val}"
            )
    
    def sample(self, size: int = 1, random_state: Optional[np.random.RandomState] = None) -> np.ndarray:
        if random_state is None:
            random_state = np.random.RandomState()
        
        return random_state.triangular(self.min_val, self.mode_val, self.max_val, size)
    
    def mean(self) -> float:
        return (self.min_val + self.mode_val + self.max_val) / 3
    
    def std(self) -> float:
        a, m, b = self.min_val, self.mode_val, self.max_val
        variance = (a**2 + m**2 + b**2 - a*m - a*b - m*b) / 18
        return np.sqrt(variance)
    
    def percentile(self, q: float) -> float:
        return stats.triang.ppf(
            q, 
            c=(self.mode_val - self.min_val) / (self.max_val - self.min_val),
            loc=self.min_val,
            scale=self.max_val - self.min_val
        )


@dataclass
class Beta(Distribution):
    """Beta distribution - useful for modeling rates and percentages"""
    alpha: float
    beta_param: float
    min_val: float = 0.0
    max_val: float = 1.0
    
    def __post_init__(self):
        if self.alpha <= 0 or self.beta_param <= 0:
            raise ValidationError("beta_parameters", f"alpha={self.alpha}, beta={self.beta_param}", 
                                "positive numbers", "Both alpha and beta must be > 0")
        if self.min_val >= self.max_val:
            raise ValidationError("beta_bounds", f"min={self.min_val}, max={self.max_val}",
                                "min < max", "Minimum value must be less than maximum")
    
    def sample(self, size: int = 1, random_state: Optional[np.random.RandomState] = None) -> np.ndarray:
        if random_state is None:
            random_state = np.random.RandomState()
        
        # Sample from standard beta [0,1]
        samples = random_state.beta(self.alpha, self.beta_param, size)
        
        # Scale to [min_val, max_val]
        return self.min_val + samples * (self.max_val - self.min_val)
    
    def mean(self) -> float:
        standard_mean = self.alpha / (self.alpha + self.beta_param)
        return self.min_val + standard_mean * (self.max_val - self.min_val)
    
    def std(self) -> float:
        a, b = self.alpha, self.beta_param
        standard_var = (a * b) / ((a + b)**2 * (a + b + 1))
        scaled_var = standard_var * (self.max_val - self.min_val)**2
        return np.sqrt(scaled_var)
    
    def percentile(self, q: float) -> float:
        standard_percentile = stats.beta.ppf(q, self.alpha, self.beta_param)
        return self.min_val + standard_percentile * (self.max_val - self.min_val)


@dataclass
class Uniform(Distribution):
    """Uniform distribution - all values equally likely within range"""
    min_val: float
    max_val: float
    
    def __post_init__(self):
        if self.min_val >= self.max_val:
            raise ValidationError("uniform_bounds", f"min={self.min_val}, max={self.max_val}",
                                "min < max", "Minimum value must be less than maximum")
    
    def sample(self, size: int = 1, random_state: Optional[np.random.RandomState] = None) -> np.ndarray:
        if random_state is None:
            random_state = np.random.RandomState()
        
        return random_state.uniform(self.min_val, self.max_val, size)
    
    def mean(self) -> float:
        return (self.min_val + self.max_val) / 2
    
    def std(self) -> float:
        return (self.max_val - self.min_val) / np.sqrt(12)
    
    def percentile(self, q: float) -> float:
        return self.min_val + q * (self.max_val - self.min_val)


@dataclass
class LogNormal(Distribution):
    """Log-normal distribution - useful for modeling costs and durations"""
    mean_log: float
    std_log: float
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    
    def __post_init__(self):
        if self.std_log <= 0:
            raise ValidationError("std_log", self.std_log, "positive number", 
                                "Log-normal standard deviation must be > 0")
    
    def sample(self, size: int = 1, random_state: Optional[np.random.RandomState] = None) -> np.ndarray:
        if random_state is None:
            random_state = np.random.RandomState()
        
        samples = random_state.lognormal(self.mean_log, self.std_log, size)
        
        # Apply bounds if specified
        if self.min_val is not None:
            samples = np.maximum(samples, self.min_val)
        if self.max_val is not None:
            samples = np.minimum(samples, self.max_val)
        
        return samples
    
    def mean(self) -> float:
        return np.exp(self.mean_log + self.std_log**2 / 2)
    
    def std(self) -> float:
        mean = self.mean()
        variance = (np.exp(self.std_log**2) - 1) * np.exp(2 * self.mean_log + self.std_log**2)
        return np.sqrt(variance)
    
    def percentile(self, q: float) -> float:
        value = stats.lognorm.ppf(q, s=self.std_log, scale=np.exp(self.mean_log))
        if self.min_val is not None:
            value = max(value, self.min_val)
        if self.max_val is not None:
            value = min(value, self.max_val)
        return value


@dataclass
class Deterministic(Distribution):
    """Deterministic 'distribution' - always returns the same value"""
    value: float
    
    def sample(self, size: int = 1, random_state: Optional[np.random.RandomState] = None) -> np.ndarray:
        return np.full(size, self.value)
    
    def mean(self) -> float:
        return self.value
    
    def std(self) -> float:
        return 0.0
    
    def percentile(self, q: float) -> float:
        return self.value


class ParameterDistributions:
    """Container for managing parameter distributions in a model"""
    
    def __init__(self):
        self.distributions: Dict[str, Distribution] = {}
        self.correlations: Dict[Tuple[str, str], float] = {}
    
    def add_distribution(self, param_name: str, distribution: Distribution):
        """Add a distribution for a parameter"""
        self.distributions[param_name] = distribution
    
    def add_correlation(self, param1: str, param2: str, correlation: float):
        """Add correlation between two parameters"""
        if not -1 <= correlation <= 1:
            raise ValidationError("correlation", correlation, "value between -1 and 1",
                                f"Correlation coefficient must be in range [-1, 1], got {correlation}")
        
        # Store both directions for easy lookup
        self.correlations[(param1, param2)] = correlation
        self.correlations[(param2, param1)] = correlation
    
    def sample_all(self, size: int = 1, random_state: Optional[np.random.RandomState] = None) -> Dict[str, np.ndarray]:
        """Sample from all distributions, respecting correlations"""
        if random_state is None:
            random_state = np.random.RandomState()
        
        samples = {}
        
        # Handle uncorrelated parameters first
        uncorrelated = set(self.distributions.keys())
        for (p1, p2) in self.correlations.keys():
            if p1 in uncorrelated:
                uncorrelated.discard(p1)
            if p2 in uncorrelated:
                uncorrelated.discard(p2)
        
        for param in uncorrelated:
            samples[param] = self.distributions[param].sample(size, random_state)
        
        # Handle correlated parameters using copulas (simplified approach)
        # For now, we'll use a simple approach with normal copulas
        correlated_groups = self._find_correlation_groups()
        
        for group in correlated_groups:
            if len(group) == 2:
                # Simple case: two correlated parameters
                p1, p2 = group
                corr = self.correlations.get((p1, p2), 0)
                
                # Generate correlated normal samples
                mean = [0, 0]
                cov = [[1, corr], [corr, 1]]
                normal_samples = random_state.multivariate_normal(mean, cov, size)
                
                # Transform to uniform [0,1] using normal CDF
                uniform_samples = stats.norm.cdf(normal_samples)
                
                # Transform to target distributions using inverse CDF
                samples[p1] = np.array([
                    self.distributions[p1].percentile(u) for u in uniform_samples[:, 0]
                ])
                samples[p2] = np.array([
                    self.distributions[p2].percentile(u) for u in uniform_samples[:, 1]
                ])
            else:
                # Complex case: multiple correlated parameters
                # For simplicity, sample independently (correlation handling could be enhanced)
                for param in group:
                    if param not in samples:
                        samples[param] = self.distributions[param].sample(size, random_state)
        
        return samples
    
    def _find_correlation_groups(self) -> List[List[str]]:
        """Find groups of correlated parameters"""
        groups = []
        processed = set()
        
        for param in self.distributions.keys():
            if param in processed:
                continue
            
            # Find all parameters correlated with this one
            group = [param]
            for (p1, p2), _ in self.correlations.items():
                if p1 == param and p2 not in group:
                    group.append(p2)
                elif p2 == param and p1 not in group:
                    group.append(p1)
            
            if len(group) > 1:
                groups.append(group)
                processed.update(group)
        
        return groups


def create_distribution_from_config(config: Dict[str, Any]) -> Distribution:
    """Factory function to create distribution from configuration dictionary"""
    dist_type = config.get('type', 'deterministic')
    
    if dist_type == 'normal':
        return Normal(
            mean_val=config['mean'],
            std_val=config['std'],
            min_val=config.get('min'),
            max_val=config.get('max')
        )
    elif dist_type == 'triangular':
        return Triangular(
            min_val=config['min'],
            mode_val=config['mode'],
            max_val=config['max']
        )
    elif dist_type == 'beta':
        return Beta(
            alpha=config['alpha'],
            beta_param=config['beta'],
            min_val=config.get('min', 0.0),
            max_val=config.get('max', 1.0)
        )
    elif dist_type == 'uniform':
        return Uniform(
            min_val=config['min'],
            max_val=config['max']
        )
    elif dist_type == 'lognormal':
        return LogNormal(
            mean_log=config['mean_log'],
            std_log=config['std_log'],
            min_val=config.get('min'),
            max_val=config.get('max')
        )
    elif dist_type == 'deterministic':
        return Deterministic(value=config.get('value', config.get('default', 0)))
    else:
        raise ValidationError("distribution_type", dist_type, 
                            "one of: normal, triangular, beta, uniform, lognormal, deterministic",
                            f"Unknown distribution type: {dist_type}")