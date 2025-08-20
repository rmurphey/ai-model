#!/usr/bin/env python3
"""
Test suite for the reproduction engine
Tests metadata extraction, scenario building, and result validation.
"""

import os
import sys
import unittest
import tempfile
import yaml
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reproducibility.reproduction_engine import (
    MetadataExtractor, ScenarioBuilder, ReproductionEngine,
    ReproductionMetadata, ReproductionResult
)
from src.reproducibility.validators import ValidationConfig, create_validation_config
from src.utils.exceptions import ValidationError


class TestMetadataExtractor(unittest.TestCase):
    """Test metadata extraction from markdown reports"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = MetadataExtractor()
        
        # Sample markdown report content
        self.sample_report = """# AI Development Impact Analysis Report

**Generated:** 2025-08-20 18:59:01  
**Analysis Type:** Single Scenario  
**Scenarios:** moderate_enterprise  
**Report ID:** `a1b2c3d4`  

## Scenario Analysis: moderate_enterprise

### Executive Summary

| Metric | Value | Trend |
|--------|-------|-------|
| **Team Size** | 50 developers | |
| **Peak Adoption Rate** | 84.5% | |
| **Net Present Value (NPV)** | $9,560,070 | |
| **Return on Investment (ROI)** | 387.9% | |
| **Breakeven Point** | Month 2 | |

### Reproducibility

**Command used:**
```bash
python run_analysis.py moderate_enterprise
```

**Complete scenario configuration used:**

**moderate_enterprise:**
```yaml
adoption:
  scenario: grassroots
baseline:
  profile: enterprise
costs:
  scenario: enterprise
description: 50-person enterprise with balanced adoption approach
impact:
  scenario: moderate
name: Moderate Enterprise
timeframe_months: 36
```

**Resolved parameter values used in calculations:**

```yaml
baseline_metrics:
  team_size: 50
  junior_ratio: 0.3
  weighted_avg_flc: 182000.0
final_metrics:
  npv: 9560070.124960652
  roi_percent: 387.89591216872265
  breakeven_month: 2
  peak_adoption: 0.8447857870220122
```
"""
    
    def test_extract_analysis_type(self):
        """Test extraction of analysis type"""
        result = self.extractor._extract_analysis_type(self.sample_report)
        self.assertEqual(result, "Single Scenario")
    
    def test_extract_scenario_names(self):
        """Test extraction of scenario names"""
        result = self.extractor._extract_scenario_names(self.sample_report)
        self.assertEqual(result, ["moderate_enterprise"])
    
    def test_extract_generation_date(self):
        """Test extraction of generation date"""
        result = self.extractor._extract_generation_date(self.sample_report)
        self.assertEqual(result, "2025-08-20 18:59:01")
    
    def test_extract_command_used(self):
        """Test extraction of command used"""
        result = self.extractor._extract_command_used(self.sample_report)
        self.assertEqual(result, "python run_analysis.py moderate_enterprise")
    
    def test_extract_scenario_configs(self):
        """Test extraction of scenario configurations"""
        result = self.extractor._extract_scenario_configs(self.sample_report)
        
        self.assertIn('moderate_enterprise', result)
        config = result['moderate_enterprise']
        self.assertEqual(config['adoption']['scenario'], 'grassroots')
        self.assertEqual(config['baseline']['profile'], 'enterprise')
        self.assertEqual(config['timeframe_months'], 36)
    
    def test_extract_resolved_parameters(self):
        """Test extraction of resolved parameters"""
        result = self.extractor._extract_resolved_parameters(self.sample_report)
        
        self.assertIn('baseline_metrics', result)
        self.assertIn('final_metrics', result)
        self.assertEqual(result['baseline_metrics']['team_size'], 50)
        self.assertEqual(result['final_metrics']['breakeven_month'], 2)
    
    def test_extract_original_results(self):
        """Test extraction of original results for validation"""
        result = self.extractor._extract_original_results(self.sample_report)
        
        self.assertIn('npv', result)
        self.assertIn('roi_percent', result)
        self.assertIn('breakeven_month', result)
        self.assertIn('peak_adoption', result)
        
        self.assertEqual(result['npv'], 9560070)
        self.assertEqual(result['roi_percent'], 387.9)
        self.assertEqual(result['breakeven_month'], 2)
        self.assertEqual(result['peak_adoption'], 0.845)
    
    def test_extract_from_report_file(self):
        """Test extracting metadata from a real report file"""
        # Create temporary file with sample content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_report)
            temp_path = f.name
        
        try:
            metadata = self.extractor.extract_from_report(temp_path)
            
            self.assertIsInstance(metadata, ReproductionMetadata)
            self.assertEqual(metadata.analysis_type, "Single Scenario")
            self.assertEqual(metadata.scenario_names, ["moderate_enterprise"])
            self.assertEqual(metadata.command_used, "python run_analysis.py moderate_enterprise")
            self.assertIn('moderate_enterprise', metadata.scenario_configs)
            self.assertTrue(len(metadata.report_checksum) > 0)
            
        finally:
            os.unlink(temp_path)


class TestScenarioBuilder(unittest.TestCase):
    """Test scenario file building from metadata"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.builder = ScenarioBuilder()
        
        # Sample metadata
        self.sample_metadata = ReproductionMetadata(
            command_used="python run_analysis.py test_scenario",
            analysis_type="Single Scenario",
            scenario_names=["test_scenario"],
            generation_date="2025-08-20 18:59:01",
            scenario_configs={
                "test_scenario": {
                    "name": "Test Scenario",
                    "baseline": {"profile": "startup"},
                    "adoption": {"scenario": "organic"},
                    "impact": {"scenario": "moderate"},
                    "costs": {"scenario": "startup"},
                    "timeframe_months": 24
                }
            },
            resolved_parameters={},
            original_results={},
            report_checksum="abc123"
        )
    
    def test_create_temporary_scenario_file(self):
        """Test creation of temporary scenario file"""
        try:
            temp_file = self.builder.create_temporary_scenario_file(self.sample_metadata)
            
            # Verify file exists
            self.assertTrue(os.path.exists(temp_file))
            
            # Verify content
            with open(temp_file, 'r') as f:
                content = yaml.safe_load(f)
            
            self.assertIn('test_scenario', content)
            self.assertEqual(content['test_scenario']['name'], "Test Scenario")
            self.assertEqual(content['test_scenario']['timeframe_months'], 24)
            
        finally:
            self.builder.cleanup()
    
    def test_cleanup(self):
        """Test cleanup of temporary files"""
        temp_file = self.builder.create_temporary_scenario_file(self.sample_metadata)
        
        # Verify file exists before cleanup
        self.assertTrue(os.path.exists(temp_file))
        
        # Cleanup
        self.builder.cleanup()
        
        # Verify file is removed
        self.assertFalse(os.path.exists(temp_file))


