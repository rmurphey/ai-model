"""
Custom exception classes for AI Impact Analysis tool.
Provides specific, user-friendly error handling for business analysis scenarios.
"""


class AIAnalysisError(Exception):
    """Base exception class for AI analysis tool errors."""
    pass


class ConfigurationError(AIAnalysisError):
    """Raised when there are issues with configuration files or parameters."""
    
    def __init__(self, message: str, config_file: str = None, suggestion: str = None, resolution_steps: list = None):
        self.config_file = config_file
        self.suggestion = suggestion
        self.resolution_steps = resolution_steps or []
        
        full_message = f"Configuration Error: {message}"
        if config_file:
            full_message += f"\n📁 File: {config_file}"
        
        if suggestion:
            full_message += f"\n💡 Suggestion: {suggestion}"
        
        if self.resolution_steps:
            full_message += "\n🔧 Resolution Steps:"
            for i, step in enumerate(self.resolution_steps, 1):
                full_message += f"\n   {i}. {step}"
        
        if not suggestion and not self.resolution_steps:
            # Provide default resolution steps for common config issues
            if "not found" in message.lower():
                full_message += "\n🔧 Resolution Steps:"
                full_message += "\n   1. Check if the file path is correct"
                full_message += "\n   2. Ensure the file exists in the expected location"
                full_message += "\n   3. Verify file permissions allow reading"
            elif "yaml" in message.lower() or "format" in message.lower():
                full_message += "\n🔧 Resolution Steps:"
                full_message += "\n   1. Validate YAML syntax using an online YAML validator"
                full_message += "\n   2. Check for proper indentation (use spaces, not tabs)"
                full_message += "\n   3. Ensure all string values are properly quoted"
                full_message += "\n   4. Look for examples in 'src/scenarios/scenarios.yaml'"
        
        super().__init__(full_message)


class ValidationError(AIAnalysisError):
    """Raised when input validation fails."""
    
    def __init__(self, field_name: str, value, expected: str, suggestion: str = None, valid_examples: list = None):
        self.field_name = field_name
        self.value = value
        self.expected = expected
        self.valid_examples = valid_examples or []
        
        message = f"Invalid value for '{field_name}': {value}"
        message += f"\n📋 Expected: {expected}"
        
        if suggestion:
            message += f"\n💡 Suggestion: {suggestion}"
        
        if self.valid_examples:
            message += "\n✅ Valid examples:"
            for example in self.valid_examples:
                message += f"\n   • {example}"
        
        # Provide default examples for common validation errors
        if not self.valid_examples:
            if "ratio" in expected.lower() or "0-1" in expected:
                message += "\n✅ Valid examples:"
                message += "\n   • 0.25 (25%)"
                message += "\n   • 0.5 (50%)"
                message += "\n   • 0.75 (75%)"
                message += "\n   • 1.0 (100%)"
            elif "positive" in expected.lower():
                message += "\n✅ Valid examples:"
                message += "\n   • 1.0"
                message += "\n   • 10"
                message += "\n   • 100.5"
            elif "percentage" in expected.lower():
                message += "\n✅ Valid examples:"
                message += "\n   • 25 (for 25%)"
                message += "\n   • 50.5 (for 50.5%)"
                message += "\n   • 100 (for 100%)"
        
        super().__init__(message)


class CalculationError(AIAnalysisError):
    """Raised when mathematical calculations encounter invalid conditions."""
    
    def __init__(self, operation: str, reason: str, context: str = None, debug_info: dict = None):
        self.operation = operation
        self.reason = reason
        self.context = context
        self.debug_info = debug_info or {}
        
        message = f"Calculation error in {operation}: {reason}"
        if context:
            message += f"\n📍 Context: {context}"
        
        if self.debug_info:
            message += "\n🔍 Debug Information:"
            for key, value in self.debug_info.items():
                message += f"\n   • {key}: {value}"
        
        # Provide specific resolution steps based on operation type
        message += "\n🔧 Resolution Steps:"
        if "division" in operation.lower():
            message += "\n   1. Check that denominator values are not zero"
            message += "\n   2. Verify input data contains valid numbers"
            message += "\n   3. Consider using safe_divide() function for robustness"
        elif "validation" in operation.lower():
            message += "\n   1. Review the input value requirements"
            message += "\n   2. Check data source for correct value formatting"
            message += "\n   3. Ensure values are within expected ranges"
        elif "logarithm" in operation.lower():
            message += "\n   1. Ensure input values are positive"
            message += "\n   2. Check for zero or negative values in data"
            message += "\n   3. Consider using safe_log() function for edge cases"
        else:
            message += "\n   1. Review input parameters for the calculation"
            message += "\n   2. Check for invalid or missing data"
            message += "\n   3. Verify calculation assumptions are met"
        
        super().__init__(message)


