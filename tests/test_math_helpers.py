"""
Tests for math_helpers.py - Critical mathematical utility functions
"""

import pytest
import numpy as np
import warnings
from src.utils.math_helpers import (
    safe_divide, validate_positive, validate_ratio, safe_percentage,
    safe_mean, safe_sum, safe_log
)
from src.utils.exceptions import CalculationError


class TestSafeDivide:
    """Test safe division with zero-denominator protection"""
    
    def test_normal_division(self):
        """Test normal division cases"""
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(7, 3) == pytest.approx(2.333, rel=1e-3)
        assert safe_divide(0, 5) == 0.0
        
    def test_zero_denominator_scalar(self):
        """Test division by zero with scalar values"""
        assert safe_divide(10, 0) == 0.0  # default
        assert safe_divide(10, 0, default=999) == 999
        assert safe_divide(0, 0, default=-1) == -1
        
    def test_zero_denominator_with_context(self):
        """Test zero denominator generates warning with context"""
        with pytest.warns(UserWarning, match="Division by zero in test_context"):
            result = safe_divide(10, 0, context="test_context")
            assert result == 0.0
            
    def test_array_division(self):
        """Test division with numpy arrays"""
        numerator = np.array([10, 20, 30])
        denominator = np.array([2, 4, 5])
        result = safe_divide(numerator, denominator)
        expected = np.array([5, 5, 6])
        np.testing.assert_array_equal(result, expected)
        
    def test_array_with_zero_denominators(self):
        """Test array division with some zero denominators"""
        numerator = np.array([10, 20, 30])
        denominator = np.array([2, 0, 5])
        result = safe_divide(numerator, denominator, default=999)
        expected = np.array([5, 999, 6])
        np.testing.assert_array_equal(result, expected)
        
    def test_array_zero_warning(self):
        """Test that array division with zeros generates appropriate warning"""
        numerator = np.array([10, 20, 30])
        denominator = np.array([2, 0, 0])
        
        with pytest.warns(UserWarning, match="2 zero values in array_test"):
            result = safe_divide(numerator, denominator, context="array_test")
            expected = np.array([5, 0, 0])
            np.testing.assert_array_equal(result, expected)


class TestValidatePositive:
    """Test positive number validation"""
    
    def test_valid_positive_numbers(self):
        """Test valid positive numbers pass validation"""
        # These should not raise exceptions
        validate_positive(1.0, "test")
        validate_positive(0.001, "test")
        validate_positive(1000, "test")
        
    def test_zero_raises_error(self):
        """Test that zero raises CalculationError"""
        with pytest.raises(CalculationError, match="must be positive"):
            validate_positive(0, "test_field")
            
    def test_negative_raises_error(self):
        """Test that negative numbers raise CalculationError"""
        with pytest.raises(CalculationError, match="must be positive"):
            validate_positive(-1, "test_field")
            
        with pytest.raises(CalculationError, match="must be positive"):
            validate_positive(-0.001, "test_field")


class TestValidateRatio:
    """Test ratio validation (0-1 range)"""
    
    def test_valid_ratios(self):
        """Test valid ratios in 0-1 range"""
        # These should not raise exceptions
        validate_ratio(0.0, "test")
        validate_ratio(0.5, "test")
        validate_ratio(1.0, "test")
        
    def test_invalid_negative_ratio(self):
        """Test negative ratios raise error"""
        with pytest.raises(CalculationError, match="must be between 0.0 and 1.0"):
            validate_ratio(-0.1, "test_ratio")
            
    def test_invalid_too_large_ratio(self):
        """Test ratios > 1 raise error"""
        with pytest.raises(CalculationError, match="must be between 0.0 and 1.0"):
            validate_ratio(1.1, "test_ratio")
            
        with pytest.raises(CalculationError, match="must be between 0.0 and 1.0"):
            validate_ratio(2.0, "test_ratio")


