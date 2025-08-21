#!/usr/bin/env python3
"""
Test suite for Monte Carlo simulation functionality.
Tests distributions, Monte Carlo engine, and integration with the model.
"""

import os
import sys
import unittest
import numpy as np
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model.distributions import (
    Normal, Triangular, Beta, Uniform, LogNormal, Deterministic,
    ParameterDistributions, create_distribution_from_config
)
from src.model.monte_carlo import MonteCarloEngine, MonteCarloResults, create_parameter_distributions_from_scenario
from src.utils.exceptions import ValidationError


class TestDistributions(unittest.TestCase):
    """Test probability distribution classes"""
    
    def test_normal_distribution(self):
        """Test normal distribution"""
        dist = Normal(mean_val=100, std_val=10)
        
        # Test properties
        self.assertEqual(dist.mean(), 100)
        self.assertEqual(dist.std(), 10)
        
        # Test sampling
        samples = dist.sample(1000, random_state=np.random.RandomState(42))
        self.assertEqual(len(samples), 1000)
        self.assertAlmostEqual(np.mean(samples), 100, delta=1)
        self.assertAlmostEqual(np.std(samples), 10, delta=1)
        
        # Test bounds
        dist_bounded = Normal(mean_val=100, std_val=10, min_val=90, max_val=110)
        samples_bounded = dist_bounded.sample(1000, random_state=np.random.RandomState(42))
        self.assertTrue(np.all(samples_bounded >= 90))
        self.assertTrue(np.all(samples_bounded <= 110))
    
    def test_triangular_distribution(self):
        """Test triangular distribution"""
        dist = Triangular(min_val=10, mode_val=20, max_val=40)
        
        # Test properties
        self.assertAlmostEqual(dist.mean(), 23.33, places=1)
        
        # Test sampling
        samples = dist.sample(1000, random_state=np.random.RandomState(42))
        self.assertEqual(len(samples), 1000)
        self.assertTrue(np.all(samples >= 10))
        self.assertTrue(np.all(samples <= 40))
        
        # Test validation
        with self.assertRaises(ValidationError):
            Triangular(min_val=30, mode_val=20, max_val=40)
    
    def test_beta_distribution(self):
        """Test beta distribution"""
        dist = Beta(alpha=2, beta_param=5)
        
        # Test properties
        expected_mean = 2 / (2 + 5)
        self.assertAlmostEqual(dist.mean(), expected_mean, places=3)
        
        # Test sampling
        samples = dist.sample(1000, random_state=np.random.RandomState(42))
        self.assertEqual(len(samples), 1000)
        self.assertTrue(np.all(samples >= 0))
        self.assertTrue(np.all(samples <= 1))
        
        # Test scaled beta
        dist_scaled = Beta(alpha=2, beta_param=5, min_val=10, max_val=20)
        samples_scaled = dist_scaled.sample(1000, random_state=np.random.RandomState(42))
        self.assertTrue(np.all(samples_scaled >= 10))
        self.assertTrue(np.all(samples_scaled <= 20))
    
    def test_uniform_distribution(self):
        """Test uniform distribution"""
        dist = Uniform(min_val=50, max_val=150)
        
        # Test properties
        self.assertEqual(dist.mean(), 100)
        self.assertAlmostEqual(dist.std(), (150 - 50) / np.sqrt(12), places=2)
        
        # Test sampling
        samples = dist.sample(1000, random_state=np.random.RandomState(42))
        self.assertEqual(len(samples), 1000)
        self.assertTrue(np.all(samples >= 50))
        self.assertTrue(np.all(samples <= 150))
    
    def test_lognormal_distribution(self):
        """Test log-normal distribution"""
        dist = LogNormal(mean_log=4.6, std_log=0.5)
        
        # Test sampling
        samples = dist.sample(1000, random_state=np.random.RandomState(42))
        self.assertEqual(len(samples), 1000)
        self.assertTrue(np.all(samples > 0))
        
        # Test bounds
        dist_bounded = LogNormal(mean_log=4.6, std_log=0.5, min_val=50, max_val=200)
        samples_bounded = dist_bounded.sample(1000, random_state=np.random.RandomState(42))
        self.assertTrue(np.all(samples_bounded >= 50))
        self.assertTrue(np.all(samples_bounded <= 200))
    
    def test_deterministic_distribution(self):
        """Test deterministic 'distribution'"""
        dist = Deterministic(value=42)
        
        # Test properties
        self.assertEqual(dist.mean(), 42)
        self.assertEqual(dist.std(), 0)
        self.assertEqual(dist.percentile(0.5), 42)
        
        # Test sampling
        samples = dist.sample(100)
        self.assertTrue(np.all(samples == 42))
    
    def test_confidence_intervals(self):
        """Test confidence interval calculation"""
        dist = Normal(mean_val=100, std_val=10)
        lower, upper = dist.confidence_interval(0.95)
        
        # For normal distribution, 95% CI should be approximately mean ± 1.96*std
        self.assertAlmostEqual(lower, 100 - 1.96 * 10, delta=1)
        self.assertAlmostEqual(upper, 100 + 1.96 * 10, delta=1)
    
    def test_create_distribution_from_config(self):
        """Test factory function for creating distributions"""
        # Normal
        config = {'type': 'normal', 'mean': 50, 'std': 5}
        dist = create_distribution_from_config(config)
        self.assertIsInstance(dist, Normal)
        self.assertEqual(dist.mean(), 50)
        
        # Triangular
        config = {'type': 'triangular', 'min': 10, 'mode': 15, 'max': 20}
        dist = create_distribution_from_config(config)
        self.assertIsInstance(dist, Triangular)
        
        # Beta
        config = {'type': 'beta', 'alpha': 3, 'beta': 7}
        dist = create_distribution_from_config(config)
        self.assertIsInstance(dist, Beta)
        
        # Deterministic (default)
        config = {'value': 100}
        dist = create_distribution_from_config(config)
        self.assertIsInstance(dist, Deterministic)
        self.assertEqual(dist.mean(), 100)


