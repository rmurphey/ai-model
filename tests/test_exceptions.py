"""
Tests for exceptions.py - Enhanced error handling with user-friendly messages
"""

import pytest
from src.utils.exceptions import (
    AIAnalysisError, ConfigurationError, ValidationError, 
    CalculationError, ScenarioError, DataError
)


class TestAIAnalysisError:
    """Test base exception class"""
    
    def test_base_exception_creation(self):
        """Test basic exception creation and inheritance"""
        error = AIAnalysisError("test message")
        assert str(error) == "test message"
        assert isinstance(error, Exception)


class TestConfigurationError:
    """Test configuration error with file context and resolution steps"""
    
    def test_basic_configuration_error(self):
        """Test basic configuration error message"""
        error = ConfigurationError("File not found")
        assert "Configuration Error: File not found" in str(error)
        
    def test_configuration_error_with_file(self):
        """Test configuration error with file context"""
        error = ConfigurationError("Invalid format", config_file="test.yaml")
        error_str = str(error)
        assert "Configuration Error: Invalid format" in error_str
        assert "📁 File: test.yaml" in error_str
        
    def test_configuration_error_with_suggestion(self):
        """Test configuration error with suggestion"""
        error = ConfigurationError("Parse error", suggestion="Check YAML syntax")
        error_str = str(error)
        assert "💡 Suggestion: Check YAML syntax" in error_str
        
    def test_configuration_error_with_resolution_steps(self):
        """Test configuration error with resolution steps"""
        steps = ["Step 1: Check file", "Step 2: Validate syntax"]
        error = ConfigurationError("Error", resolution_steps=steps)
        error_str = str(error)
        assert "🔧 Resolution Steps:" in error_str
        assert "1. Step 1: Check file" in error_str
        assert "2. Step 2: Validate syntax" in error_str
        
    def test_configuration_error_default_steps_file_not_found(self):
        """Test default resolution steps for file not found"""
        error = ConfigurationError("File not found")
        error_str = str(error)
        assert "🔧 Resolution Steps:" in error_str
        assert "Check if the file path is correct" in error_str
        
    def test_configuration_error_default_steps_yaml_error(self):
        """Test default resolution steps for YAML errors"""
        error = ConfigurationError("Invalid YAML format")
        error_str = str(error)
        assert "🔧 Resolution Steps:" in error_str
        assert "Validate YAML syntax" in error_str


class TestValidationError:
    """Test validation error with examples and guidance"""
    
    def test_basic_validation_error(self):
        """Test basic validation error"""
        error = ValidationError("field_name", "invalid_value", "positive number")
        error_str = str(error)
        assert "Invalid value for 'field_name': invalid_value" in error_str
        assert "📋 Expected: positive number" in error_str
        
    def test_validation_error_with_suggestion(self):
        """Test validation error with suggestion"""
        error = ValidationError("ratio", 1.5, "0-1 range", suggestion="Use decimal values")
        error_str = str(error)
        assert "💡 Suggestion: Use decimal values" in error_str
        
    def test_validation_error_with_examples(self):
        """Test validation error with custom examples"""
        examples = ["0.25", "0.5", "0.75"]
        error = ValidationError("ratio", 1.5, "0-1 range", valid_examples=examples)
        error_str = str(error)
        assert "✅ Valid examples:" in error_str
        assert "• 0.25" in error_str
        assert "• 0.5" in error_str
        
    def test_validation_error_default_ratio_examples(self):
        """Test default examples for ratio validation"""
        error = ValidationError("adoption_rate", 1.5, "ratio between 0-1")
        error_str = str(error)
        assert "✅ Valid examples:" in error_str
        assert "• 0.25 (25%)" in error_str
        assert "• 0.5 (50%)" in error_str
        
    def test_validation_error_default_positive_examples(self):
        """Test default examples for positive number validation"""
        error = ValidationError("team_size", -1, "positive number")
        error_str = str(error)
        assert "✅ Valid examples:" in error_str
        assert "• 1.0" in error_str
        assert "• 10" in error_str
        
    def test_validation_error_default_percentage_examples(self):
        """Test default examples for percentage validation"""
        error = ValidationError("efficiency", 150, "percentage value")
        error_str = str(error)
        assert "✅ Valid examples:" in error_str
        assert "• 25 (for 25%)" in error_str
        assert "• 50.5 (for 50.5%)" in error_str


