#!/usr/bin/env python3
"""
Test suite for version management system
Tests version configuration, compatibility checking, and adaptation.
"""

import os
import sys
import unittest
import tempfile
import re
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.version import (
    ModelVersion, get_current_version, get_current_version_string,
    is_version_supported, get_compatibility_info, validate_version_string,
    CURRENT_VERSION, SUPPORTED_VERSIONS
)
from src.versioning.version_adapter import (
    V1ToV1Adapter, IdentityAdapter, UnsupportedAdapter,
    get_version_adapter, adapt_scenario_config, adapt_resolved_parameters
)


class TestModelVersion(unittest.TestCase):
    """Test ModelVersion class functionality"""
    
    def test_version_creation(self):
        """Test creating ModelVersion objects"""
        v1 = ModelVersion(1, 0, 0)
        self.assertEqual(v1.major, 1)
        self.assertEqual(v1.minor, 0)
        self.assertEqual(v1.patch, 0)
    
    def test_version_string_representation(self):
        """Test string representation of versions"""
        v1 = ModelVersion(1, 2, 3)
        self.assertEqual(str(v1), "1.2.3")
        self.assertEqual(repr(v1), "ModelVersion(1, 2, 3)")
    
    def test_version_comparison(self):
        """Test version comparison operators"""
        v1_0_0 = ModelVersion(1, 0, 0)
        v1_0_1 = ModelVersion(1, 0, 1)
        v1_1_0 = ModelVersion(1, 1, 0)
        v2_0_0 = ModelVersion(2, 0, 0)
        
        # Equality
        self.assertEqual(v1_0_0, ModelVersion(1, 0, 0))
        self.assertNotEqual(v1_0_0, v1_0_1)
        
        # Less than
        self.assertTrue(v1_0_0 < v1_0_1)
        self.assertTrue(v1_0_0 < v1_1_0)
        self.assertTrue(v1_0_0 < v2_0_0)
        self.assertFalse(v1_0_1 < v1_0_0)
        
        # Greater than
        self.assertTrue(v2_0_0 > v1_0_0)
        self.assertTrue(v1_1_0 > v1_0_0)
        self.assertFalse(v1_0_0 > v1_0_1)
    
    def test_version_compatibility(self):
        """Test version compatibility checking"""
        v1_0_0 = ModelVersion(1, 0, 0)
        v1_0_1 = ModelVersion(1, 0, 1)
        v1_1_0 = ModelVersion(1, 1, 0)
        v2_0_0 = ModelVersion(2, 0, 0)
        
        # Same major version = compatible
        self.assertTrue(v1_0_0.is_compatible_with(v1_0_1))
        self.assertTrue(v1_0_0.is_compatible_with(v1_1_0))
        
        # Different major version = incompatible
        self.assertFalse(v1_0_0.is_compatible_with(v2_0_0))
    
    def test_compatibility_levels(self):
        """Test compatibility level classification"""
        v1_0_0 = ModelVersion(1, 0, 0)
        v1_0_1 = ModelVersion(1, 0, 1)
        v1_1_0 = ModelVersion(1, 1, 0)
        v2_0_0 = ModelVersion(2, 0, 0)
        v3_0_0 = ModelVersion(3, 0, 0)
        
        # Full compatibility (same version)
        self.assertEqual(v1_0_0.compatibility_level(v1_0_0), 'full')
        
        # Major compatibility (same major version)
        self.assertEqual(v1_0_0.compatibility_level(v1_0_1), 'major')
        self.assertEqual(v1_0_0.compatibility_level(v1_1_0), 'major')
        
        # Minor compatibility (1 major version difference)
        self.assertEqual(v1_0_0.compatibility_level(v2_0_0), 'minor')
        
        # No compatibility (>1 major version difference)
        self.assertEqual(v1_0_0.compatibility_level(v3_0_0), 'none')
    
    def test_from_string_parsing(self):
        """Test parsing version strings"""
        # Valid formats
        v1 = ModelVersion.from_string("1.0.0")
        self.assertEqual(v1, ModelVersion(1, 0, 0))
        
        v2 = ModelVersion.from_string("v2.3.4")
        self.assertEqual(v2, ModelVersion(2, 3, 4))
        
        v3 = ModelVersion.from_string("10.20.30")
        self.assertEqual(v3, ModelVersion(10, 20, 30))
        
        # Invalid formats
        with self.assertRaises(ValueError):
            ModelVersion.from_string("1.0")
        
        with self.assertRaises(ValueError):
            ModelVersion.from_string("invalid")
        
        with self.assertRaises(ValueError):
            ModelVersion.from_string("1.0.0.0")


