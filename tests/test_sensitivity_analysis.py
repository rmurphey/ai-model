"""
Tests for SALib-based sensitivity analysis implementation.
Focus on testing our wrapper code, not SALib's algorithms.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.analysis.sensitivity_analysis import (
    SensitivityResults,
    SobolAnalyzer,
    format_sensitivity_report,
    run_sobol_analysis,
    run_sensitivity_analysis
)
from src.model.distributions import (
    ParameterDistributions,
    Uniform,
    Normal
)


class TestSobolAnalyzerProblemDefinition:
    """Test conversion from ParameterDistributions to SALib problem format"""
    
    def test_uniform_distribution_conversion(self):
        """Test that uniform distributions are correctly converted to bounds"""
        distributions = ParameterDistributions()
        distributions.add_distribution("param1", Uniform(min_val=0, max_val=10))
        distributions.add_distribution("param2", Uniform(min_val=-5, max_val=5))
        
        def dummy_model(params):
            return sum(params.values())
        
        analyzer = SobolAnalyzer(dummy_model, distributions)
        problem = analyzer.problem
        
        assert problem['num_vars'] == 2
        assert problem['names'] == ['param1', 'param2']
        assert problem['bounds'] == [[0, 10], [-5, 5]]
    
    def test_normal_distribution_conversion(self):
        """Test that normal distributions use 3-sigma bounds"""
        distributions = ParameterDistributions()
        distributions.add_distribution("param1", Normal(mean_val=10, std_val=2))
        
        def dummy_model(params):
            return params['param1']
        
        analyzer = SobolAnalyzer(dummy_model, distributions)
        problem = analyzer.problem
        
        assert problem['num_vars'] == 1
        assert problem['names'] == ['param1']
        # Should use mean ± 3*std
        expected_bounds = [[10 - 3*2, 10 + 3*2]]  # [4, 16]
        assert problem['bounds'] == expected_bounds
    
    def test_mixed_distributions(self):
        """Test handling of mixed distribution types"""
        distributions = ParameterDistributions()
        distributions.add_distribution("uniform_param", Uniform(min_val=0, max_val=1))
        distributions.add_distribution("normal_param", Normal(mean_val=5, std_val=1))
        
        def dummy_model(params):
            return sum(params.values())
        
        analyzer = SobolAnalyzer(dummy_model, distributions)
        problem = analyzer.problem
        
        assert problem['num_vars'] == 2
        assert 'uniform_param' in problem['names']
        assert 'normal_param' in problem['names']
        assert len(problem['bounds']) == 2


class TestSobolAnalyzerCalculation:
    """Test the calculate_indices method with mocked SALib"""
    
    @patch('src.analysis.sensitivity_analysis.sobol.analyze')
    @patch('src.analysis.sensitivity_analysis.saltelli.sample')
    def test_calculate_indices_basic(self, mock_sample, mock_analyze):
        """Test basic index calculation with mocked SALib"""
        # Setup distributions
        distributions = ParameterDistributions()
        distributions.add_distribution("param1", Uniform(min_val=0, max_val=1))
        distributions.add_distribution("param2", Uniform(min_val=0, max_val=1))
        
        # Mock SALib sampling
        n_samples = 8
        mock_sample.return_value = np.array([
            [0.5, 0.5],
            [0.3, 0.7],
            [0.8, 0.2],
            [0.1, 0.9]
        ])
        
        # Mock SALib analysis results
        mock_analyze.return_value = {
            'S1': np.array([0.6, 0.3]),  # First-order indices
            'ST': np.array([0.7, 0.4]),  # Total indices
            'S1_conf': np.array([0.05, 0.03]),  # Confidence intervals
            'ST_conf': np.array([0.06, 0.04])
        }
        
        # Create analyzer and run
        def model(params):
            return params['param1'] * 2 + params['param2']
        
        analyzer = SobolAnalyzer(model, distributions)
        results = analyzer.calculate_indices(n_samples=n_samples, calc_second_order=False)
        
        # Verify SALib was called correctly
        mock_sample.assert_called_once()
        mock_analyze.assert_called_once()
        
        # Check results structure
        assert isinstance(results, SensitivityResults)
        assert results.n_samples == n_samples
        assert results.n_params == 2
        
        # Check extracted indices
        assert results.first_order_indices['param1'] == 0.6
        assert results.first_order_indices['param2'] == 0.3
        assert results.total_indices['param1'] == 0.7
        assert results.total_indices['param2'] == 0.4
        
        # Check confidence intervals (use approximate comparison for floats)
        assert abs(results.first_order_conf['param1'][0] - 0.55) < 0.001
        assert abs(results.first_order_conf['param1'][1] - 0.65) < 0.001
        assert abs(results.first_order_conf['param2'][0] - 0.27) < 0.001
        assert abs(results.first_order_conf['param2'][1] - 0.33) < 0.001
    
    def test_model_failure_handling(self):
        """Test graceful handling when model evaluations fail"""
        distributions = ParameterDistributions()
        distributions.add_distribution("param1", Uniform(min_val=0, max_val=1))
        
        # Model that always fails
        def failing_model(params):
            raise ValueError("Model failure")
        
        analyzer = SobolAnalyzer(failing_model, distributions)
        
        with patch('src.analysis.sensitivity_analysis.saltelli.sample') as mock_sample:
            mock_sample.return_value = np.array([[0.5], [0.3], [0.8]])
            
            results = analyzer.calculate_indices(n_samples=8)
            
            # Should return empty results when all evaluations fail
            assert results.n_samples == 0
            assert results.convergence_achieved is False
            assert results.variance_explained == 0.0
            assert all(v == 0.0 for v in results.first_order_indices.values())
    
    @patch('src.analysis.sensitivity_analysis.sobol.analyze')
    @patch('src.analysis.sensitivity_analysis.saltelli.sample')
    def test_convergence_detection(self, mock_sample, mock_analyze):
        """Test convergence detection based on confidence intervals"""
        distributions = ParameterDistributions()
        distributions.add_distribution("param1", Uniform(min_val=0, max_val=1))
        
        mock_sample.return_value = np.array([[0.5], [0.3]])
        
        # Test with tight confidence intervals (converged)
        mock_analyze.return_value = {
            'S1': np.array([0.6]),
            'ST': np.array([0.7]),
            'S1_conf': np.array([0.02]),  # Small confidence interval
            'ST_conf': np.array([0.03])
        }
        
        def model(params):
            return params['param1']
        
        analyzer = SobolAnalyzer(model, distributions)
        results = analyzer.calculate_indices(n_samples=8)
        
        # Should be converged (conf interval width = 0.04 < 0.1)
        assert results.convergence_achieved is True
        
        # Test with wide confidence intervals (not converged)
        mock_analyze.return_value = {
            'S1': np.array([0.6]),
            'ST': np.array([0.7]),
            'S1_conf': np.array([0.2]),  # Large confidence interval
            'ST_conf': np.array([0.3])
        }
        
        results = analyzer.calculate_indices(n_samples=8)
        
        # Should not be converged (conf interval width = 0.4 > 0.1)
        assert results.convergence_achieved is False


class TestReportFormatting:
    """Test the format_sensitivity_report function"""
    
    def test_format_report_basic(self):
        """Test basic report formatting"""
        # Create mock results
        results = SensitivityResults(
            first_order_indices={'param1': 0.6, 'param2': 0.3},
            total_indices={'param1': 0.7, 'param2': 0.4},
            second_order_indices={},
            first_order_conf={'param1': (0.55, 0.65), 'param2': (0.25, 0.35)},
            total_conf={'param1': (0.65, 0.75), 'param2': (0.35, 0.45)},
            n_samples=1024,
            n_params=2,
            model_outputs_mean=10.5,
            model_outputs_std=2.3,
            partial_dependence={},
            parameter_ranges={'param1': (0, 1), 'param2': (0, 1)},
            convergence_achieved=True,
            variance_explained=0.9,
            computation_time=5.2
        )
        
        report = format_sensitivity_report(results)
        
        # Check report contains key information
        assert "SENSITIVITY ANALYSIS REPORT" in report
        assert "Parameters analyzed: 2" in report
        assert "Sample size: 1024" in report
        assert "Convergence achieved: True" in report
        assert "param1" in report
        assert "param2" in report
        assert "0.6000" in report  # First-order index for param1
        assert "[0.550, 0.650]" in report  # Confidence interval
    
    def test_format_report_with_interactions(self):
        """Test report formatting with second-order interactions"""
        results = SensitivityResults(
            first_order_indices={'param1': 0.4, 'param2': 0.3},
            total_indices={'param1': 0.6, 'param2': 0.5},
            second_order_indices={('param1', 'param2'): 0.15},
            first_order_conf=None,
            total_conf=None,
            n_samples=512,
            n_params=2,
            model_outputs_mean=5.0,
            model_outputs_std=1.0,
            partial_dependence={},
            parameter_ranges={'param1': (0, 1), 'param2': (0, 1)},
            convergence_achieved=False,
            variance_explained=0.7,
            computation_time=2.5
        )
        
        report = format_sensitivity_report(results)
        
        # Check interactions section
        assert "INTERACTION EFFECTS" in report
        assert "TOP PAIRWISE INTERACTIONS" in report
        assert "param1 × param2" in report
        assert "0.1500" in report  # Second-order index


class TestIntegration:
    """Integration tests with real SALib calls"""
    
    def test_end_to_end_small_sample(self):
        """Test complete workflow with small sample size"""
        # Create distributions
        distributions = ParameterDistributions()
        distributions.add_distribution("x1", Uniform(min_val=0, max_val=1))
        distributions.add_distribution("x2", Uniform(min_val=0, max_val=1))
        distributions.add_distribution("x3", Uniform(min_val=0, max_val=1))
        
        # Simple additive model
        def model(params):
            return params['x1'] + 0.5 * params['x2'] + 0.1 * params['x3']
        
        # Run analysis with small sample size
        results = run_sobol_analysis(
            model,
            distributions,
            n_samples=64,  # Small for speed
            calc_second_order=False
        )
        
        # Basic checks
        assert isinstance(results, SensitivityResults)
        assert results.n_params == 3
        assert 'x1' in results.first_order_indices
        assert 'x2' in results.first_order_indices
        assert 'x3' in results.first_order_indices
        
        # For this additive model, x1 should have highest importance
        # (but with small samples, we can't guarantee exact ordering)
        assert results.variance_explained >= 0  # Should be positive
        assert results.computation_time > 0
    
    def test_run_sensitivity_analysis_mock_scenario(self):
        """Test the high-level run_sensitivity_analysis function"""
        with patch('src.scenarios.scenario_loader.ScenarioLoader') as mock_loader_class:
            # Mock scenario configuration
            mock_loader = Mock()
            mock_loader.load_scenario.return_value = {
                'adoption': {'early_adopters': 0.2},
                'impact': {
                    'feature_cycle_reduction': 0.3,
                    'defect_reduction': 0.25
                },
                'costs': {
                    'cost_per_seat_month': 100,
                    'token_price_per_million': 10
                }
            }
            mock_loader_class.return_value = mock_loader
            
            with patch('main.AIImpactModel') as mock_model_class:
                # Mock model that returns simple calculation
                mock_model = Mock()
                mock_model._run_scenario_cached.return_value = {'npv': 50000}
                mock_model_class.return_value = mock_model
                
                # Run analysis
                results = run_sensitivity_analysis("test_scenario", n_samples=32)
                
                # Check results structure
                assert isinstance(results, dict)
                assert 'ranked_parameters' in results
                assert 'variance_explained' in results
                assert isinstance(results['ranked_parameters'], list)
                
                # Check parameters are included
                param_names = [p['name'] for p in results['ranked_parameters']]
                assert 'adoption_rate' in param_names
                assert 'feature_cycle_reduction' in param_names


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_distributions(self):
        """Test with no parameters"""
        distributions = ParameterDistributions()
        
        def model(params):
            return 1.0
        
        with pytest.raises(Exception):
            # Should fail with no parameters
            analyzer = SobolAnalyzer(model, distributions)
            analyzer.calculate_indices(n_samples=8)
    
    def test_single_parameter(self):
        """Test with only one parameter"""
        distributions = ParameterDistributions()
        distributions.add_distribution("only_param", Uniform(min_val=0, max_val=1))
        
        def model(params):
            return params['only_param'] * 2
        
        analyzer = SobolAnalyzer(model, distributions)
        
        with patch('src.analysis.sensitivity_analysis.saltelli.sample') as mock_sample:
            with patch('src.analysis.sensitivity_analysis.sobol.analyze') as mock_analyze:
                mock_sample.return_value = np.array([[0.5], [0.3]])
                mock_analyze.return_value = {
                    'S1': np.array([1.0]),  # Should be 1 for single param
                    'ST': np.array([1.0])
                }
                
                results = analyzer.calculate_indices(n_samples=8)
                
                assert results.n_params == 1
                assert results.first_order_indices['only_param'] == 1.0
                assert results.variance_explained == 1.0