#!/usr/bin/env python3
"""
Validation Framework for Result Reproduction
Provides configurable validation rules and tolerance levels for reproduction verification.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

from src.utils.exceptions import ValidationError


@dataclass
class ValidationRule:
    """Configuration for a validation rule"""
    metric_name: str
    tolerance: float
    tolerance_type: str  # 'percentage', 'absolute', 'relative'
    required: bool = True
    description: str = ""


@dataclass 
class ValidationConfig:
    """Configuration for validation behavior"""
    default_tolerance: float = 0.01  # 1%
    default_tolerance_type: str = 'percentage'
    ignore_missing_metrics: bool = False
    ignore_none_values: bool = True
    minimum_confidence_score: float = 0.95
    custom_rules: Dict[str, ValidationRule] = None
    
    def __post_init__(self):
        if self.custom_rules is None:
            self.custom_rules = {}


class BaseValidator(ABC):
    """Abstract base class for validation strategies"""
    
    @abstractmethod
    def validate(self, original: Any, reproduced: Any, tolerance: float) -> Tuple[bool, str]:
        """Validate two values and return (is_valid, description)"""
        pass


class NumericalValidator(BaseValidator):
    """Validator for numerical values with configurable tolerance"""
    
    def validate(self, original: Union[int, float], reproduced: Union[int, float], 
                tolerance: float) -> Tuple[bool, str]:
        """Validate numerical values within tolerance"""
        
        # Handle None values
        if original is None and reproduced is None:
            return True, "Both values are None"
        if original is None or reproduced is None:
            return False, f"One value is None: original={original}, reproduced={reproduced}"
        
        # Convert to float for comparison
        try:
            orig_val = float(original)
            repro_val = float(reproduced)
        except (ValueError, TypeError):
            return False, f"Cannot convert to numbers: original={original}, reproduced={reproduced}"
        
        # Handle zero values
        if orig_val == 0:
            if abs(repro_val) <= tolerance:
                return True, f"Both approximately zero (within {tolerance})"
            else:
                return False, f"Original is 0 but reproduced is {repro_val}"
        
        # Percentage difference calculation
        pct_diff = abs((repro_val - orig_val) / orig_val)
        
        if pct_diff <= tolerance:
            return True, f"Within tolerance: {pct_diff:.4%} ≤ {tolerance:.4%}"
        else:
            return False, f"Exceeds tolerance: {pct_diff:.4%} > {tolerance:.4%} (orig={orig_val}, repro={repro_val})"


class AbsoluteValidator(BaseValidator):
    """Validator for absolute differences"""
    
    def validate(self, original: Union[int, float], reproduced: Union[int, float],
                tolerance: float) -> Tuple[bool, str]:
        """Validate values within absolute tolerance"""
        
        if original is None and reproduced is None:
            return True, "Both values are None"
        if original is None or reproduced is None:
            return False, f"One value is None: original={original}, reproduced={reproduced}"
        
        try:
            orig_val = float(original)
            repro_val = float(reproduced)
            abs_diff = abs(repro_val - orig_val)
            
            if abs_diff <= tolerance:
                return True, f"Within absolute tolerance: |{abs_diff}| ≤ {tolerance}"
            else:
                return False, f"Exceeds absolute tolerance: |{abs_diff}| > {tolerance}"
                
        except (ValueError, TypeError):
            return False, f"Cannot convert to numbers: original={original}, reproduced={reproduced}"


class ExactValidator(BaseValidator):
    """Validator for exact matches (strings, integers, etc.)"""
    
    def validate(self, original: Any, reproduced: Any, tolerance: float) -> Tuple[bool, str]:
        """Validate exact equality"""
        
        if original == reproduced:
            return True, f"Exact match: {original}"
        else:
            return False, f"Values differ: original={original}, reproduced={reproduced}"


class ScenarioValidator:
    """Validates specific scenario types with custom rules"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.validators = {
            'numerical': NumericalValidator(),
            'absolute': AbsoluteValidator(), 
            'exact': ExactValidator()
        }
        
        # Define default validation rules for common metrics
        self.default_rules = {
            'npv': ValidationRule('npv', 0.01, 'percentage', True, "Net Present Value"),
            'roi_percent': ValidationRule('roi_percent', 0.02, 'percentage', True, "Return on Investment"),
            'peak_adoption': ValidationRule('peak_adoption', 0.01, 'percentage', True, "Peak Adoption Rate"),
            'total_cost_3y': ValidationRule('total_cost_3y', 0.01, 'percentage', True, "Total 3-Year Cost"),
            'total_value_3y': ValidationRule('total_value_3y', 0.01, 'percentage', True, "Total 3-Year Value"),
            'breakeven_month': ValidationRule('breakeven_month', 0, 'exact', False, "Breakeven Month"),
            'annual_cost_per_dev': ValidationRule('annual_cost_per_dev', 0.02, 'percentage', True, "Annual Cost per Developer"),
            'annual_value_per_dev': ValidationRule('annual_value_per_dev', 0.02, 'percentage', True, "Annual Value per Developer")
        }
    
    def validate_scenario(self, original: Dict[str, Any], reproduced: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a complete scenario's results"""
        
        validation_results = {
            'total_metrics': 0,
            'passed_metrics': 0,
            'failed_metrics': 0,
            'metric_details': {},
            'confidence_score': 0.0,
            'overall_success': False
        }
        
        # Get all metrics to validate
        all_metrics = set(original.keys()) | set(reproduced.keys())
        
        for metric in all_metrics:
            validation_results['total_metrics'] += 1
            
            # Check if metric exists in both
            if metric not in original:
                if not self.config.ignore_missing_metrics:
                    validation_results['failed_metrics'] += 1
                    validation_results['metric_details'][metric] = {
                        'success': False,
                        'message': "Missing in original results"
                    }
                continue
                
            if metric not in reproduced:
                validation_results['failed_metrics'] += 1
                validation_results['metric_details'][metric] = {
                    'success': False,
                    'message': "Missing in reproduced results"
                }
                continue
            
            # Validate the metric
            result = self._validate_metric(metric, original[metric], reproduced[metric])
            validation_results['metric_details'][metric] = result
            
            if result['success']:
                validation_results['passed_metrics'] += 1
            else:
                validation_results['failed_metrics'] += 1
        
        # Calculate confidence score
        if validation_results['total_metrics'] > 0:
            validation_results['confidence_score'] = (
                validation_results['passed_metrics'] / validation_results['total_metrics']
            )
        
        # Determine overall success
        validation_results['overall_success'] = (
            validation_results['confidence_score'] >= self.config.minimum_confidence_score
        )
        
        return validation_results
    
    def _validate_metric(self, metric_name: str, original: Any, reproduced: Any) -> Dict[str, Any]:
        """Validate a single metric"""
        
        # Get validation rule for this metric
        rule = self._get_validation_rule(metric_name)
        
        # Select appropriate validator
        if rule.tolerance_type == 'exact':
            validator = self.validators['exact']
        elif rule.tolerance_type == 'absolute':
            validator = self.validators['absolute']
        else:  # percentage or relative
            validator = self.validators['numerical']
        
        # Perform validation
        success, message = validator.validate(original, reproduced, rule.tolerance)
        
        return {
            'success': success,
            'message': message,
            'tolerance': rule.tolerance,
            'tolerance_type': rule.tolerance_type,
            'rule_description': rule.description
        }
    
    def _get_validation_rule(self, metric_name: str) -> ValidationRule:
        """Get validation rule for a metric"""
        
        # Check custom rules first
        if metric_name in self.config.custom_rules:
            return self.config.custom_rules[metric_name]
        
        # Check default rules
        if metric_name in self.default_rules:
            return self.default_rules[metric_name]
        
        # Create default rule
        return ValidationRule(
            metric_name=metric_name,
            tolerance=self.config.default_tolerance,
            tolerance_type=self.config.default_tolerance_type,
            required=False,
            description=f"Default validation for {metric_name}"
        )


class MultiScenarioValidator:
    """Validates results across multiple scenarios"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.scenario_validator = ScenarioValidator(config)
    
    def validate_multiple_scenarios(self, original: Dict[str, Dict], 
                                  reproduced: Dict[str, Dict]) -> Dict[str, Any]:
        """Validate results across multiple scenarios"""
        
        overall_results = {
            'total_scenarios': 0,
            'passed_scenarios': 0,
            'failed_scenarios': 0,
            'scenario_details': {},
            'overall_confidence': 0.0,
            'overall_success': False,
            'summary_stats': {
                'total_metrics': 0,
                'passed_metrics': 0,
                'failed_metrics': 0
            }
        }
        
        # Get all scenarios
        all_scenarios = set(original.keys()) | set(reproduced.keys())
        
        for scenario in all_scenarios:
            overall_results['total_scenarios'] += 1
            
            # Check if scenario exists in both
            if scenario not in original:
                overall_results['failed_scenarios'] += 1
                overall_results['scenario_details'][scenario] = {
                    'success': False,
                    'message': "Scenario missing in original results",
                    'confidence_score': 0.0,
                    'total_metrics': 0,
                    'passed_metrics': 0,
                    'failed_metrics': 0
                }
                continue
                
            if scenario not in reproduced:
                overall_results['failed_scenarios'] += 1
                # Count the metrics that would have been in the missing scenario
                missing_metric_count = len(original[scenario])
                overall_results['summary_stats']['total_metrics'] += missing_metric_count
                overall_results['summary_stats']['failed_metrics'] += missing_metric_count
                
                overall_results['scenario_details'][scenario] = {
                    'success': False,
                    'message': "Scenario missing in reproduced results",
                    'confidence_score': 0.0,
                    'total_metrics': missing_metric_count,
                    'passed_metrics': 0,
                    'failed_metrics': missing_metric_count
                }
                continue
            
            # Validate the scenario
            scenario_result = self.scenario_validator.validate_scenario(
                original[scenario], reproduced[scenario]
            )
            
            overall_results['scenario_details'][scenario] = scenario_result
            
            # Update summary statistics
            overall_results['summary_stats']['total_metrics'] += scenario_result['total_metrics']
            overall_results['summary_stats']['passed_metrics'] += scenario_result['passed_metrics']
            overall_results['summary_stats']['failed_metrics'] += scenario_result['failed_metrics']
            
            if scenario_result['overall_success']:
                overall_results['passed_scenarios'] += 1
            else:
                overall_results['failed_scenarios'] += 1
        
        # Calculate overall confidence
        if overall_results['summary_stats']['total_metrics'] > 0:
            overall_results['overall_confidence'] = (
                overall_results['summary_stats']['passed_metrics'] / 
                overall_results['summary_stats']['total_metrics']
            )
        
        # Determine overall success
        overall_results['overall_success'] = (
            overall_results['overall_confidence'] >= self.config.minimum_confidence_score
        )
        
        return overall_results


def create_validation_config(tolerance: float = 0.01, 
                           strict: bool = False,
                           custom_rules: Dict[str, Dict] = None) -> ValidationConfig:
    """Create a validation configuration with common presets"""
    
    config = ValidationConfig(
        default_tolerance=tolerance,
        minimum_confidence_score=0.98 if strict else 0.95,
        ignore_missing_metrics=False,  # Always fail on missing metrics by default
        ignore_none_values=True
    )
    
    # Add custom rules if provided
    if custom_rules:
        config.custom_rules = {}
        for metric, rule_config in custom_rules.items():
            config.custom_rules[metric] = ValidationRule(
                metric_name=metric,
                tolerance=rule_config.get('tolerance', tolerance),
                tolerance_type=rule_config.get('type', 'percentage'),
                required=rule_config.get('required', True),
                description=rule_config.get('description', f"Custom rule for {metric}")
            )
    
    return config