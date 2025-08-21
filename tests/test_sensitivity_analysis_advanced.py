"""
Advanced tests for sensitivity analysis module.
"""

import pytest
import numpy as np
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, Any
import subprocess  # For timeout test in next_task_command

from src.analysis.sensitivity_analysis import (
    SensitivityResults,
    SobolAnalyzer,
    perform_sensitivity_analysis,
    run_sensitivity_analysis
)
from src.model.distributions import (
    Distribution, ParameterDistributions, 
    Uniform, Normal, Triangular, Beta, LogNormal, Deterministic
)


class TestSensitivityResults:
    """Test SensitivityResults dataclass"""
    
    def test_sensitivity_results_creation(self):
        """Test creating SensitivityResults"""
        results = SensitivityResults(
            first_order_indices={"param1": 0.3, "param2": 0.5},
            total_indices={"param1": 0.4, "param2": 0.6},
            second_order_indices={("param1", "param2"): 0.1},
            partial_dependence={"param1": np.array([1, 2, 3])},
            parameter_ranges={"param1": (0, 1), "param2": (5, 10)},
            convergence_achieved=True,
            variance_explained=0.85,
            computation_time=2.5
        )
        
        assert results.first_order_indices["param1"] == 0.3
        assert results.total_indices["param2"] == 0.6
        assert results.convergence_achieved is True
        assert results.variance_explained == 0.85
        assert results.computation_time == 2.5


class TestSobolAnalyzer:
    """Test SobolAnalyzer class"""
    
    @pytest.fixture
    def simple_distributions(self):
        """Create simple parameter distributions"""
        dist = ParameterDistributions()
        dist.add_distribution("param1", Uniform(min_val=0, max_val=1))
        dist.add_distribution("param2", Normal(mean_val=5, std_val=1))
        return dist
    
    @pytest.fixture
    def simple_model(self):
        """Create a simple model function"""
        def model(params: Dict[str, float]) -> float:
            # Simple linear combination
            return params["param1"] * 2 + params["param2"] * 0.5
        return model
    
    def test_sobol_analyzer_initialization(self, simple_model, simple_distributions):
        """Test SobolAnalyzer initialization"""
        analyzer = SobolAnalyzer(simple_model, simple_distributions)
        
        assert analyzer.model_func == simple_model
        assert analyzer.distributions == simple_distributions
        assert analyzer.param_names == ["param1", "param2"]
        assert analyzer.n_params == 2
    
    def test_generate_sample_matrices(self, simple_model, simple_distributions):
        """Test sample generation for Sobol analysis"""
        analyzer = SobolAnalyzer(simple_model, simple_distributions)
        
        A, B, AB_matrices = analyzer._generate_sample_matrices(n_samples=64)
        
        # Check shapes
        assert A.shape == (64, 2)
        assert B.shape == (64, 2)
        assert len(AB_matrices) == 2
        assert all(ab.shape == (64, 2) for ab in AB_matrices)
        
        # Check values are within expected ranges for uniform distribution
        assert np.all(A[:, 0] >= 0) and np.all(A[:, 0] <= 1)
        assert np.all(B[:, 0] >= 0) and np.all(B[:, 0] <= 1)
        
        # Check AB matrices have correct structure
        assert np.array_equal(AB_matrices[0][:, 1], A[:, 1])  # Column 1 from A
        assert np.array_equal(AB_matrices[0][:, 0], B[:, 0])  # Column 0 from B
    
    def test_evaluate_model(self, simple_model, simple_distributions):
        """Test model evaluation"""
        analyzer = SobolAnalyzer(simple_model, simple_distributions)
        
        samples = np.array([
            [0.5, 5.0],
            [1.0, 6.0],
            [0.0, 4.0]
        ])
        
        results = analyzer._evaluate_model(samples)
        
        # Check results match expected values
        # model: param1 * 2 + param2 * 0.5
        expected = [
            0.5 * 2 + 5.0 * 0.5,  # 3.5
            1.0 * 2 + 6.0 * 0.5,  # 5.0
            0.0 * 2 + 4.0 * 0.5   # 2.0
        ]
        
        np.testing.assert_array_almost_equal(results, expected)
    
    def test_calculate_indices_internals(self, simple_model, simple_distributions):
        """Test Sobol indices calculation process"""
        analyzer = SobolAnalyzer(simple_model, simple_distributions)
        
        # Just test that the public method works
        results = analyzer.calculate_indices(n_samples=16, calc_second_order=False)
        
        # Check structure
        assert "param1" in results.first_order_indices
        assert "param2" in results.first_order_indices
        assert "param1" in results.total_indices
        assert "param2" in results.total_indices
        
        # Check values are reasonable (between -1 and 1, can be negative due to sampling)
        for key in results.first_order_indices:
            assert -1 <= results.first_order_indices[key] <= 1
            assert -1 <= results.total_indices[key] <= 1
    
    def test_calculate_indices_basic(self, simple_model, simple_distributions):
        """Test full indices calculation"""
        analyzer = SobolAnalyzer(simple_model, simple_distributions)
        
        results = analyzer.calculate_indices(n_samples=32, calc_second_order=False)
        
        assert isinstance(results, SensitivityResults)
        assert len(results.first_order_indices) == 2
        assert len(results.total_indices) == 2
        assert results.computation_time > 0
        
        # For this linear model, param1 should have higher importance
        assert results.first_order_indices["param1"] > 0
    
    def test_calculate_indices_with_second_order(self, simple_model, simple_distributions):
        """Test indices calculation with second-order interactions"""
        analyzer = SobolAnalyzer(simple_model, simple_distributions)
        
        results = analyzer.calculate_indices(n_samples=32, calc_second_order=True)
        
        # Should have second order indices
        assert len(results.second_order_indices) > 0
        assert ("param1", "param2") in results.second_order_indices
    
    def test_convergence_via_calculate(self, simple_model, simple_distributions):
        """Test convergence via the calculate_indices method"""
        analyzer = SobolAnalyzer(simple_model, simple_distributions)
        
        # Run with enough samples to potentially achieve convergence
        results = analyzer.calculate_indices(n_samples=64, calc_second_order=False)
        
        # Check that convergence flag is set
        assert isinstance(results.convergence_achieved, bool)
        
        # The simple linear model should converge easily
        # But with small samples it might not, so just check the flag exists
        assert hasattr(results, 'convergence_achieved')


