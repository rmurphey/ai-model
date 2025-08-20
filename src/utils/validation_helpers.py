"""
Validation helper functions that provide constructive feedback for common input errors.
These functions complement the existing validation but focus on user-friendly guidance.
"""

from typing import Dict, List, Any, Optional, Union
from .exceptions import ValidationError, ConfigurationError, DataError
from .math_helpers import validate_positive, validate_ratio


def validate_scenario_config(scenario_data: Dict[str, Any], scenario_name: str) -> None:
    """
    Validate a complete scenario configuration with helpful error messages.
    
    Args:
        scenario_data: The scenario configuration dictionary
        scenario_name: Name of the scenario for error reporting
        
    Raises:
        ConfigurationError: If scenario structure is invalid
        ValidationError: If parameter values are invalid
    """
    required_sections = {
        'baseline': ['team_size', 'annual_salary', 'total_working_days'],
        'adoption': ['initial_adopters', 'early_adopters', 'early_majority', 'late_majority'],
        'impact': ['productivity_gain', 'quality_improvement', 'time_to_market_improvement'],
        'costs': ['license_cost_monthly', 'setup_cost_one_time'],
        'timeframe_months': None  # Simple field, not a section
    }
    
    # Check for missing top-level sections
    missing_sections = [section for section in required_sections.keys() if section not in scenario_data]
    if missing_sections:
        raise ConfigurationError(
            f"Scenario '{scenario_name}' is missing required sections: {', '.join(missing_sections)}",
            resolution_steps=[
                f"Add missing sections to scenario '{scenario_name}': {', '.join(missing_sections)}",
                "Copy structure from a working scenario as a template",
                "Ensure each section contains the required fields",
                "Validate all parameter values are in the correct format"
            ]
        )
    
    # Validate each section's required fields
    for section_name, required_fields in required_sections.items():
        if required_fields is None:  # Simple field like timeframe_months
            continue
            
        section_data = scenario_data.get(section_name, {})
        if isinstance(section_data, str):  # Profile reference like "startup"
            continue  # Profile validation happens elsewhere
            
        missing_fields = [field for field in required_fields if field not in section_data]
        if missing_fields:
            raise ConfigurationError(
                f"Scenario '{scenario_name}' section '{section_name}' is missing fields: {', '.join(missing_fields)}",
                resolution_steps=[
                    f"Add missing fields to '{section_name}' section: {', '.join(missing_fields)}",
                    f"Check documentation for required {section_name} parameters",
                    "Compare with working scenario examples",
                    "Ensure field names match exactly (case-sensitive)"
                ]
            )


def validate_team_size(team_size: Union[int, float], context: str = "team configuration") -> None:
    """
    Validate team size with specific guidance for common issues.
    
    Args:
        team_size: Number of team members
        context: Context for error reporting
        
    Raises:
        ValidationError: If team size is invalid
    """
    if not isinstance(team_size, (int, float)):
        raise ValidationError(
            field_name="team_size",
            value=team_size,
            expected="positive integer or float",
            suggestion="Team size should be a number representing the count of developers",
            valid_examples=["5", "10", "25", "100", "5.5 (for part-time equivalents)"]
        )
    
    if team_size <= 0:
        raise ValidationError(
            field_name="team_size", 
            value=team_size,
            expected="positive number greater than 0",
            suggestion="Team size must be at least 1 developer",
            valid_examples=["1 (single developer)", "5 (small team)", "25 (medium team)", "100 (large team)"]
        )
    
    if team_size > 10000:
        raise ValidationError(
            field_name="team_size",
            value=team_size, 
            expected="reasonable team size (typically < 10,000)",
            suggestion="Very large team sizes may indicate a data entry error",
            valid_examples=["100 (large team)", "500 (enterprise)", "1000 (very large organization)"]
        )