class TestCalculationError:
    """Test calculation error with debug information and operation-specific guidance"""
    
    def test_basic_calculation_error(self):
        """Test basic calculation error"""
        error = CalculationError("division", "denominator is zero")
        error_str = str(error)
        assert "Calculation error in division: denominator is zero" in error_str
        
    def test_calculation_error_with_context(self):
        """Test calculation error with context"""
        error = CalculationError("validation", "invalid range", context="ROI calculation")
        error_str = str(error)
        assert "📍 Context: ROI calculation" in error_str
        
    def test_calculation_error_with_debug_info(self):
        """Test calculation error with debug information"""
        debug_info = {"numerator": 100, "denominator": 0, "step": "final_calculation"}
        error = CalculationError("division", "zero denominator", debug_info=debug_info)
        error_str = str(error)
        assert "🔍 Debug Information:" in error_str
        assert "• numerator: 100" in error_str
        assert "• denominator: 0" in error_str
        
    def test_calculation_error_division_steps(self):
        """Test division-specific resolution steps"""
        error = CalculationError("division", "error")
        error_str = str(error)
        assert "🔧 Resolution Steps:" in error_str
        assert "Check that denominator values are not zero" in error_str
        assert "Consider using safe_divide() function" in error_str
        
    def test_calculation_error_validation_steps(self):
        """Test validation-specific resolution steps"""
        error = CalculationError("validation", "error")
        error_str = str(error)
        assert "Review the input value requirements" in error_str
        
    def test_calculation_error_logarithm_steps(self):
        """Test logarithm-specific resolution steps"""
        error = CalculationError("logarithm", "error")
        error_str = str(error)
        assert "Ensure input values are positive" in error_str
        assert "Consider using safe_log() function" in error_str


class TestScenarioError:
    """Test scenario error with closest match suggestions"""
    
    def test_basic_scenario_error(self):
        """Test basic scenario error"""
        error = ScenarioError("test_scenario", "not found")
        error_str = str(error)
        assert "Scenario 'test_scenario': not found" in error_str
        
    def test_scenario_error_with_available_scenarios(self):
        """Test scenario error with available scenarios list"""
        available = ["scenario1", "scenario2", "scenario3"]
        error = ScenarioError("missing", "not found", available_scenarios=available)
        error_str = str(error)
        assert "📋 Available scenarios:" in error_str
        assert "• scenario1" in error_str
        assert "• scenario2" in error_str
        
    def test_scenario_error_with_config_file(self):
        """Test scenario error with config file reference"""
        error = ScenarioError("test", "invalid", config_file="scenarios.yaml")
        error_str = str(error)
        assert "📁 Configuration file: scenarios.yaml" in error_str
        
    def test_scenario_error_not_found_steps(self):
        """Test resolution steps for not found scenarios"""
        error = ScenarioError("missing", "not found")
        error_str = str(error)
        assert "🔧 Resolution Steps:" in error_str
        assert "Check spelling of scenario name" in error_str
        assert "Use '--list' to see all available scenarios" in error_str
        
    def test_scenario_error_closest_match(self):
        """Test closest match suggestion"""
        available = ["moderate_enterprise", "conservative_startup"]
        error = ScenarioError("moderate_enterprize", "not found", available_scenarios=available)
        error_str = str(error)
        # Should suggest "moderate_enterprise" as closest match
        assert "Did you mean 'moderate_enterprise'?" in error_str
        
    def test_find_closest_scenario_method(self):
        """Test the closest scenario matching logic"""
        available = ["moderate_enterprise", "conservative_startup", "aggressive_scaleup"]
        error = ScenarioError("test", "test", available_scenarios=available)
        
        # Test exact partial match
        closest = error._find_closest_scenario("moderate", available)
        assert closest == "moderate_enterprise"
        
        # Test no good match
        closest = error._find_closest_scenario("xyz", available)
        assert closest is None
        
        # Test empty scenarios
        closest = error._find_closest_scenario("test", [])
        assert closest is None


class TestDataError:
    """Test data error with format expectations and troubleshooting"""
    
    def test_basic_data_error(self):
        """Test basic data error"""
        error = DataError("team_metrics", "invalid format")
        error_str = str(error)
        assert "Data error (team_metrics): invalid format" in error_str
        
    def test_data_error_with_source(self):
        """Test data error with data source"""
        error = DataError("baseline", "missing values", data_source="config.yaml")
        error_str = str(error)
        assert "📁 Source: config.yaml" in error_str
        
    def test_data_error_with_expected_format(self):
        """Test data error with expected format"""
        error = DataError("metrics", "wrong type", expected_format="numeric values")
        error_str = str(error)
        assert "📋 Expected format: numeric values" in error_str
        
    def test_data_error_with_current_value(self):
        """Test data error with current value display"""
        error = DataError("field", "invalid", current_value="string_value")
        error_str = str(error)
        assert "📊 Current value: string_value" in error_str
        
    def test_data_error_missing_resolution_steps(self):
        """Test resolution steps for missing data"""
        error = DataError("records", "missing data")
        error_str = str(error)
        assert "🔧 Resolution Steps:" in error_str
        assert "Check if data source file exists" in error_str
        
    def test_data_error_format_resolution_steps(self):
        """Test resolution steps for format errors"""
        error = DataError("values", "invalid format")
        error_str = str(error)
        assert "Validate data format matches expected structure" in error_str
        assert "Compare with working data examples" in error_str
        
    def test_data_error_empty_resolution_steps(self):
        """Test resolution steps for empty data"""
        error = DataError("dataset", "empty data")
        error_str = str(error)
        assert "Verify data source contains records" in error_str
        assert "Check filtering conditions are not too restrictive" in error_str