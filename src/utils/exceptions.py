"""
Custom exception classes for AI Impact Analysis tool.
Provides specific, user-friendly error handling for business analysis scenarios.
"""


class AIAnalysisError(Exception):
    """Base exception class for AI analysis tool errors."""
    pass


class ConfigurationError(AIAnalysisError):
    """Raised when there are issues with configuration files or parameters."""
    
    def __init__(self, message: str, config_file: str = None, suggestion: str = None):
        self.config_file = config_file
        self.suggestion = suggestion
        
        full_message = f"Configuration Error: {message}"
        if config_file:
            full_message += f" (File: {config_file})"
        if suggestion:
            full_message += f"\nSuggestion: {suggestion}"
        
        super().__init__(full_message)


class ValidationError(AIAnalysisError):
    """Raised when input validation fails."""
    
    def __init__(self, field_name: str, value, expected: str, suggestion: str = None):
        self.field_name = field_name
        self.value = value
        self.expected = expected
        
        message = f"Invalid value for '{field_name}': {value}. Expected: {expected}"
        if suggestion:
            message += f"\nSuggestion: {suggestion}"
        
        super().__init__(message)


class CalculationError(AIAnalysisError):
    """Raised when mathematical calculations encounter invalid conditions."""
    
    def __init__(self, operation: str, reason: str, context: str = None):
        self.operation = operation
        self.reason = reason
        self.context = context
        
        message = f"Calculation error in {operation}: {reason}"
        if context:
            message += f" (Context: {context})"
        
        super().__init__(message)


class ScenarioError(AIAnalysisError):
    """Raised when scenario configuration is invalid or missing."""
    
    def __init__(self, scenario_name: str, issue: str, available_scenarios: list = None):
        self.scenario_name = scenario_name
        self.issue = issue
        self.available_scenarios = available_scenarios
        
        message = f"Scenario '{scenario_name}': {issue}"
        if available_scenarios:
            message += f"\nAvailable scenarios: {', '.join(available_scenarios)}"
        
        super().__init__(message)


class DataError(AIAnalysisError):
    """Raised when data processing encounters invalid or missing data."""
    
    def __init__(self, data_type: str, issue: str, data_source: str = None):
        self.data_type = data_type
        self.issue = issue
        self.data_source = data_source
        
        message = f"Data error ({data_type}): {issue}"
        if data_source:
            message += f" (Source: {data_source})"
        
        super().__init__(message)