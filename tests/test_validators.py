#!/usr/bin/env python3
"""
Test suite for the validation framework
Tests validation rules, tolerance configurations, and scenario validation.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reproducibility.validators import (
    ValidationRule, ValidationConfig, NumericalValidator, AbsoluteValidator,
    ExactValidator, ScenarioValidator, MultiScenarioValidator, create_validation_config
)


class TestValidationRule(unittest.TestCase):
    """Test validation rule configuration"""
    
    def test_validation_rule_creation(self):
        """Test creation of validation rules"""
        rule = ValidationRule(
            metric_name="npv",
            tolerance=0.01,
            tolerance_type="percentage",
            required=True,
            description="Net Present Value"
        )
        
        self.assertEqual(rule.metric_name, "npv")
        self.assertEqual(rule.tolerance, 0.01)
        self.assertEqual(rule.tolerance_type, "percentage")
        self.assertTrue(rule.required)
        self.assertEqual(rule.description, "Net Present Value")


class TestValidationConfig(unittest.TestCase):
    """Test validation configuration"""
    
    def test_default_config(self):
        """Test default validation configuration"""
        config = ValidationConfig()
        
        self.assertEqual(config.default_tolerance, 0.01)
        self.assertEqual(config.default_tolerance_type, 'percentage')
        self.assertFalse(config.ignore_missing_metrics)
        self.assertTrue(config.ignore_none_values)
        self.assertEqual(config.minimum_confidence_score, 0.95)
        self.assertEqual(config.custom_rules, {})
    
    def test_custom_config(self):
        """Test custom validation configuration"""
        custom_rules = {
            "npv": ValidationRule("npv", 0.02, "percentage", True, "NPV rule")
        }
        
        config = ValidationConfig(
            default_tolerance=0.05,
            minimum_confidence_score=0.90,
            custom_rules=custom_rules
        )
        
        self.assertEqual(config.default_tolerance, 0.05)
        self.assertEqual(config.minimum_confidence_score, 0.90)
        self.assertIn("npv", config.custom_rules)


class TestNumericalValidator(unittest.TestCase):
    """Test numerical validation with tolerances"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = NumericalValidator()
    
    def test_exact_match(self):
        """Test validation of exact matches"""
        success, message = self.validator.validate(1000.0, 1000.0, 0.01)
        
        self.assertTrue(success)
        self.assertIn("Within tolerance", message)
    
    def test_within_tolerance(self):
        """Test validation within tolerance"""
        # 0.5% difference, tolerance is 1%
        success, message = self.validator.validate(1000.0, 1005.0, 0.01)
        
        self.assertTrue(success)
        self.assertIn("Within tolerance", message)
    
    def test_exceeds_tolerance(self):
        """Test validation exceeding tolerance"""
        # 5% difference, tolerance is 1%
        success, message = self.validator.validate(1000.0, 1050.0, 0.01)
        
        self.assertFalse(success)
        self.assertIn("Exceeds tolerance", message)
    
    def test_zero_values(self):
        """Test validation of zero values"""
        # Original is 0, reproduced is small value within tolerance
        success, message = self.validator.validate(0.0, 0.005, 0.01)
        
        self.assertTrue(success)
        self.assertIn("approximately zero", message)
        
        # Original is 0, reproduced exceeds tolerance
        success, message = self.validator.validate(0.0, 0.02, 0.01)
        
        self.assertFalse(success)
        self.assertIn("Original is 0", message)
    
    def test_none_values(self):
        """Test validation of None values"""
        # Both None
        success, message = self.validator.validate(None, None, 0.01)
        
        self.assertTrue(success)
        self.assertIn("Both values are None", message)
        
        # One None
        success, message = self.validator.validate(1000.0, None, 0.01)
        
        self.assertFalse(success)
        self.assertIn("One value is None", message)
    
    def test_non_numeric_values(self):
        """Test validation of non-numeric values"""
        success, message = self.validator.validate("not_a_number", 1000.0, 0.01)
        
        self.assertFalse(success)
        self.assertIn("Cannot convert to numbers", message)