class TestParameterDistributions(unittest.TestCase):
    """Test parameter distribution container"""
    
    def test_parameter_distributions(self):
        """Test ParameterDistributions class"""
        params = ParameterDistributions()
        
        # Add distributions
        params.add_distribution('param1', Normal(100, 10))
        params.add_distribution('param2', Uniform(50, 150))
        
        # Test sampling
        samples = params.sample_all(100, random_state=np.random.RandomState(42))
        
        self.assertIn('param1', samples)
        self.assertIn('param2', samples)
        self.assertEqual(len(samples['param1']), 100)
        self.assertEqual(len(samples['param2']), 100)
    
    def test_correlations(self):
        """Test parameter correlations"""
        params = ParameterDistributions()
        
        params.add_distribution('param1', Normal(100, 10))
        params.add_distribution('param2', Normal(50, 5))
        
        # Add correlation
        params.add_correlation('param1', 'param2', 0.7)
        
        # Test correlation storage
        self.assertEqual(params.correlations[('param1', 'param2')], 0.7)
        self.assertEqual(params.correlations[('param2', 'param1')], 0.7)
        
        # Test validation
        with self.assertRaises(ValidationError):
            params.add_correlation('param1', 'param2', 1.5)  # Invalid correlation


class TestMonteCarloEngine(unittest.TestCase):
    """Test Monte Carlo simulation engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create simple parameter distributions
        self.distributions = ParameterDistributions()
        self.distributions.add_distribution('param1', Normal(100, 10))
        self.distributions.add_distribution('param2', Uniform(0.8, 1.2))
        
        # Create mock model runner
        def mock_model_runner(config):
            # Simple linear model for testing
            p1 = config.get('param1', 100)
            p2 = config.get('param2', 1.0)
            
            npv = p1 * p2 * 1000
            roi = (npv / 100000) * 100
            breakeven = max(1, int(24 - npv / 10000))
            
            return {
                'npv': npv,
                'roi_percent': roi,
                'breakeven_month': breakeven,
                'total_cost_3y': 100000,
                'total_value_3y': npv + 100000,
                'peak_adoption': 0.8,
                'annual_cost_per_dev': 1000,
                'annual_value_per_dev': 5000,
                'impact_breakdown': {},
                'baseline': None
            }
        
        self.model_runner = mock_model_runner
    
    def test_monte_carlo_engine_initialization(self):
        """Test Monte Carlo engine initialization"""
        engine = MonteCarloEngine(
            model_runner=self.model_runner,
            parameter_distributions=self.distributions,
            iterations=100,
            confidence_level=0.95,
            target_roi=100,
            random_seed=42
        )
        
        self.assertEqual(engine.iterations, 100)
        self.assertEqual(engine.confidence_level, 0.95)
        self.assertEqual(engine.target_roi, 100)
        self.assertEqual(engine.random_seed, 42)
    
    def test_monte_carlo_simulation(self):
        """Test running Monte Carlo simulation"""
        engine = MonteCarloEngine(
            model_runner=self.model_runner,
            parameter_distributions=self.distributions,
            iterations=100,
            random_seed=42,
            n_jobs=1
        )
        
        base_config = {'param1': 100, 'param2': 1.0}
        results = engine.run(base_config)
        
        # Check results structure
        self.assertIsInstance(results, MonteCarloResults)
        self.assertEqual(results.iterations, 100)
        self.assertEqual(len(results.npv_distribution), 100)
        self.assertEqual(len(results.roi_distribution), 100)
        
        # Check statistics
        self.assertIn('mean', results.npv_stats)
        self.assertIn('std', results.npv_stats)
        self.assertIn('p50', results.npv_stats)
        
        # Check risk metrics
        self.assertGreaterEqual(results.probability_positive_npv, 0)
        self.assertLessEqual(results.probability_positive_npv, 1)
        
        # Check sensitivity analysis
        self.assertIsInstance(results.parameter_correlations, dict)
        self.assertIsInstance(results.parameter_importance, list)
    
    def test_confidence_intervals(self):
        """Test confidence interval calculation"""
        engine = MonteCarloEngine(
            model_runner=self.model_runner,
            parameter_distributions=self.distributions,
            iterations=1000,
            confidence_level=0.95,
            random_seed=42,
            n_jobs=1
        )
        
        results = engine.run({})
        
        # Get confidence interval
        lower, upper = results.get_confidence_interval('npv', confidence=0.95)
        
        self.assertLess(lower, results.npv_stats['mean'])
        self.assertGreater(upper, results.npv_stats['mean'])
        
        # Check that ~95% of values are within interval
        within_ci = np.sum((results.npv_distribution >= lower) & 
                          (results.npv_distribution <= upper))
        proportion = within_ci / len(results.npv_distribution)
        self.assertAlmostEqual(proportion, 0.95, delta=0.05)
    
    def test_convergence_check(self):
        """Test convergence checking"""
        engine = MonteCarloEngine(
            model_runner=self.model_runner,
            parameter_distributions=self.distributions,
            iterations=10,  # Too few for convergence
            convergence_threshold=0.01,
            random_seed=42,
            n_jobs=1
        )
        
        results = engine.run({})
        self.assertFalse(results.convergence_achieved)
        
        # Test with more iterations
        engine.iterations = 500
        results = engine.run({})
        # May or may not converge depending on randomness


class TestMonteCarloIntegration(unittest.TestCase):
    """Test integration with main model"""
    
    def test_create_distributions_from_scenario(self):
        """Test creating distributions from scenario config"""
        scenario = {
            'baseline': {
                'team_size': 100,
                'avg_feature_cycle_days': {
                    'value': 30,
                    'distribution': {
                        'type': 'triangular',
                        'min': 25,
                        'mode': 30,
                        'max': 40
                    }
                }
            },
            'impact': {
                'feature_cycle_reduction': {
                    'value': 0.3,
                    'distribution': {
                        'type': 'normal',
                        'mean': 0.3,
                        'std': 0.05,
                        'min': 0.1,
                        'max': 0.5
                    }
                }
            },
            'correlations': [
                {
                    'param1': 'baseline.team_size',
                    'param2': 'impact.feature_cycle_reduction',
                    'correlation': 0.5
                }
            ]
        }
        
        distributions = create_parameter_distributions_from_scenario(scenario)
        
        # Check distributions were created
        self.assertIn('baseline.avg_feature_cycle_days', distributions.distributions)
        self.assertIn('impact.feature_cycle_reduction', distributions.distributions)
        
        # Check deterministic for non-distribution params
        self.assertIn('baseline.team_size', distributions.distributions)
        self.assertIsInstance(distributions.distributions['baseline.team_size'], Deterministic)
    
    def test_monte_carlo_results_methods(self):
        """Test MonteCarloResults methods"""
        # Create mock results
        results = MonteCarloResults(
            npv_distribution=np.random.normal(1000000, 200000, 1000),
            roi_distribution=np.random.normal(150, 30, 1000),
            breakeven_distribution=np.random.uniform(12, 24, 1000),
            total_value_distribution=np.random.normal(2000000, 300000, 1000),
            total_cost_distribution=np.random.normal(1000000, 100000, 1000),
            npv_stats={'mean': 1000000, 'std': 200000, 'p10': 700000, 'p50': 1000000, 'p90': 1300000},
            roi_stats={'mean': 150, 'std': 30, 'p10': 110, 'p50': 150, 'p90': 190},
            breakeven_stats={'mean': 18, 'std': 3, 'p10': 13, 'p50': 18, 'p90': 23},
            value_stats={},
            cost_stats={},
            probability_positive_npv=0.95,
            probability_breakeven_within_24_months=0.85,
            probability_roi_above_target=0.75,
            parameter_correlations={'param1': 0.8, 'param2': -0.3},
            parameter_importance=[('param1', 0.8), ('param2', 0.3)],
            iterations=1000,
            convergence_achieved=True,
            runtime_seconds=5.2,
            random_seed=42
        )
        
        # Test confidence interval
        lower, upper = results.get_confidence_interval('npv', confidence=0.90)
        self.assertLess(lower, upper)
        
        # Test invalid metric
        with self.assertRaises(ValueError):
            results.get_confidence_interval('invalid_metric')


if __name__ == '__main__':
    unittest.main()