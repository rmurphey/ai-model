"""
Tests for validation_helpers.py - User-friendly parameter validation functions
"""

import pytest
from src.utils.validation_helpers import (
    validate_scenario_config, validate_team_size, validate_adoption_ratios,
    validate_financial_parameters, validate_timeframe, suggest_parameter_fixes
)
from src.utils.exceptions import ValidationError, ConfigurationError


class TestValidateScenarioConfig:
    """Test complete scenario configuration validation"""
    
    def test_valid_scenario_config(self):
        """Test validation of valid scenario configuration"""
        valid_config = {
            'baseline': {'profile': 'enterprise'},
            'adoption': {'scenario': 'grassroots'},
            'impact': {'scenario': 'moderate'},
            'costs': {'scenario': 'enterprise'},
            'timeframe_months': 36
        }
        # Should not raise any exceptions
        validate_scenario_config(valid_config, "test_scenario")
        
    def test_missing_top_level_sections(self):
        """Test error when top-level sections are missing"""
        incomplete_config = {
            'baseline': {'profile': 'enterprise'},
            'adoption': {'scenario': 'grassroots'}
            # Missing impact, costs, timeframe_months
        }
        
        with pytest.raises(ConfigurationError, match="missing required sections"):
            validate_scenario_config(incomplete_config, "test_scenario")
            
    def test_missing_section_fields(self):
        """Test error when section fields are missing"""
        config_with_detailed_baseline = {
            'baseline': {
                'team_size': 50,
                # Missing annual_salary, total_working_days
            },
            'adoption': {'scenario': 'grassroots'},
            'impact': {'scenario': 'moderate'},
            'costs': {'scenario': 'enterprise'},
            'timeframe_months': 36
        }
        
        with pytest.raises(ConfigurationError, match="missing fields"):
            validate_scenario_config(config_with_detailed_baseline, "test_scenario")


class TestValidateTeamSize:
    """Test team size validation with business context"""
    
    def test_valid_team_sizes(self):
        """Test valid team sizes pass validation"""
        validate_team_size(1)      # Single developer
        validate_team_size(5)      # Small team
        validate_team_size(50)     # Medium team
        validate_team_size(5.5)    # Part-time equivalents
        validate_team_size(100)    # Large team
        
    def test_zero_team_size(self):
        """Test zero team size raises ValidationError"""
        with pytest.raises(ValidationError, match="positive number greater than 0"):
            validate_team_size(0)
            
    def test_negative_team_size(self):
        """Test negative team size raises ValidationError"""
        with pytest.raises(ValidationError, match="positive number greater than 0"):
            validate_team_size(-5)
            
    def test_very_large_team_size(self):
        """Test unrealistically large team size raises ValidationError"""
        with pytest.raises(ValidationError, match="reasonable team size"):
            validate_team_size(15000)
            
    def test_non_numeric_team_size(self):
        """Test non-numeric team size raises ValidationError"""
        with pytest.raises(ValidationError, match="positive integer or float"):
            validate_team_size("fifty")
            
        with pytest.raises(ValidationError, match="positive integer or float"):
            validate_team_size(None)


class TestValidateAdoptionRatios:
    """Test adoption ratio validation and sum checking"""
    
    def test_valid_adoption_ratios(self):
        """Test valid adoption ratios that sum to 1.0"""
        valid_ratios = {
            'initial_adopters': 0.05,
            'early_adopters': 0.15,
            'early_majority': 0.35,
            'late_majority': 0.35,
            'laggards': 0.10
        }
        # Should not raise any exceptions
        validate_adoption_ratios(valid_ratios, "test_scenario")
        
    def test_missing_adoption_fields(self):
        """Test error when adoption ratio fields are missing"""
        incomplete_ratios = {
            'initial_adopters': 0.05,
            'early_adopters': 0.15,
            # Missing early_majority, late_majority, laggards
        }
        
        with pytest.raises(ConfigurationError, match="missing fields"):
            validate_adoption_ratios(incomplete_ratios, "test_scenario")
            
    def test_non_numeric_adoption_ratios(self):
        """Test error when adoption ratios are not numeric"""
        invalid_ratios = {
            'initial_adopters': "five percent",
            'early_adopters': 0.15,
            'early_majority': 0.35,
            'late_majority': 0.35,
            'laggards': 0.10
        }
        
        with pytest.raises(ValidationError, match="number between 0.0 and 1.0"):
            validate_adoption_ratios(invalid_ratios, "test_scenario")
            
    def test_out_of_range_adoption_ratios(self):
        """Test error when adoption ratios are outside 0-1 range"""
        invalid_ratios = {
            'initial_adopters': -0.05,  # Negative
            'early_adopters': 0.15,
            'early_majority': 0.35,
            'late_majority': 0.35,
            'laggards': 0.10
        }
        
        with pytest.raises(ValidationError, match="ratio between 0.0 and 1.0"):
            validate_adoption_ratios(invalid_ratios, "test_scenario")
            
        invalid_ratios['initial_adopters'] = 1.5  # Greater than 1
        with pytest.raises(ValidationError, match="ratio between 0.0 and 1.0"):
            validate_adoption_ratios(invalid_ratios, "test_scenario")
            
    def test_ratios_dont_sum_to_one(self):
        """Test error when adoption ratios don't sum to approximately 1.0"""
        ratios_sum_too_high = {
            'initial_adopters': 0.1,
            'early_adopters': 0.2,
            'early_majority': 0.4,
            'late_majority': 0.4,
            'laggards': 0.2  # Sum = 1.3
        }
        
        with pytest.raises(ValidationError, match="sum of all adoption ratios"):
            validate_adoption_ratios(ratios_sum_too_high, "test_scenario")
            
        ratios_sum_too_low = {
            'initial_adopters': 0.05,
            'early_adopters': 0.1,
            'early_majority': 0.2,
            'late_majority': 0.2,
            'laggards': 0.1  # Sum = 0.65
        }
        
        with pytest.raises(ValidationError, match="sum of all adoption ratios"):
            validate_adoption_ratios(ratios_sum_too_low, "test_scenario")