class TestReproductionEngine(unittest.TestCase):
    """Test the main reproduction engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ReproductionEngine()
        
        # Create a sample report file
        self.sample_report_content = """# AI Development Impact Analysis Report

**Generated:** 2025-08-20 18:59:01  
**Analysis Type:** Single Scenario  
**Scenarios:** conservative_startup

### Executive Summary

| Metric | Value |
|--------|-------|
| **Net Present Value (NPV)** | $1,000,000 |
| **Return on Investment (ROI)** | 200.0% |
| **Breakeven Point** | Month 6 |
| **Peak Adoption Rate** | 75.0% |

### Reproducibility

**Command used:**
```bash
python run_analysis.py conservative_startup
```

**Complete scenario configuration used:**

**conservative_startup:**
```yaml
name: Conservative Startup
baseline:
  profile: startup
adoption:
  scenario: organic
impact:
  scenario: conservative
costs:
  scenario: startup
timeframe_months: 24
```

**Resolved parameter values used in calculations:**

```yaml
baseline_metrics:
  team_size: 10
final_metrics:
  npv: 1000000.0
  roi_percent: 200.0
  breakeven_month: 6
  peak_adoption: 0.75
```
"""
        
        # Create temporary report file
        self.temp_report = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_report.write(self.sample_report_content)
        self.temp_report.close()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_report.name):
            os.unlink(self.temp_report.name)
    
    @patch('src.reproducibility.reproduction_engine.AIImpactModel')
    def test_extract_key_metrics(self, mock_model_class):
        """Test extraction of key metrics from scenario results"""
        
        # Mock scenario results
        mock_results = {
            'npv': 1000000.0,
            'roi_percent': 200.0,
            'breakeven_month': 6,
            'peak_adoption': 0.75,
            'total_cost_3y': 500000.0,
            'total_value_3y': 1500000.0,
            'annual_cost_per_dev': 25000.0,
            'annual_value_per_dev': 50000.0
        }
        
        extracted = self.engine._extract_key_metrics(mock_results)
        
        self.assertEqual(extracted['npv'], 1000000.0)
        self.assertEqual(extracted['roi_percent'], 200.0)
        self.assertEqual(extracted['breakeven_month'], 6)
        self.assertEqual(extracted['peak_adoption'], 0.75)
    
    def test_validate_results_matching(self):
        """Test validation of matching results"""
        
        original = {
            'npv': 1000000.0,
            'roi_percent': 200.0,
            'breakeven_month': 6,
            'peak_adoption': 0.75
        }
        
        reproduced = {
            'npv': 1001000.0,  # 0.1% difference
            'roi_percent': 200.5,  # 0.25% difference
            'breakeven_month': 6,
            'peak_adoption': 0.751  # 0.13% difference
        }
        
        result = self.engine._validate_results(original, reproduced, tolerance=0.01)
        
        self.assertTrue(result['success'])
        self.assertGreater(result['confidence_score'], 0.95)
    
    def test_validate_results_not_matching(self):
        """Test validation of non-matching results"""
        
        original = {
            'npv': 1000000.0,
            'roi_percent': 200.0,
            'peak_adoption': 0.75
        }
        
        reproduced = {
            'npv': 1100000.0,  # 10% difference - too large
            'roi_percent': 220.0,  # 10% difference - too large
            'peak_adoption': 0.85  # 13% difference - too large
        }
        
        result = self.engine._validate_results(original, reproduced, tolerance=0.01)
        
        self.assertFalse(result['success'])
        self.assertLess(result['confidence_score'], 0.95)
        self.assertTrue(len(result['differences']) > 0)
    
    def test_validate_results_with_scenarios(self):
        """Test validation with multiple scenarios"""
        
        original = {
            'scenario1': {'npv': 1000000.0, 'roi_percent': 200.0},
            'scenario2': {'npv': 2000000.0, 'roi_percent': 300.0}
        }
        
        reproduced = {
            'scenario1': {'npv': 1001000.0, 'roi_percent': 200.5},
            'scenario2': {'npv': 2002000.0, 'roi_percent': 300.5}
        }
        
        result = self.engine._validate_results(original, reproduced, tolerance=0.01)
        
        self.assertTrue(result['success'])
        self.assertGreater(result['confidence_score'], 0.95)
    
    @patch('src.reproducibility.reproduction_engine.AIImpactModel')
    def test_reproduce_from_report_success(self, mock_model_class):
        """Test successful reproduction from report"""
        
        # Mock the model and its methods
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        
        # Mock scenario results
        mock_model.run_scenario.return_value = {
            'npv': 1000000.0,
            'roi_percent': 200.0,
            'breakeven_month': 6,
            'peak_adoption': 0.75,
            'total_cost_3y': 500000.0,
            'total_value_3y': 1500000.0,
            'annual_cost_per_dev': 25000.0,
            'annual_value_per_dev': 50000.0
        }
        
        result = self.engine.reproduce_from_report(self.temp_report.name, tolerance=0.01)
        
        self.assertIsInstance(result, ReproductionResult)
        self.assertTrue(result.success)
        self.assertGreater(result.confidence_score, 0.90)
        self.assertIsNotNone(result.reproduction_metadata)
    
    def test_reproduce_from_nonexistent_file(self):
        """Test reproduction from non-existent file"""
        
        result = self.engine.reproduce_from_report("nonexistent.md")
        
        self.assertFalse(result.success)
        self.assertEqual(result.confidence_score, 0.0)
        self.assertIn('error', result.differences)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for reproduction scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ReproductionEngine()
    
    @patch('src.reproducibility.reproduction_engine.AIImpactModel')
    def test_single_scenario_reproduction(self, mock_model_class):
        """Test reproduction of single scenario analysis"""
        
        # Create sample report
        report_content = """# AI Development Impact Analysis Report

