"""
Mathematical utility functions for safe calculations in AI impact analysis.
Provides division by zero protection and other mathematical safeguards.
"""

import numpy as np
from typing import Union, Optional
from .exceptions import CalculationError


def safe_divide(numerator: Union[float, np.ndarray], 
                denominator: Union[float, np.ndarray], 
                default: Union[float, np.ndarray] = 0.0,
                context: str = None) -> Union[float, np.ndarray]:
    """
    Safely perform division with zero-denominator protection.
    
    Args:
        numerator: Value to be divided
        denominator: Value to divide by
        default: Value to return when denominator is zero
        context: Description of the calculation for error reporting
        
    Returns:
        Result of division or default value if denominator is zero
        
    Raises:
        CalculationError: If calculation parameters are invalid
    """
    if isinstance(denominator, (int, float)):
        if denominator == 0:
            if context:
                print(f"Warning: Division by zero in {context}, using default value {default}")
            return default
        return numerator / denominator
    
    elif isinstance(denominator, np.ndarray):
        # Handle numpy arrays with element-wise division
        result = np.where(denominator != 0, numerator / denominator, default)
        
        zero_count = np.sum(denominator == 0)
        if zero_count > 0 and context:
            print(f"Warning: {zero_count} zero values in {context}, using default value {default}")
        
        return result
    
    else:
        raise CalculationError(
            operation="division",
            reason=f"Unsupported type for denominator: {type(denominator)}",
            context=context
        )


def safe_percentage(value: Union[float, np.ndarray], 
                   total: Union[float, np.ndarray],
                   default: float = 0.0,
                   context: str = None) -> Union[float, np.ndarray]:
    """
    Safely calculate percentage with zero-total protection.
    
    Args:
        value: Part value
        total: Total value
        default: Default percentage when total is zero
        context: Description for error reporting
        
    Returns:
        Percentage (0-100) or default if total is zero
    """
    return safe_divide(value * 100, total, default, f"percentage calculation ({context})")


def validate_positive(value: Union[float, int], 
                     field_name: str, 
                     allow_zero: bool = False) -> None:
    """
    Validate that a value is positive (or non-negative if allow_zero=True).
    
    Args:
        value: Value to validate
        field_name: Name of the field for error reporting
        allow_zero: Whether zero is allowed
        
    Raises:
        CalculationError: If value is not positive (or negative when allow_zero=True)
    """
    if allow_zero and value < 0:
        raise CalculationError(
            operation="validation",
            reason=f"{field_name} must be non-negative, got {value}",
            context=field_name
        )
    elif not allow_zero and value <= 0:
        raise CalculationError(
            operation="validation", 
            reason=f"{field_name} must be positive, got {value}",
            context=field_name
        )


def validate_ratio(value: float, 
                  field_name: str, 
                  min_val: float = 0.0, 
                  max_val: float = 1.0) -> None:
    """
    Validate that a value is within ratio bounds (typically 0-1).
    
    Args:
        value: Value to validate
        field_name: Name of the field for error reporting
        min_val: Minimum allowed value (default 0.0)
        max_val: Maximum allowed value (default 1.0)
        
    Raises:
        CalculationError: If value is outside the valid range
    """
    if not (min_val <= value <= max_val):
        raise CalculationError(
            operation="validation",
            reason=f"{field_name} must be between {min_val} and {max_val}, got {value}",
            context=field_name
        )


def safe_mean(values: np.ndarray, 
              default: float = 0.0,
              context: str = None) -> float:
    """
    Safely calculate mean with empty array protection.
    
    Args:
        values: Array of values
        default: Default value for empty arrays
        context: Description for error reporting
        
    Returns:
        Mean of values or default if array is empty
    """
    if len(values) == 0:
        if context:
            print(f"Warning: Empty array in mean calculation ({context}), using default {default}")
        return default
    
    return np.mean(values)


def safe_sum(values: np.ndarray,
             context: str = None) -> float:
    """
    Safely calculate sum with validation.
    
    Args:
        values: Array of values to sum
        context: Description for error reporting
        
    Returns:
        Sum of values
    """
    if len(values) == 0:
        if context:
            print(f"Warning: Empty array in sum calculation ({context}), returning 0")
        return 0.0
    
    return np.sum(values)


def validate_ratios_sum_to_one(ratios: dict, 
                              tolerance: float = 0.01,
                              context: str = None) -> None:
    """
    Validate that a dictionary of ratios sums to approximately 1.0.
    
    Args:
        ratios: Dictionary of ratio values
        tolerance: Acceptable deviation from 1.0
        context: Description for error reporting
        
    Raises:
        CalculationError: If ratios don't sum to approximately 1.0
    """
    total = sum(ratios.values())
    if abs(total - 1.0) > tolerance:
        raise CalculationError(
            operation="validation",
            reason=f"Ratios must sum to 1.0 (±{tolerance}), got {total:.3f}",
            context=f"ratio validation ({context})" if context else "ratio validation"
        )


def safe_log(value: Union[float, np.ndarray],
             default: float = 0.0,
             context: str = None) -> Union[float, np.ndarray]:
    """
    Safely calculate natural logarithm with non-positive value protection.
    
    Args:
        value: Value to take log of
        default: Default value for non-positive inputs
        context: Description for error reporting
        
    Returns:
        Natural log of value or default for non-positive values
    """
    if isinstance(value, (int, float)):
        if value <= 0:
            if context:
                print(f"Warning: Non-positive value in log calculation ({context}), using default {default}")
            return default
        return np.log(value)
    
    elif isinstance(value, np.ndarray):
        result = np.where(value > 0, np.log(value), default)
        
        invalid_count = np.sum(value <= 0)
        if invalid_count > 0 and context:
            print(f"Warning: {invalid_count} non-positive values in log calculation ({context}), using default {default}")
        
        return result
    
    else:
        raise CalculationError(
            operation="logarithm",
            reason=f"Unsupported type: {type(value)}",
            context=context
        )