class TestAbsoluteValidator(unittest.TestCase):
    """Test absolute difference validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = AbsoluteValidator()
    
    def test_within_absolute_tolerance(self):
        """Test validation within absolute tolerance"""
        success, message = self.validator.validate(1000.0, 1005.0, 10.0)
        
        self.assertTrue(success)
        self.assertIn("Within absolute tolerance", message)
    
    def test_exceeds_absolute_tolerance(self):
        """Test validation exceeding absolute tolerance"""
        success, message = self.validator.validate(1000.0, 1020.0, 10.0)
        
        self.assertFalse(success)
        self.assertIn("Exceeds absolute tolerance", message)


class TestExactValidator(unittest.TestCase):
    """Test exact match validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = ExactValidator()
    
    def test_exact_match(self):
        """Test exact matching values"""
        success, message = self.validator.validate("test", "test", 0.0)
        
        self.assertTrue(success)
        self.assertIn("Exact match", message)
        
        success, message = self.validator.validate(42, 42, 0.0)
        
        self.assertTrue(success)
        self.assertIn("Exact match", message)
    
    def test_different_values(self):
        """Test different values"""
        success, message = self.validator.validate("test1", "test2", 0.0)
        
        self.assertFalse(success)
        self.assertIn("Values differ", message)


class TestScenarioValidator(unittest.TestCase):
    """Test scenario-level validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ValidationConfig()
        self.validator = ScenarioValidator(self.config)
    
    def test_validate_matching_scenario(self):
        """Test validation of matching scenario results"""
        original = {
            'npv': 1000000.0,
            'roi_percent': 200.0,
            'breakeven_month': 6,
            'peak_adoption': 0.75
        }
        
        reproduced = {
            'npv': 1005000.0,  # 0.5% difference
            'roi_percent': 201.0,  # 0.5% difference
            'breakeven_month': 6,  # exact match
            'peak_adoption': 0.751  # 0.13% difference
        }
        
        result = self.validator.validate_scenario(original, reproduced)
        
        self.assertTrue(result['overall_success'])
        self.assertGreater(result['confidence_score'], 0.95)
        self.assertEqual(result['passed_metrics'], 4)
        self.assertEqual(result['failed_metrics'], 0)
    
    def test_validate_mismatched_scenario(self):
        """Test validation of mismatched scenario results"""
        original = {
            'npv': 1000000.0,
            'roi_percent': 200.0,
            'peak_adoption': 0.75
        }
        
        reproduced = {
            'npv': 1200000.0,  # 20% difference - too large
            'roi_percent': 240.0,  # 20% difference - too large
            'peak_adoption': 0.9  # 20% difference - too large
        }
        
        result = self.validator.validate_scenario(original, reproduced)
        
        self.assertFalse(result['overall_success'])
        self.assertLess(result['confidence_score'], 0.95)
        self.assertEqual(result['passed_metrics'], 0)
        self.assertEqual(result['failed_metrics'], 3)
    
    def test_validate_missing_metrics(self):
        """Test validation with missing metrics"""
        original = {
            'npv': 1000000.0,
            'roi_percent': 200.0,
            'missing_metric': 100.0
        }
        
        reproduced = {
            'npv': 1005000.0,
            'roi_percent': 201.0
            # missing_metric is absent
        }
        
        result = self.validator.validate_scenario(original, reproduced)
        
        # Should fail because missing_metric is not in reproduced
        self.assertFalse(result['overall_success'])
        self.assertIn('missing_metric', result['metric_details'])
        self.assertFalse(result['metric_details']['missing_metric']['success'])
    
    def test_get_validation_rule(self):
        """Test getting validation rules for metrics"""
        # Test default rule
        rule = self.validator._get_validation_rule('npv')
        self.assertEqual(rule.metric_name, 'npv')
        self.assertEqual(rule.tolerance, 0.01)
        self.assertEqual(rule.tolerance_type, 'percentage')
        
        # Test custom rule
        custom_config = ValidationConfig()
        custom_config.custom_rules = {
            'custom_metric': ValidationRule('custom_metric', 0.05, 'absolute', False)
        }
        custom_validator = ScenarioValidator(custom_config)
        
        rule = custom_validator._get_validation_rule('custom_metric')
        self.assertEqual(rule.tolerance, 0.05)
        self.assertEqual(rule.tolerance_type, 'absolute')
        self.assertFalse(rule.required)


class TestMultiScenarioValidator(unittest.TestCase):
    """Test multi-scenario validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ValidationConfig()
        self.validator = MultiScenarioValidator(self.config)
    
    def test_validate_multiple_scenarios_success(self):
        """Test successful validation of multiple scenarios"""
        original = {
            'scenario1': {'npv': 1000000.0, 'roi_percent': 200.0},
            'scenario2': {'npv': 2000000.0, 'roi_percent': 300.0}
        }
        
        reproduced = {
            'scenario1': {'npv': 1005000.0, 'roi_percent': 201.0},
            'scenario2': {'npv': 2010000.0, 'roi_percent': 301.5}
        }
        
        result = self.validator.validate_multiple_scenarios(original, reproduced)
        
        self.assertTrue(result['overall_success'])
        self.assertGreater(result['overall_confidence'], 0.95)
        self.assertEqual(result['passed_scenarios'], 2)
        self.assertEqual(result['failed_scenarios'], 0)
        self.assertEqual(result['summary_stats']['total_metrics'], 4)
        self.assertEqual(result['summary_stats']['passed_metrics'], 4)
    
    def test_validate_multiple_scenarios_partial_failure(self):
        """Test validation with some failing scenarios"""
        original = {
            'scenario1': {'npv': 1000000.0, 'roi_percent': 200.0},
            'scenario2': {'npv': 2000000.0, 'roi_percent': 300.0}
        }
        
        reproduced = {
            'scenario1': {'npv': 1005000.0, 'roi_percent': 201.0},  # Good match
            'scenario2': {'npv': 2500000.0, 'roi_percent': 400.0}   # Bad match (25% and 33% differences)
        }
        
        result = self.validator.validate_multiple_scenarios(original, reproduced)
        
        self.assertFalse(result['overall_success'])
        self.assertEqual(result['passed_scenarios'], 1)
        self.assertEqual(result['failed_scenarios'], 1)
        
        # Check individual scenario results
        self.assertTrue(result['scenario_details']['scenario1']['overall_success'])
        self.assertFalse(result['scenario_details']['scenario2']['overall_success'])
    
    def test_validate_missing_scenarios(self):
        """Test validation with missing scenarios"""
        original = {
            'scenario1': {'npv': 1000000.0},
            'scenario2': {'npv': 2000000.0}
        }
        
        reproduced = {
            'scenario1': {'npv': 1005000.0}
            # scenario2 is missing
        }
        
        result = self.validator.validate_multiple_scenarios(original, reproduced)
        
        self.assertFalse(result['overall_success'])
        self.assertEqual(result['passed_scenarios'], 1)
        self.assertEqual(result['failed_scenarios'], 1)
        
        # Check that missing scenario is marked as failed
        self.assertFalse(result['scenario_details']['scenario2']['success'])
        self.assertIn("missing in reproduced", result['scenario_details']['scenario2']['message'])