class TestValidateFinancialParameters:
    """Test financial parameter validation with realistic bounds"""
    
    def test_valid_financial_parameters(self):
        """Test valid financial parameters"""
        valid_params = {
            'annual_salary': 75000,
            'license_cost_monthly': 25,
            'setup_cost_one_time': 5000
        }
        # Should not raise any exceptions
        validate_financial_parameters(valid_params, "baseline")
        
    def test_non_numeric_financial_values(self):
        """Test error for non-numeric financial values"""
        invalid_params = {
            'annual_salary': "seventy-five thousand",
            'license_cost_monthly': 25
        }
        
        with pytest.raises(ValidationError, match="positive number \\(dollar amount\\)"):
            validate_financial_parameters(invalid_params, "baseline")
            
    def test_unrealistically_low_salary(self):
        """Test error for unrealistically low salary"""
        invalid_params = {
            'annual_salary': 500  # Too low
        }
        
        with pytest.raises(ValidationError, match="amount >= \\$1000"):
            validate_financial_parameters(invalid_params, "baseline")
            
    def test_unrealistically_high_salary(self):
        """Test error for unrealistically high salary"""
        invalid_params = {
            'annual_salary': 1500000  # Too high
        }
        
        with pytest.raises(ValidationError, match="amount <= \\$1000000"):
            validate_financial_parameters(invalid_params, "baseline")
            
    def test_negative_financial_values(self):
        """Test error for negative financial values"""
        invalid_params = {
            'license_cost_monthly': -10
        }
        
        with pytest.raises(ValidationError, match="amount >= \\$0"):
            validate_financial_parameters(invalid_params, "costs")


class TestValidateTimeframe:
    """Test timeframe validation with practical business constraints"""
    
    def test_valid_timeframes(self):
        """Test valid analysis timeframes"""
        validate_timeframe(6)   # 6 months
        validate_timeframe(12)  # 1 year
        validate_timeframe(24)  # 2 years
        validate_timeframe(36)  # 3 years
        validate_timeframe(60)  # 5 years
        
    def test_non_numeric_timeframe(self):
        """Test error for non-numeric timeframe"""
        with pytest.raises(ValidationError, match="positive integer \\(number of months\\)"):
            validate_timeframe("two years")
            
    def test_zero_or_negative_timeframe(self):
        """Test error for zero or negative timeframe"""
        with pytest.raises(ValidationError, match="positive number of months"):
            validate_timeframe(0)
            
        with pytest.raises(ValidationError, match="positive number of months"):
            validate_timeframe(-6)
            
    def test_very_short_timeframe(self):
        """Test error for very short timeframes"""
        with pytest.raises(ValidationError, match="at least 3 months"):
            validate_timeframe(1)
            
        with pytest.raises(ValidationError, match="at least 3 months"):
            validate_timeframe(2)
            
    def test_very_long_timeframe(self):
        """Test error for unrealistically long timeframes"""
        with pytest.raises(ValidationError, match="reasonable timeframe"):
            validate_timeframe(150)  # Over 10 years


class TestSuggestParameterFixes:
    """Test contextual parameter fix suggestions"""
    
    def test_ratio_context_suggestions(self):
        """Test suggestions for ratio-related errors"""
        suggestions = suggest_parameter_fixes("invalid ratio", 1.5)
        assert "Convert percentages to decimals" in suggestions
        assert "0.05 for 5%, 0.15 for 15%" in suggestions
        
    def test_salary_context_suggestions(self):
        """Test suggestions for salary-related errors"""
        suggestions = suggest_parameter_fixes("invalid salary", 500)
        assert "Use annual salary in dollars" in suggestions
        assert "$40,000 - $200,000 for developers" in suggestions
        
    def test_cost_context_suggestions(self):
        """Test suggestions for cost-related errors"""
        suggestions = suggest_parameter_fixes("invalid cost", -100)
        assert "Enter costs in dollars without currency symbols" in suggestions
        assert "For monthly costs, use per-user amounts" in suggestions
        
    def test_team_context_suggestions(self):
        """Test suggestions for team-related errors"""
        suggestions = suggest_parameter_fixes("invalid team size", 0)
        assert "Count only developers who will use AI tools" in suggestions
        assert "Use headcount or FTE" in suggestions
        
    def test_generic_context_suggestions(self):
        """Test generic suggestions for unknown error types"""
        suggestions = suggest_parameter_fixes("unknown error", "bad_value")
        assert "Check data type (number vs. string)" in suggestions
        assert "Review parameter documentation" in suggestions