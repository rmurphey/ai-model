"""
Advanced tests for batch processor module.
"""

import pytest
import yaml
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, call
from concurrent.futures import Future
import time

from src.batch.batch_processor import (
    BatchConfig,
    BatchResult,
    BatchProcessor
)
from src.utils.exceptions import ConfigurationError


class TestBatchConfig:
    """Test BatchConfig dataclass"""
    
    def test_batch_config_creation(self):
        """Test creating BatchConfig"""
        config = BatchConfig(
            scenarios=["scenario1", "scenario2"],
            parallel_workers=4,
            output_format="markdown",
            output_dir="outputs/batch",
            generate_comparison=True,
            include_monte_carlo=True,
            monte_carlo_iterations=1000,
            include_sensitivity=True,
            sensitivity_samples=512,
            save_individual_reports=True
        )
        
        assert config.scenarios == ["scenario1", "scenario2"]
        assert config.parallel_workers == 4
        assert config.include_monte_carlo is True
        assert config.monte_carlo_iterations == 1000
    
    def test_batch_config_defaults(self):
        """Test BatchConfig with defaults"""
        config = BatchConfig(scenarios=["test"])
        
        assert config.parallel_workers == 4
        assert config.output_format == "markdown"
        assert config.generate_comparison is True
        assert config.include_monte_carlo is False
        assert config.save_individual_reports is True
    
    def test_from_yaml_valid(self, tmp_path):
        """Test loading BatchConfig from valid YAML"""
        yaml_path = tmp_path / "batch_config.yaml"
        config_data = {
            "scenarios": ["s1", "s2", "s3"],
            "parallel_workers": 8,
            "output_format": "json",
            "include_monte_carlo": True,
            "monte_carlo_iterations": 500
        }
        
        with open(yaml_path, 'w') as f:
            yaml.dump(config_data, f)
        
        config = BatchConfig.from_yaml(str(yaml_path))
        
        assert config.scenarios == ["s1", "s2", "s3"]
        assert config.parallel_workers == 8
        assert config.output_format == "json"
        assert config.include_monte_carlo is True
        assert config.monte_carlo_iterations == 500
    
    def test_from_yaml_file_not_found(self):
        """Test loading BatchConfig from non-existent file"""
        with pytest.raises(ConfigurationError) as exc_info:
            BatchConfig.from_yaml("nonexistent.yaml")
        
        assert "not found" in str(exc_info.value)
    
    def test_from_yaml_invalid_yaml(self, tmp_path):
        """Test loading BatchConfig from invalid YAML"""
        yaml_path = tmp_path / "bad_config.yaml"
        yaml_path.write_text("{ invalid yaml content :")
        
        with pytest.raises(ConfigurationError):
            BatchConfig.from_yaml(str(yaml_path))


class TestBatchResult:
    """Test BatchResult dataclass"""
    
    def test_batch_result_success(self):
        """Test successful BatchResult"""
        result = BatchResult(
            scenario_name="test_scenario",
            success=True,
            results={"npv": 1000000},
            execution_time=2.5,
            cache_hit=True
        )
        
        assert result.scenario_name == "test_scenario"
        assert result.success is True
        assert result.results["npv"] == 1000000
        assert result.error_message is None
        assert result.cache_hit is True
    
    def test_batch_result_failure(self):
        """Test failed BatchResult"""
        result = BatchResult(
            scenario_name="bad_scenario",
            success=False,
            error_message="Scenario not found",
            execution_time=0.1
        )
        
        assert result.scenario_name == "bad_scenario"
        assert result.success is False
        assert result.results is None
        assert result.error_message == "Scenario not found"
        assert result.cache_hit is False


