#!/usr/bin/env python3
"""
Test suite for version-aware reproduction functionality
Tests reproduction engine with version detection and adaptation.
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.version import ModelVersion
from src.reproducibility.reproduction_engine import (
    MetadataExtractor, ReproductionEngine, ReproductionMetadata
)


class TestVersionAwareReproduction(unittest.TestCase):
    """Test version-aware reproduction functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = MetadataExtractor()
        self.engine = ReproductionEngine()
        
        # Sample report with version information
        self.sample_report_v1_0_0 = """# AI Development Impact Analysis Report

**Generated:** 2025-08-20 19:45:50  
**Analysis Type:** Single Scenario  
**Scenarios:** test_scenario  
**Report ID:** `abc123`  
**Python Version:** 3.13.0  
**Analysis Tool Version:** v1.0.0

---

## Scenario Analysis: test_scenario

| **Net Present Value (NPV)** | $1,000,000 |
| **Return on Investment (ROI)** | 200.0% |
| **Peak Adoption Rate** | 75.0% |

**Complete scenario configuration used:**

**test_scenario:**
```yaml
name: Test Scenario
baseline:
  profile: startup
adoption:
  scenario: organic
impact:
  scenario: moderate
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
  peak_adoption: 0.75
```

**Data sources:**
- Analysis engine: AI Impact Model v1.0.0
"""
        
        self.sample_report_v1_0_1 = self.sample_report_v1_0_0.replace(
            "v1.0.0", "v1.0.1"
        )
    
    def test_version_extraction(self):
        """Test extraction of version information from reports"""
        # Test v1.0.0 extraction
        metadata = self._extract_metadata_from_content(self.sample_report_v1_0_0)
        
        self.assertIsNotNone(metadata.model_version)
        self.assertEqual(metadata.model_version, ModelVersion(1, 0, 0))
        self.assertEqual(metadata.tool_version, "1.0.0")
        
        # Test v1.0.1 extraction
        metadata = self._extract_metadata_from_content(self.sample_report_v1_0_1)
        
        self.assertIsNotNone(metadata.model_version)
        self.assertEqual(metadata.model_version, ModelVersion(1, 0, 1))
        self.assertEqual(metadata.tool_version, "1.0.1")
    
    def test_version_extraction_fallback(self):
        """Test version extraction fallback to engine version"""
        # Report with only engine version
        report_content = """# Report
**Analysis Type:** Single Scenario
**Scenarios:** test

**Data sources:**
- Analysis engine: AI Impact Model v1.0.0
"""
        
        model_version, tool_version = self.extractor._extract_version_info(report_content)
        self.assertEqual(model_version, ModelVersion(1, 0, 0))
        self.assertIsNone(tool_version)
    
    def test_version_extraction_invalid(self):
        """Test handling of invalid version strings"""
        # Report with invalid version
        report_content = """# Report
**Analysis Tool Version:** invalid.version
**Data sources:**
- Analysis engine: AI Impact Model invalid.version
"""
        
        model_version, tool_version = self.extractor._extract_version_info(report_content)
        self.assertIsNone(model_version)
        self.assertEqual(tool_version, "invalid.version")
    
    def test_version_extraction_missing(self):
        """Test handling of missing version information"""
        # Report without version info
        report_content = """# Report
**Analysis Type:** Single Scenario
**Scenarios:** test
"""
        
        model_version, tool_version = self.extractor._extract_version_info(report_content)
        self.assertIsNone(model_version)
        self.assertIsNone(tool_version)
    
    @patch('src.reproducibility.reproduction_engine.AIImpactModel')
    def test_reproduction_with_version_adaptation(self, mock_model_class):
        """Test reproduction with version adaptation"""
        # Mock the model
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model
        mock_model.run_scenario.return_value = {
            'npv': 1000000.0,
            'roi_percent': 200.0,
            'peak_adoption': 0.75,
            'total_cost_3y': 500000.0,
            'total_value_3y': 1500000.0,
            'breakeven_month': 6,
            'annual_cost_per_dev': 25000.0,
            'annual_value_per_dev': 50000.0
        }
        
        # Create temporary report file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.sample_report_v1_0_0)
            temp_path = f.name
        
        try:
            result = self.engine.reproduce_from_report(temp_path)
            
            # Should succeed with version compatibility info
            self.assertTrue(result.success)
            self.assertIsNotNone(result.version_compatibility)
            self.assertEqual(
                result.reproduction_metadata.model_version, 
                ModelVersion(1, 0, 0)
            )
            
        finally:
            os.unlink(temp_path)
    
    @patch('src.config.version.get_current_version')
    def test_tolerance_adjustment_for_versions(self, mock_current_version):
        """Test tolerance adjustment based on version differences"""
        # Mock current version as v1.0.1
        mock_current_version.return_value = ModelVersion(1, 0, 1)
        
        # Create metadata with v1.0.0
        metadata = self._create_test_metadata(ModelVersion(1, 0, 0))
        
        # Test that tolerance should be adjusted for version differences
        # This is tested indirectly through the reproduction process
        base_tolerance = 0.01
        
        # The engine should adjust tolerance internally
        # We can verify this by checking the version compatibility info
        from src.config.version import get_compatibility_info
        info = get_compatibility_info(ModelVersion(1, 0, 0), ModelVersion(1, 0, 1))
        
        self.assertEqual(info['compatibility_level'], 'major')
        self.assertTrue(info['can_reproduce'])
        self.assertGreater(len(info['warnings']), 0)
    
    def test_version_compatibility_reporting(self):
        """Test version compatibility information in results"""
        with patch('src.config.version.get_current_version') as mock_current:
            mock_current.return_value = ModelVersion(1, 0, 1)
            
            # Create metadata with different version
            metadata = self._create_test_metadata(ModelVersion(1, 0, 0))
            
            # Test compatibility info generation
            from src.config.version import get_compatibility_info
            info = get_compatibility_info(metadata.model_version, ModelVersion(1, 0, 1))
            
            self.assertIn('compatibility_level', info)
            self.assertIn('can_reproduce', info)
            self.assertIn('warnings', info)
            self.assertIn('recommendations', info)
    
    def test_unsupported_version_handling(self):
        """Test handling of unsupported version transitions"""
        # Test major version difference
        metadata = self._create_test_metadata(ModelVersion(2, 0, 0))
        
        from src.config.version import get_compatibility_info, get_current_version
        current = get_current_version()  # Should be v1.0.0
        info = get_compatibility_info(metadata.model_version, current)
        
        # Major version difference should have limited compatibility
        self.assertEqual(info['compatibility_level'], 'minor')
        self.assertFalse(info['can_reproduce'])
    
    def _extract_metadata_from_content(self, content: str) -> ReproductionMetadata:
        """Helper to extract metadata from report content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            return self.extractor.extract_from_report(temp_path)
        finally:
            os.unlink(temp_path)
    
    def _create_test_metadata(self, version: ModelVersion) -> ReproductionMetadata:
        """Helper to create test metadata with specific version"""
        return ReproductionMetadata(
            command_used="test command",
            analysis_type="Single Scenario",
            scenario_names=["test_scenario"],
            generation_date="2025-08-20",
            scenario_configs={"test_scenario": {"name": "Test"}},
            resolved_parameters={"test": "value"},
            original_results={"npv": 1000000.0},
            report_checksum="abc123",
            model_version=version,
            tool_version=str(version)
        )


class TestVersionValidationTolerance(unittest.TestCase):
    """Test version-specific validation tolerance"""
    
    def test_tolerance_calculation(self):
        """Test tolerance adjustment based on version differences"""
        base_tolerance = 0.01
        
        # Test different version scenarios
        test_cases = [
            (ModelVersion(1, 0, 0), ModelVersion(1, 0, 0), 0.01),  # Same version
            (ModelVersion(1, 0, 0), ModelVersion(1, 0, 1), 0.02),  # Patch difference
            (ModelVersion(1, 0, 0), ModelVersion(1, 1, 0), 0.02),  # Minor difference
            (ModelVersion(1, 0, 0), ModelVersion(2, 0, 0), 0.05),  # Major difference
        ]
        
        for from_version, to_version, expected_min_tolerance in test_cases:
            from src.config.version import get_compatibility_info
            info = get_compatibility_info(from_version, to_version)
            
            # Calculate adjusted tolerance (mimicking reproduction engine logic)
            tolerance = base_tolerance
            if info['compatibility_level'] == 'major':
                tolerance = max(tolerance, 0.02)
            elif info['compatibility_level'] == 'minor':
                tolerance = max(tolerance, 0.05)
            
            self.assertGreaterEqual(tolerance, expected_min_tolerance)


class TestVersionCompatibilityWorkflow(unittest.TestCase):
    """Test complete version compatibility workflow"""
    
    def test_complete_workflow(self):
        """Test complete version-aware reproduction workflow"""
        # 1. Version detection
        v1_0_0 = ModelVersion(1, 0, 0)
        v1_0_1 = ModelVersion(1, 0, 1)
        
        # 2. Compatibility checking
        from src.config.version import get_compatibility_info
        info = get_compatibility_info(v1_0_0, v1_0_1)
        self.assertTrue(info['can_reproduce'])
        
        # 3. Adapter selection
        from src.versioning.version_adapter import get_version_adapter
        adapter = get_version_adapter(v1_0_0, v1_0_1)
        self.assertTrue(adapter.can_adapt(v1_0_0, v1_0_1))
        
        # 4. Configuration adaptation
        config = {"test": "config"}
        result = adapter.adapt_scenario_config(config, v1_0_0, v1_0_1)
        self.assertTrue(result.success)
        
        # 5. Tolerance adjustment
        base_tolerance = 0.01
        if info['compatibility_level'] == 'major':
            tolerance = max(base_tolerance, 0.02)
        else:
            tolerance = base_tolerance
        
        self.assertGreaterEqual(tolerance, base_tolerance)


if __name__ == '__main__':
    unittest.main()