class TestSafePercentage:
    """Test safe percentage calculation"""
    
    def test_valid_percentages(self):
        """Test valid percentage calculations"""
        assert safe_percentage(50, 100) == 50.0
        assert safe_percentage(25, 100) == 25.0
        assert safe_percentage(0, 100) == 0.0
        
    def test_zero_denominator(self):
        """Test percentage with zero denominator"""
        assert safe_percentage(50, 0) == 0.0  # default behavior
        assert safe_percentage(50, 0, default=999) == 999
            
    def test_array_percentages(self):
        """Test percentage calculation with arrays"""
        numerator = np.array([25, 50, 75])
        denominator = np.array([100, 100, 100])
        result = safe_percentage(numerator, denominator)
        expected = np.array([25, 50, 75])
        np.testing.assert_array_equal(result, expected)


class TestSafeMean:
    """Test safe mean calculation with empty array protection"""
    
    def test_normal_mean(self):
        """Test normal mean calculation"""
        values = np.array([1, 2, 3, 4, 5])
        assert safe_mean(values) == 3.0
        
    def test_empty_array_default(self):
        """Test empty array returns default value"""
        empty_array = np.array([])
        assert safe_mean(empty_array) == 0.0
        assert safe_mean(empty_array, default=999) == 999
        
    def test_empty_array_warning(self):
        """Test empty array generates warning with context"""
        empty_array = np.array([])
        with pytest.warns(UserWarning, match="Empty array in mean calculation"):
            result = safe_mean(empty_array, context="test_context")
            assert result == 0.0


class TestSafeSum:
    """Test safe sum calculation with empty array protection"""
    
    def test_normal_sum(self):
        """Test normal sum calculation"""
        values = np.array([1, 2, 3, 4, 5])
        assert safe_sum(values) == 15.0
        
    def test_empty_array_returns_zero(self):
        """Test empty array returns 0"""
        empty_array = np.array([])
        assert safe_sum(empty_array) == 0.0
        
    def test_empty_array_warning(self):
        """Test empty array generates warning with context"""
        empty_array = np.array([])
        with pytest.warns(UserWarning, match="Empty array in sum calculation"):
            result = safe_sum(empty_array, context="test_context")
            assert result == 0.0


class TestSafeLog:
    """Test safe logarithm calculation with negative/zero protection"""
    
    def test_normal_log(self):
        """Test normal logarithm calculation"""
        assert safe_log(1) == 0.0  # ln(1) = 0
        assert safe_log(np.e) == pytest.approx(1.0, rel=1e-10)
        assert safe_log(10) == pytest.approx(2.303, rel=1e-3)
        
    def test_zero_value_default(self):
        """Test zero value returns default"""
        assert safe_log(0) == 0.0  # default
        assert safe_log(0, default=999) == 999
        
    def test_negative_value_default(self):
        """Test negative value returns default"""
        assert safe_log(-1) == 0.0
        assert safe_log(-5, default=-999) == -999
        
    def test_invalid_value_warning(self):
        """Test invalid values generate warnings"""
        with pytest.warns(UserWarning, match="Non-positive value in log calculation"):
            result = safe_log(0, context="test_log")
            assert result == 0.0
            
        with pytest.warns(UserWarning, match="Non-positive value in log calculation"):
            result = safe_log(-1, context="test_log")
            assert result == 0.0
            
    def test_array_log(self):
        """Test logarithm with arrays"""
        values = np.array([1, np.e, 10])
        result = safe_log(values)
        expected = np.array([0, 1, np.log(10)])
        np.testing.assert_allclose(result, expected, rtol=1e-10)
        
    def test_array_with_invalid_values(self):
        """Test array logarithm with invalid values"""
        values = np.array([1, 0, -1, np.e])
        result = safe_log(values, default=999)
        expected = np.array([0, 999, 999, 1])
        np.testing.assert_allclose(result, expected, rtol=1e-10)
        
    def test_array_invalid_warning(self):
        """Test array with invalid values generates warning"""
        values = np.array([1, 0, -1])
        with pytest.warns(UserWarning, match="2 non-positive values in log calculation"):
            result = safe_log(values, context="array_log_test")
            expected = np.array([0, 0, 0])
            np.testing.assert_allclose(result, expected)