class TestBatchProcessor:
    """Test BatchProcessor class"""
    
    @pytest.fixture
    def simple_config(self):
        """Create simple batch config"""
        return BatchConfig(
            scenarios=["scenario1", "scenario2"],
            parallel_workers=2,
            output_dir="outputs/test_batch"
        )
    
    @pytest.fixture
    def processor(self, simple_config, tmp_path):
        """Create batch processor with temp directory"""
        simple_config.output_dir = str(tmp_path / "batch")
        return BatchProcessor(simple_config)
    
    def test_processor_initialization(self, processor, simple_config):
        """Test BatchProcessor initialization"""
        assert processor.config == simple_config
        assert processor.results == []
        assert processor.output_dir.exists()
    
    @patch('src.batch.batch_processor.AIImpactModel')
    def test_process_scenario_success(self, mock_model_class, processor):
        """Test successful scenario processing"""
        # Mock model instance
        mock_model = Mock()
        mock_model._run_scenario_cached.return_value = {
            "financial": {"npv": 1000000, "roi": 2.5},
            "adoption": {"peak": 0.8}
        }
        mock_model_class.return_value = mock_model
        
        result = processor._process_scenario("test_scenario")
        
        assert result.success is True
        assert result.scenario_name == "test_scenario"
        assert result.results["financial"]["npv"] == 1000000
        assert result.execution_time > 0
    
    @patch('src.batch.batch_processor.AIImpactModel')
    def test_process_scenario_failure(self, mock_model_class, processor):
        """Test failed scenario processing"""
        mock_model = Mock()
        mock_model._run_scenario_cached.side_effect = Exception("Test error")
        mock_model_class.return_value = mock_model
        
        result = processor._process_scenario("bad_scenario")
        
        assert result.success is False
        assert result.scenario_name == "bad_scenario"
        assert "Test error" in result.error_message
        assert result.results is None
    
    @patch('src.batch.batch_processor.AIImpactModel')
    def test_process_scenario_with_monte_carlo(self, mock_model_class, processor):
        """Test scenario processing with Monte Carlo"""
        processor.config.include_monte_carlo = True
        processor.config.monte_carlo_iterations = 100
        
        mock_model = Mock()
        mock_model._run_scenario_cached.return_value = {"financial": {"npv": 1000000}}
        
        # Mock Monte Carlo results
        mock_mc_results = Mock()
        mock_mc_results.npv_stats = {
            "mean": 1100000,
            "std": 50000,
            "p10": 1000000,
            "p90": 1200000
        }
        mock_mc_results.probability_positive_npv = 0.95
        mock_model.run_monte_carlo.return_value = mock_mc_results
        
        mock_model_class.return_value = mock_model
        
        result = processor._process_scenario("mc_scenario")
        
        assert result.success is True
        assert "monte_carlo" in result.results
        assert result.results["monte_carlo"]["mean_npv"] == 1100000
        assert result.results["monte_carlo"]["probability_positive"] == 0.95
    
    @patch('src.batch.batch_processor.run_sensitivity_analysis')
    @patch('src.batch.batch_processor.AIImpactModel')
    def test_process_scenario_with_sensitivity(self, mock_model_class, mock_sensitivity, processor):
        """Test scenario processing with sensitivity analysis"""
        processor.config.include_sensitivity = True
        processor.config.sensitivity_samples = 256
        
        mock_model = Mock()
        mock_model._run_scenario_cached.return_value = {"financial": {"npv": 1000000}}
        mock_model_class.return_value = mock_model
        
        # Mock sensitivity results
        mock_sensitivity.return_value = {
            "ranked_parameters": [
                {"name": "param1", "importance": 0.5},
                {"name": "param2", "importance": 0.3}
            ],
            "variance_explained": 0.8
        }
        
        result = processor._process_scenario("sens_scenario")
        
        assert result.success is True
        assert "sensitivity" in result.results
        assert len(result.results["sensitivity"]["top_parameters"]) == 2
        assert result.results["sensitivity"]["total_variance_explained"] == 0.8
    
    def test_save_individual_report(self, processor, tmp_path):
        """Test saving individual scenario report"""
        processor.config.output_dir = str(tmp_path)
        processor.output_dir = tmp_path
        
        results = {
            "financial": {"npv": 1000000},
            "adoption": {"peak": 0.8}
        }
        
        processor._save_individual_report("test_scenario", results)
        
        report_file = tmp_path / "test_scenario_report.json"
        assert report_file.exists()
        
        saved_data = json.loads(report_file.read_text())
        assert saved_data == results
    
    @patch('src.batch.batch_processor.ProcessPoolExecutor')
    def test_run_parallel(self, mock_executor_class, processor):
        """Test parallel execution"""
        processor.config.parallel_workers = 2
        
        # Mock executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Create mock futures
        future1 = Mock(spec=Future)
        future1.result.return_value = BatchResult(
            "scenario1", True, {"npv": 1000000}, execution_time=1.0
        )
        
        future2 = Mock(spec=Future)
        future2.result.return_value = BatchResult(
            "scenario2", True, {"npv": 2000000}, execution_time=1.5
        )
        
        mock_executor.submit.side_effect = [future1, future2]
        
        # Mock as_completed
        with patch('src.batch.batch_processor.as_completed') as mock_as_completed:
            mock_as_completed.return_value = [future1, future2]
            
            processor._run_parallel()
        
        assert len(processor.results) == 2
        assert processor.results[0].scenario_name in ["scenario1", "scenario2"]
        assert all(r.success for r in processor.results)
    
    def test_run_sequential(self, processor):
        """Test sequential execution"""
        with patch.object(processor, '_process_scenario') as mock_process:
            mock_process.side_effect = [
                BatchResult("scenario1", True, {"npv": 1000000}, execution_time=1.0),
                BatchResult("scenario2", True, {"npv": 2000000}, execution_time=1.5)
            ]
            
            processor._run_sequential()
        
        assert len(processor.results) == 2
        assert processor.results[0].scenario_name == "scenario1"
        assert processor.results[1].scenario_name == "scenario2"
    
    def test_generate_comparison_report(self, processor):
        """Test comparison report generation"""
        processor.results = [
            BatchResult("scenario1", True, {
                "financial": {"npv": 1000000, "roi": 2.0},
                "adoption": {"peak": 0.8}
            }, execution_time=1.0),
            BatchResult("scenario2", True, {
                "financial": {"npv": 2000000, "roi": 3.0},
                "adoption": {"peak": 0.9}
            }, execution_time=1.5),
            BatchResult("scenario3", False, error_message="Failed", execution_time=0.1)
        ]
        
        report = processor._generate_comparison_report()
        
        assert "Comparison Report" in report
        assert "scenario1" in report
        assert "scenario2" in report
        assert "1,000,000" in report or "1000000" in report
        assert "Failed" in report
    
    def test_save_results(self, processor, tmp_path):
        """Test saving batch results"""
        processor.config.output_dir = str(tmp_path)
        processor.output_dir = tmp_path
        processor.timestamp = "20240101_120000"
        
        processor.results = [
            BatchResult("scenario1", True, {"npv": 1000000}, execution_time=1.0)
        ]
        
        report = "# Test Report"
        report_path, json_path = processor._save_results(report)
        
        assert report_path.exists()
        assert json_path.exists()
        assert report_path.name == "batch_report_20240101_120000.md"
        assert json_path.name == "batch_results_20240101_120000.json"
        
        # Check content
        assert report_path.read_text() == report
        saved_json = json.loads(json_path.read_text())
        assert saved_json["results"][0]["scenario_name"] == "scenario1"
    
    @patch('src.batch.batch_processor.AIImpactModel')
    def test_run_complete_workflow(self, mock_model_class, processor, tmp_path):
        """Test complete batch processing workflow"""
        processor.config.output_dir = str(tmp_path)
        processor.output_dir = tmp_path
        processor.config.parallel_workers = 1  # Sequential for simplicity
        
        mock_model = Mock()
        mock_model._run_scenario_cached.return_value = {
            "financial": {"npv": 1000000, "roi": 2.5}
        }
        mock_model_class.return_value = mock_model
        
        with patch('builtins.print'):
            results, report = processor.run()
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert "Batch Processing Summary" in report
        
        # Check files were created
        assert len(list(tmp_path.glob("*.md"))) > 0
        assert len(list(tmp_path.glob("*.json"))) > 0
    
    def test_error_handling_in_parallel(self, processor):
        """Test error handling in parallel execution"""
        processor.config.parallel_workers = 2
        
        with patch.object(processor, '_process_scenario') as mock_process:
            # One success, one failure
            mock_process.side_effect = [
                BatchResult("scenario1", True, {"npv": 1000000}, execution_time=1.0),
                Exception("Unexpected error")
            ]
            
            with patch('src.batch.batch_processor.ProcessPoolExecutor'):
                with patch('src.batch.batch_processor.as_completed'):
                    # Should handle exception gracefully
                    processor._run_parallel()
        
        # Should have at least the successful result
        successful = [r for r in processor.results if r.success]
        assert len(successful) >= 1