class TestVersionConfiguration(unittest.TestCase):
    """Test version configuration functions"""
    
    def test_current_version(self):
        """Test current version retrieval"""
        current = get_current_version()
        self.assertIsInstance(current, ModelVersion)
        self.assertEqual(current, CURRENT_VERSION)
        
        current_str = get_current_version_string()
        self.assertEqual(current_str, str(CURRENT_VERSION))
    
    def test_supported_versions(self):
        """Test supported versions checking"""
        current = get_current_version()
        self.assertTrue(is_version_supported(current))
        
        # Test unsupported version
        unsupported = ModelVersion(99, 99, 99)
        self.assertFalse(is_version_supported(unsupported))
    
    def test_compatibility_info(self):
        """Test compatibility information generation"""
        v1_0_0 = ModelVersion(1, 0, 0)
        v1_0_1 = ModelVersion(1, 0, 1)
        v2_0_0 = ModelVersion(2, 0, 0)
        
        # Same version
        info = get_compatibility_info(v1_0_0, v1_0_0)
        self.assertEqual(info['compatibility_level'], 'full')
        self.assertTrue(info['can_reproduce'])
        self.assertEqual(len(info['warnings']), 0)
        
        # Minor difference
        info = get_compatibility_info(v1_0_0, v1_0_1)
        self.assertEqual(info['compatibility_level'], 'major')
        self.assertTrue(info['can_reproduce'])
        self.assertGreater(len(info['warnings']), 0)
        
        # Major difference
        info = get_compatibility_info(v1_0_0, v2_0_0)
        self.assertEqual(info['compatibility_level'], 'minor')
        self.assertFalse(info['can_reproduce'])
    
    def test_validate_version_string(self):
        """Test version string validation"""
        self.assertTrue(validate_version_string("1.0.0"))
        self.assertTrue(validate_version_string("v2.3.4"))
        self.assertFalse(validate_version_string("invalid"))
        self.assertFalse(validate_version_string("1.0"))


class TestVersionAdapters(unittest.TestCase):
    """Test version adapter functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_config = {
            "name": "Test Scenario",
            "baseline": {"profile": "startup"},
            "adoption": {"scenario": "organic"},
            "impact": {"scenario": "moderate"},
            "costs": {"scenario": "startup"},
            "timeframe_months": 24
        }
        
        self.sample_parameters = {
            "baseline_metrics": {"team_size": 10},
            "final_metrics": {"npv": 1000000.0}
        }
    
    def test_identity_adapter(self):
        """Test identity adapter for same versions"""
        adapter = IdentityAdapter()
        v1_0_0 = ModelVersion(1, 0, 0)
        
        self.assertTrue(adapter.can_adapt(v1_0_0, v1_0_0))
        
        result = adapter.adapt_scenario_config(self.sample_config, v1_0_0, v1_0_0)
        self.assertTrue(result.success)
        self.assertEqual(result.adapted_config, self.sample_config)
        self.assertEqual(len(result.errors), 0)
    
    def test_v1_to_v1_adapter(self):
        """Test v1.x to v1.x adapter"""
        adapter = V1ToV1Adapter()
        v1_0_0 = ModelVersion(1, 0, 0)
        v1_0_1 = ModelVersion(1, 0, 1)
        v1_1_0 = ModelVersion(1, 1, 0)
        v2_0_0 = ModelVersion(2, 0, 0)
        
        # Can adapt within v1.x
        self.assertTrue(adapter.can_adapt(v1_0_0, v1_0_1))
        self.assertTrue(adapter.can_adapt(v1_0_0, v1_1_0))
        
        # Cannot adapt to v2.x
        self.assertFalse(adapter.can_adapt(v1_0_0, v2_0_0))
        
        # Test adaptation
        result = adapter.adapt_scenario_config(self.sample_config, v1_0_0, v1_0_1)
        self.assertTrue(result.success)
        self.assertEqual(result.adapted_config, self.sample_config)
        
        # Minor version change should add warnings
        result = adapter.adapt_scenario_config(self.sample_config, v1_0_0, v1_1_0)
        self.assertTrue(result.success)
        self.assertGreater(len(result.warnings), 0)
    
    def test_unsupported_adapter(self):
        """Test unsupported adapter"""
        adapter = UnsupportedAdapter()
        v1_0_0 = ModelVersion(1, 0, 0)
        v2_0_0 = ModelVersion(2, 0, 0)
        
        self.assertTrue(adapter.can_adapt(v1_0_0, v2_0_0))  # Fallback
        
        result = adapter.adapt_scenario_config(self.sample_config, v1_0_0, v2_0_0)
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
    
    def test_adapter_registry(self):
        """Test adapter registry functionality"""
        v1_0_0 = ModelVersion(1, 0, 0)
        v1_0_1 = ModelVersion(1, 0, 1)
        v2_0_0 = ModelVersion(2, 0, 0)
        
        # Should get identity adapter for same versions
        adapter = get_version_adapter(v1_0_0, v1_0_0)
        self.assertIsInstance(adapter, IdentityAdapter)
        
        # Should get v1 adapter for v1.x transitions
        adapter = get_version_adapter(v1_0_0, v1_0_1)
        self.assertIsInstance(adapter, V1ToV1Adapter)
        
        # Should get unsupported adapter for major transitions
        adapter = get_version_adapter(v1_0_0, v2_0_0)
        self.assertIsInstance(adapter, UnsupportedAdapter)
    
    def test_convenience_functions(self):
        """Test convenience adaptation functions"""
        v1_0_0 = ModelVersion(1, 0, 0)
        v1_0_1 = ModelVersion(1, 0, 1)
        
        # Test scenario config adaptation
        result = adapt_scenario_config(self.sample_config, v1_0_0, v1_0_1)
        self.assertTrue(result.success)
        
        # Test parameter adaptation
        result = adapt_resolved_parameters(self.sample_parameters, v1_0_0, v1_0_1)
        self.assertTrue(result.success)


class TestVersionIntegration(unittest.TestCase):
    """Integration tests for version management"""
    
    def test_report_version_extraction_simulation(self):
        """Test version extraction from simulated report content"""
        # Simulate report content with version information
        report_content = """# AI Development Impact Analysis Report