def validate_adoption_ratios(adoption_data: Dict[str, float], scenario_name: str = "unknown") -> None:
    """
    Validate adoption segment ratios sum to approximately 1.0 with helpful guidance.
    
    Args:
        adoption_data: Dictionary containing adoption ratios
        scenario_name: Name of scenario for error context
        
    Raises:
        ValidationError: If ratios are invalid or don't sum correctly
    """
    ratio_fields = ['initial_adopters', 'early_adopters', 'early_majority', 'late_majority', 'laggards']
    
    # Check for missing ratio fields
    missing_fields = [field for field in ratio_fields if field not in adoption_data]
    if missing_fields:
        raise ConfigurationError(
            f"Adoption configuration for '{scenario_name}' missing fields: {', '.join(missing_fields)}",
            resolution_steps=[
                f"Add missing adoption ratio fields: {', '.join(missing_fields)}",
                "All five adoption segments must be defined",
                "Each ratio should be between 0.0 and 1.0",
                "All ratios should sum to approximately 1.0",
                "Example: initial_adopters: 0.05, early_adopters: 0.15, etc."
            ]
        )
    
    # Validate individual ratios
    for field in ratio_fields:
        value = adoption_data[field]
        if not isinstance(value, (int, float)):
            raise ValidationError(
                field_name=f"adoption.{field}",
                value=value,
                expected="number between 0.0 and 1.0",
                suggestion=f"{field} should be a decimal ratio (e.g., 0.15 for 15%)",
                valid_examples=["0.05 (5%)", "0.15 (15%)", "0.25 (25%)", "0.35 (35%)"]
            )
        
        if not (0.0 <= value <= 1.0):
            raise ValidationError(
                field_name=f"adoption.{field}",
                value=value,
                expected="ratio between 0.0 and 1.0",
                suggestion="Adoption ratios should be decimal values, not percentages",
                valid_examples=["0.05 (for 5%)", "0.15 (for 15%)", "0.25 (for 25%)"]
            )
    
    # Check if ratios sum to approximately 1.0
    total = sum(adoption_data[field] for field in ratio_fields)
    tolerance = 0.01
    
    if abs(total - 1.0) > tolerance:
        raise ValidationError(
            field_name="adoption_ratios_sum",
            value=f"{total:.3f}",
            expected="sum of all adoption ratios ≈ 1.0",
            suggestion=f"Current sum is {total:.3f}, adjust ratios to sum to 1.0",
            valid_examples=[
                "initial_adopters: 0.05 + early_adopters: 0.15 + early_majority: 0.35 + late_majority: 0.35 + laggards: 0.10 = 1.00",
                "Typical distribution: 5% + 15% + 35% + 35% + 10% = 100%"
            ]
        )


def validate_financial_parameters(financial_data: Dict[str, float], section_name: str) -> None:
    """
    Validate financial parameters with context-appropriate guidance.
    
    Args:
        financial_data: Dictionary containing financial values
        section_name: Name of the configuration section
        
    Raises:
        ValidationError: If financial values are invalid
    """
    financial_fields = {
        'annual_salary': {'min': 1000, 'max': 1000000, 'typical_range': '40000-200000'},
        'license_cost_monthly': {'min': 0, 'max': 10000, 'typical_range': '10-500'},
        'setup_cost_one_time': {'min': 0, 'max': 1000000, 'typical_range': '0-50000'}
    }
    
    for field_name, constraints in financial_fields.items():
        if field_name not in financial_data:
            continue  # Optional field
            
        value = financial_data[field_name]
        
        if not isinstance(value, (int, float)):
            raise ValidationError(
                field_name=f"{section_name}.{field_name}",
                value=value,
                expected="positive number (dollar amount)",
                suggestion=f"{field_name} should be a numeric dollar amount",
                valid_examples=["1000", "50000", "120000.50"]
            )
        
        if value < constraints['min']:
            raise ValidationError(
                field_name=f"{section_name}.{field_name}",
                value=value,
                expected=f"amount >= ${constraints['min']}",
                suggestion=f"Minimum realistic value for {field_name} is ${constraints['min']}",
                valid_examples=[f"${constraints['min']}", f"${constraints['min'] * 10}"]
            )
        
        if value > constraints['max']:
            raise ValidationError(
                field_name=f"{section_name}.{field_name}",
                value=value,
                expected=f"amount <= ${constraints['max']} (typical range: ${constraints['typical_range']})",
                suggestion=f"Value seems unusually high for {field_name}. Please verify.",
                valid_examples=[f"${constraints['max'] // 10}", f"${constraints['max'] // 2}"]
            )