class ScenarioError(AIAnalysisError):
    """Raised when scenario configuration is invalid or missing."""
    
    def __init__(self, scenario_name: str, issue: str, available_scenarios: list = None, config_file: str = None):
        self.scenario_name = scenario_name
        self.issue = issue
        self.available_scenarios = available_scenarios or []
        self.config_file = config_file
        
        message = f"Scenario '{scenario_name}': {issue}"
        
        if self.available_scenarios:
            message += "\n📋 Available scenarios:"
            for scenario in self.available_scenarios:
                message += f"\n   • {scenario}"
        
        if config_file:
            message += f"\n📁 Configuration file: {config_file}"
        
        message += "\n🔧 Resolution Steps:"
        if "not found" in issue.lower():
            message += "\n   1. Check spelling of scenario name"
            message += "\n   2. Use '--list' to see all available scenarios"
            message += "\n   3. Verify scenario exists in configuration file"
            if self.available_scenarios:
                closest_match = self._find_closest_scenario(scenario_name, self.available_scenarios)
                if closest_match:
                    message += f"\n   4. Did you mean '{closest_match}'?"
        else:
            message += "\n   1. Review scenario configuration format"
            message += "\n   2. Check required fields are present"
            message += "\n   3. Validate parameter values are correct"
            message += "\n   4. Compare with working scenario examples"
        
        super().__init__(message)
    
    def _find_closest_scenario(self, target: str, scenarios: list) -> str:
        """Find the closest matching scenario name using simple string similarity."""
        if not scenarios:
            return None
        
        target_lower = target.lower()
        best_match = None
        best_score = 0
        
        for scenario in scenarios:
            scenario_lower = scenario.lower()
            # Simple similarity: count common characters
            common_chars = sum(1 for a, b in zip(target_lower, scenario_lower) if a == b)
            score = common_chars / max(len(target_lower), len(scenario_lower))
            
            if score > best_score and score > 0.3:  # At least 30% similarity
                best_score = score
                best_match = scenario
        
        return best_match


class DataError(AIAnalysisError):
    """Raised when data processing encounters invalid or missing data."""
    
    def __init__(self, data_type: str, issue: str, data_source: str = None, expected_format: str = None, current_value=None):
        self.data_type = data_type
        self.issue = issue
        self.data_source = data_source
        self.expected_format = expected_format
        self.current_value = current_value
        
        message = f"Data error ({data_type}): {issue}"
        
        if data_source:
            message += f"\n📁 Source: {data_source}"
        
        if current_value is not None:
            message += f"\n📊 Current value: {current_value}"
        
        if expected_format:
            message += f"\n📋 Expected format: {expected_format}"
        
        message += "\n🔧 Resolution Steps:"
        if "missing" in issue.lower():
            message += "\n   1. Check if data source file exists"
            message += "\n   2. Verify required fields are present in data"
            message += "\n   3. Ensure data is not filtered out by processing logic"
        elif "format" in issue.lower() or "invalid" in issue.lower():
            message += "\n   1. Validate data format matches expected structure"
            message += "\n   2. Check for correct data types (numbers, strings, dates)"
            message += "\n   3. Verify encoding and special characters"
            message += "\n   4. Compare with working data examples"
        elif "empty" in issue.lower():
            message += "\n   1. Verify data source contains records"
            message += "\n   2. Check filtering conditions are not too restrictive"
            message += "\n   3. Ensure data loading completed successfully"
        else:
            message += "\n   1. Review data quality and completeness"
            message += "\n   2. Check data source is accessible and readable"
            message += "\n   3. Validate data preprocessing steps"
        
        super().__init__(message)