**Generated:** 2025-08-20 19:45:50  
**Analysis Type:** Single Scenario  
**Scenarios:** test_scenario  
**Report ID:** `abc123`  
**Python Version:** 3.13.0  
**Analysis Tool Version:** v1.0.0

---

Content here...

**Data sources:**
- Analysis engine: AI Impact Model v1.0.0
"""
        
        # Test version extraction patterns
        tool_match = re.search(r'\*\*Analysis Tool Version:\*\* v?([\d.]+)', report_content)
        self.assertIsNotNone(tool_match)
        self.assertEqual(tool_match.group(1), "1.0.0")
        
        engine_match = re.search(r'Analysis engine: AI Impact Model v?([\d.]+)', report_content)
        self.assertIsNotNone(engine_match)
        self.assertEqual(engine_match.group(1), "1.0.0")
    
    def test_version_tolerance_adjustment(self):
        """Test tolerance adjustment based on version compatibility"""
        base_tolerance = 0.01
        
        # Same version - no adjustment
        v1_0_0 = ModelVersion(1, 0, 0)
        info = get_compatibility_info(v1_0_0, v1_0_0)
        if info['compatibility_level'] == 'full':
            tolerance = base_tolerance
        self.assertEqual(tolerance, 0.01)
        
        # Minor version difference - slight adjustment
        v1_0_1 = ModelVersion(1, 0, 1)
        info = get_compatibility_info(v1_0_0, v1_0_1)
        if info['compatibility_level'] == 'major':
            tolerance = max(base_tolerance, 0.02)
        self.assertEqual(tolerance, 0.02)
    
    def test_version_workflow_simulation(self):
        """Test complete version handling workflow"""
        v1_0_0 = ModelVersion(1, 0, 0)
        v1_0_1 = ModelVersion(1, 0, 1)
        
        # 1. Check compatibility
        info = get_compatibility_info(v1_0_0, v1_0_1)
        self.assertTrue(info['can_reproduce'])
        
        # 2. Get adapter
        adapter = get_version_adapter(v1_0_0, v1_0_1)
        self.assertTrue(adapter.can_adapt(v1_0_0, v1_0_1))
        
        # 3. Adapt configuration
        config = {"test": "value"}
        result = adapter.adapt_scenario_config(config, v1_0_0, v1_0_1)
        self.assertTrue(result.success)
        
        # 4. Check for warnings
        if result.warnings:
            print(f"Adaptation warnings: {result.warnings}")


if __name__ == '__main__':
    unittest.main()