**Generated:** 2025-08-20 18:59:01  
**Analysis Type:** Single Scenario  
**Scenarios:** test_scenario

| **Net Present Value (NPV)** | $1,500,000 |
| **Return on Investment (ROI)** | 250.0% |
| **Peak Adoption Rate** | 80.0% |

**Complete scenario configuration used:**

**test_scenario:**
```yaml
name: Test Scenario
baseline:
  profile: startup
timeframe_months: 24
```

**Resolved parameter values used in calculations:**
```yaml
final_metrics:
  npv: 1500000.0
  roi_percent: 250.0
  peak_adoption: 0.8
```
"""
        
        # Mock model behavior
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        mock_model.run_scenario.return_value = {
            'npv': 1500000.0,
            'roi_percent': 250.0,
            'peak_adoption': 0.8,
            'total_cost_3y': 600000.0,
            'total_value_3y': 2100000.0,
            'breakeven_month': None,
            'annual_cost_per_dev': 30000.0,
            'annual_value_per_dev': 75000.0
        }
        
        # Create temporary report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(report_content)
            temp_path = f.name
        
        try:
            result = self.engine.reproduce_from_report(temp_path)
            
            self.assertTrue(result.success)
            self.assertGreater(result.confidence_score, 0.90)
            self.assertEqual(result.reproduction_metadata.analysis_type, "Single Scenario")
            self.assertEqual(result.reproduction_metadata.scenario_names, ["test_scenario"])
            
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()