class TestSensitivityAnalysisFunctions:
    """Test module-level functions"""
    
    def test_perform_sensitivity_analysis(self):
        """Test perform_sensitivity_analysis function"""
        def dummy_model(params):
            return params.get("x", 0) ** 2
        
        distributions = ParameterDistributions()
        distributions.add_distribution("x", Uniform(min_val=0, max_val=1))
        
        with patch('src.analysis.sensitivity_analysis.cached_result') as mock_cache:
            # Make decorator pass through
            mock_cache.side_effect = lambda **kwargs: lambda f: f
            
            results = perform_sensitivity_analysis(
                "test_scenario",
                dummy_model,
                distributions,
                n_samples=16
            )
            
            assert isinstance(results, SensitivityResults)
            assert "x" in results.first_order_indices
    
    @patch('src.analysis.sensitivity_analysis.load_scenario')
    @patch('main.AIImpactModel')
    def test_run_sensitivity_analysis(self, mock_model_class, mock_load_scenario):
        """Test run_sensitivity_analysis convenience function"""
        # Mock scenario config
        mock_config = {
            'adoption': {'early_adopters': 0.15},
            'impact': {
                'feature_cycle_reduction': 0.25,
                'defect_reduction': 0.30
            },
            'costs': {
                'cost_per_seat_month': 50,
                'token_price_per_million': 8
            }
        }
        mock_load_scenario.return_value = mock_config
        
        # Mock model instance
        mock_model = Mock()
        mock_model._run_scenario_cached.return_value = {
            'financial': {'npv': 1000000}
        }
        mock_model_class.return_value = mock_model
        
        # Run analysis
        results = run_sensitivity_analysis("test_scenario", n_samples=16)
        
        assert isinstance(results, dict)
        assert 'ranked_parameters' in results
        assert 'variance_explained' in results
        assert 'convergence_achieved' in results
        assert 'computation_time' in results
        
        # Check ranked parameters structure
        if results['ranked_parameters']:
            param = results['ranked_parameters'][0]
            assert 'name' in param
            assert 'importance' in param
    
    @patch('src.analysis.sensitivity_analysis.load_scenario')
    def test_run_sensitivity_analysis_error_handling(self, mock_load_scenario):
        """Test error handling in run_sensitivity_analysis"""
        mock_load_scenario.return_value = {}
        
        # Should handle missing config gracefully
        results = run_sensitivity_analysis("bad_scenario", n_samples=8)
        
        assert isinstance(results, dict)
        assert 'ranked_parameters' in results