class TestValidationConfigCreation(unittest.TestCase):
    """Test validation configuration creation helpers"""
    
    def test_create_default_config(self):
        """Test creation of default configuration"""
        config = create_validation_config()
        
        self.assertEqual(config.default_tolerance, 0.01)
        self.assertEqual(config.minimum_confidence_score, 0.95)
        self.assertFalse(config.ignore_missing_metrics)
    
    def test_create_strict_config(self):
        """Test creation of strict configuration"""
        config = create_validation_config(tolerance=0.005, strict=True)
        
        self.assertEqual(config.default_tolerance, 0.005)
        self.assertEqual(config.minimum_confidence_score, 0.98)
        self.assertFalse(config.ignore_missing_metrics)
    
    def test_create_custom_rules_config(self):
        """Test creation with custom rules"""
        custom_rules = {
            'npv': {
                'tolerance': 0.02,
                'type': 'percentage',
                'required': True,
                'description': 'Custom NPV rule'
            },
            'breakeven_month': {
                'tolerance': 0,
                'type': 'exact',
                'required': False,
                'description': 'Exact breakeven match'
            }
        }
        
        config = create_validation_config(custom_rules=custom_rules)
        
        self.assertIn('npv', config.custom_rules)
        self.assertIn('breakeven_month', config.custom_rules)
        
        npv_rule = config.custom_rules['npv']
        self.assertEqual(npv_rule.tolerance, 0.02)
        self.assertEqual(npv_rule.tolerance_type, 'percentage')
        self.assertTrue(npv_rule.required)
        
        breakeven_rule = config.custom_rules['breakeven_month']
        self.assertEqual(breakeven_rule.tolerance, 0)
        self.assertEqual(breakeven_rule.tolerance_type, 'exact')
        self.assertFalse(breakeven_rule.required)


if __name__ == '__main__':
    unittest.main()