def validate_timeframe(timeframe_months: Union[int, float], scenario_name: str = "unknown") -> None:
    """
    Validate analysis timeframe with practical guidance.
    
    Args:
        timeframe_months: Duration of analysis in months
        scenario_name: Name of scenario for context
        
    Raises:
        ValidationError: If timeframe is invalid
    """
    if not isinstance(timeframe_months, (int, float)):
        raise ValidationError(
            field_name="timeframe_months",
            value=timeframe_months,
            expected="positive integer (number of months)",
            suggestion="Timeframe should be specified in months as a whole number",
            valid_examples=["12 (1 year)", "24 (2 years)", "36 (3 years)", "60 (5 years)"]
        )
    
    if timeframe_months <= 0:
        raise ValidationError(
            field_name="timeframe_months",
            value=timeframe_months,
            expected="positive number of months",
            suggestion="Analysis timeframe must be at least 1 month",
            valid_examples=["6 (6 months)", "12 (1 year)", "24 (2 years)"]
        )
    
    if timeframe_months < 3:
        raise ValidationError(
            field_name="timeframe_months",
            value=timeframe_months,
            expected="at least 3 months for meaningful analysis",
            suggestion="Short timeframes may not capture adoption dynamics effectively",
            valid_examples=["6 (minimum useful)", "12 (1 year)", "24 (2 years)"]
        )
    
    if timeframe_months > 120:  # 10 years
        raise ValidationError(
            field_name="timeframe_months",
            value=timeframe_months,
            expected="reasonable timeframe (typically ≤ 10 years)",
            suggestion="Very long timeframes may have high uncertainty in predictions",
            valid_examples=["24 (2 years)", "36 (3 years)", "60 (5 years)"]
        )


def suggest_parameter_fixes(error_context: str, current_value: Any) -> List[str]:
    """
    Provide contextual suggestions for fixing common parameter errors.
    
    Args:
        error_context: Description of what went wrong
        current_value: The problematic value
        
    Returns:
        List of specific suggestions for fixing the issue
    """
    suggestions = []
    
    if "ratio" in error_context.lower():
        suggestions.extend([
            "Convert percentages to decimals (e.g., 25% → 0.25)",
            "Ensure all ratio values are between 0.0 and 1.0",
            "Check that adoption ratios sum to 1.0",
            "Use decimal notation: 0.05 for 5%, 0.15 for 15%"
        ])
    
    elif "salary" in error_context.lower():
        suggestions.extend([
            "Use annual salary in dollars (e.g., 75000 for $75k/year)",
            "Consider total compensation including benefits",
            "Check if value is in correct currency",
            "Typical range: $40,000 - $200,000 for developers"
        ])
    
    elif "cost" in error_context.lower():
        suggestions.extend([
            "Enter costs in dollars without currency symbols",
            "For monthly costs, use per-user amounts",
            "Include any setup, training, or maintenance costs",
            "Check vendor pricing documentation"
        ])
    
    elif "team" in error_context.lower():
        suggestions.extend([
            "Count only developers who will use AI tools",
            "Use headcount or FTE (full-time equivalent)",
            "Don't include managers or non-development roles",
            "Consider part-time staff as fractional (e.g., 2.5)"
        ])
    
    else:
        suggestions.extend([
            "Check data type (number vs. string)",
            "Verify value is in expected units",
            "Compare with working examples",
            "Review parameter documentation"
        ])
    
    return suggestions