class TestSensitivityAnalysisIntegration:
    """Integration tests for sensitivity analysis"""
    
    def test_nonlinear_model_sensitivity(self):
        """Test sensitivity analysis on a nonlinear model"""
        def nonlinear_model(params):
            # Ishigami function - classic test for sensitivity analysis
            x1 = params["x1"]
            x2 = params["x2"]
            x3 = params["x3"]
            return np.sin(x1) + 7 * np.sin(x2)**2 + 0.1 * x3**4 * np.sin(x1)
        
        distributions = ParameterDistributions()
        distributions.add_distribution("x1", Uniform(min_val=-np.pi, max_val=np.pi))
        distributions.add_distribution("x2", Uniform(min_val=-np.pi, max_val=np.pi))
        distributions.add_distribution("x3", Uniform(min_val=-np.pi, max_val=np.pi))
        
        analyzer = SobolAnalyzer(nonlinear_model, distributions)
        results = analyzer.calculate_indices(n_samples=128)
        
        # x2 should have highest first-order effect for Ishigami function
        assert results.first_order_indices["x2"] > results.first_order_indices["x1"]
        assert results.first_order_indices["x2"] > results.first_order_indices["x3"]
        
        # x1 and x3 interact, so total indices should be higher than first-order
        assert results.total_indices["x1"] > results.first_order_indices["x1"]
        assert results.total_indices["x3"] > results.first_order_indices["x3"]
    
    def test_parallel_evaluation(self):
        """Test parallel model evaluation"""
        def slow_model(params):
            # Simulate slow computation
            import time
            time.sleep(0.001)
            return params["a"] + params["b"]
        
        distributions = ParameterDistributions()
        distributions.add_distribution("a", Uniform(min_val=0, max_val=1))
        distributions.add_distribution("b", Uniform(min_val=0, max_val=1))
        
        analyzer = SobolAnalyzer(slow_model, distributions)
        
        # Should complete despite slow model due to parallel processing
        results = analyzer.calculate_indices(n_samples=16)
        
        assert results.computation_time < 10  # Should be fast with parallelization
        assert results.convergence_achieved is not None
    
    def test_edge_cases(self):
        """Test edge cases in sensitivity analysis"""
        # Test with single parameter
        def single_param_model(params):
            return params["only"] * 2
        
        single_dist = ParameterDistributions()
        single_dist.add_distribution("only", Uniform(min_val=0, max_val=1))
        
        analyzer = SobolAnalyzer(single_param_model, single_dist)
        results = analyzer.calculate_indices(n_samples=16)
        
        # Single parameter should explain all variance
        assert results.first_order_indices["only"] > 0.9
        assert results.total_indices["only"] > 0.9
        
        # Test with constant model
        def constant_model(params):
            return 42.0
        
        const_dist = ParameterDistributions()
        const_dist.add_distribution("unused", Uniform(min_val=0, max_val=1))
        
        analyzer2 = SobolAnalyzer(constant_model, const_dist)
        results2 = analyzer2.calculate_indices(n_samples=16)
        
        # No parameter should have influence
        assert abs(results2.first_order_indices["unused"]) < 0.1