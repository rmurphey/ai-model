"""
Comprehensive tests for impact_model.py - Core business logic calculations
"""

import pytest
import numpy as np
from dataclasses import asdict

from src.model.impact_model import (
    ImpactFactors, BusinessImpact, create_impact_scenario,
    calculate_task_specific_impact
)
from src.model.baseline import create_industry_baseline
from src.utils.exceptions import ValidationError, CalculationError


class TestImpactFactors:
    """Test ImpactFactors dataclass validation and creation"""
    
    def test_valid_impact_factors_creation(self):
        """Test creating valid ImpactFactors"""
        factors = ImpactFactors(
            feature_cycle_reduction=0.25,
            bug_fix_reduction=0.35,
            onboarding_reduction=0.40,
            pr_review_reduction=0.50,
            defect_reduction=0.30,
            incident_reduction=0.25,
            rework_reduction=0.40,
            feature_capacity_gain=0.10,
            tech_debt_capacity_gain=0.05,
            boilerplate_effectiveness=0.85,
            test_generation_effectiveness=0.70,
            documentation_effectiveness=0.80,
            code_review_effectiveness=0.60,
            debugging_effectiveness=0.50,
            junior_multiplier=1.5,
            mid_multiplier=1.3,
            senior_multiplier=1.2
        )
        
        # All fields should be accessible
        assert factors.feature_cycle_reduction == 0.25
        assert factors.junior_multiplier == 1.5
        
    def test_invalid_reduction_ratios(self):
        """Test that invalid reduction ratios raise ValidationError"""
        with pytest.raises(CalculationError, match="must be between 0.0 and 1.0"):
            ImpactFactors(
                feature_cycle_reduction=1.5,  # Invalid: > 1.0
                bug_fix_reduction=0.35,
                onboarding_reduction=0.40,
                pr_review_reduction=0.50,
                defect_reduction=0.30,
                incident_reduction=0.25,
                rework_reduction=0.40,
                feature_capacity_gain=0.10,
                tech_debt_capacity_gain=0.05,
                boilerplate_effectiveness=0.85,
                test_generation_effectiveness=0.70,
                documentation_effectiveness=0.80,
                code_review_effectiveness=0.60,
                debugging_effectiveness=0.50,
                junior_multiplier=1.5,
                mid_multiplier=1.3,
                senior_multiplier=1.2
            )
            
    def test_invalid_effectiveness_ratios(self):
        """Test that invalid effectiveness ratios raise ValidationError"""
        with pytest.raises(CalculationError, match="must be between 0.0 and 1.0"):
            ImpactFactors(
                feature_cycle_reduction=0.25,
                bug_fix_reduction=0.35,
                onboarding_reduction=0.40,
                pr_review_reduction=0.50,
                defect_reduction=0.30,
                incident_reduction=0.25,
                rework_reduction=0.40,
                feature_capacity_gain=0.10,
                tech_debt_capacity_gain=0.05,
                boilerplate_effectiveness=1.5,  # Invalid: > 1.0
                test_generation_effectiveness=0.70,
                documentation_effectiveness=0.80,
                code_review_effectiveness=0.60,
                debugging_effectiveness=0.50,
                junior_multiplier=1.5,
                mid_multiplier=1.3,
                senior_multiplier=1.2
            )
            
    def test_invalid_multipliers(self):
        """Test that invalid multipliers raise ValidationError"""
        with pytest.raises(CalculationError):
            ImpactFactors(
                feature_cycle_reduction=0.25,
                bug_fix_reduction=0.35,
                onboarding_reduction=0.40,
                pr_review_reduction=0.50,
                defect_reduction=0.30,
                incident_reduction=0.25,
                rework_reduction=0.40,
                feature_capacity_gain=0.10,
                tech_debt_capacity_gain=0.05,
                boilerplate_effectiveness=0.85,
                test_generation_effectiveness=0.70,
                documentation_effectiveness=0.80,
                code_review_effectiveness=0.60,
                debugging_effectiveness=0.50,
                junior_multiplier=-0.5,  # Invalid: negative
                mid_multiplier=1.3,
                senior_multiplier=1.2
            )


class TestBusinessImpact:
    """Test BusinessImpact calculations"""
    
    @pytest.fixture
    def baseline_metrics(self):
        """Standard baseline metrics for testing"""
        return create_industry_baseline("enterprise")
    
    @pytest.fixture
    def impact_factors(self):
        """Standard impact factors for testing"""
        return create_impact_scenario("moderate")
    
    @pytest.fixture
    def business_impact(self, baseline_metrics, impact_factors):
        """BusinessImpact instance for testing"""
        return BusinessImpact(
            baseline=baseline_metrics,
            factors=impact_factors,
            adoption_rate=0.5  # 50% adoption
        )
    
    def test_business_impact_creation(self, business_impact):
        """Test that BusinessImpact can be created"""
        assert business_impact.adoption_rate == 0.5
        assert business_impact.baseline.team_size == 50
        assert business_impact.factors.feature_cycle_reduction == 0.25
        
    def test_calculate_time_value_structure(self, business_impact):
        """Test that time value calculation returns correct structure"""
        time_value = business_impact.calculate_time_value()
        
        # Check all required keys exist
        required_keys = [
            "feature_acceleration_value",
            "bug_fix_acceleration_value", 
            "onboarding_acceleration_value",
            "total_time_value"
        ]
        
        for key in required_keys:
            assert key in time_value, f"Missing key: {key}"
            assert isinstance(time_value[key], (int, float)), f"{key} should be numeric"
            assert time_value[key] >= 0, f"{key} should be non-negative"
    
    def test_calculate_time_value_logic(self, business_impact):
        """Test time value calculation logic"""
        time_value = business_impact.calculate_time_value()
        
        # Total should equal sum of components
        expected_total = (
            time_value["feature_acceleration_value"] +
            time_value["bug_fix_acceleration_value"] +
            time_value["onboarding_acceleration_value"]
        )
        
        assert abs(time_value["total_time_value"] - expected_total) < 1, \
            "Total time value should equal sum of components"
    
    def test_calculate_quality_value_structure(self, business_impact):
        """Test that quality value calculation returns correct structure"""
        quality_value = business_impact.calculate_quality_value()
        
        required_keys = [
            "defect_reduction_value",
            "incident_reduction_value",
            "rework_reduction_value",
            "total_quality_value"
        ]
        
        for key in required_keys:
            assert key in quality_value, f"Missing key: {key}"
            assert isinstance(quality_value[key], (int, float)), f"{key} should be numeric"
            assert quality_value[key] >= 0, f"{key} should be non-negative"
    
    def test_calculate_capacity_value_structure(self, business_impact):
        """Test that capacity value calculation returns correct structure"""
        capacity_value = business_impact.calculate_capacity_value()
        
        required_keys = [
            "feature_capacity_value",
            "tech_debt_value",
            "context_switch_value",
            "total_capacity_value"
        ]
        
        for key in required_keys:
            assert key in capacity_value, f"Missing key: {key}"
            assert isinstance(capacity_value[key], (int, float)), f"{key} should be numeric"
    
    def test_calculate_strategic_value_structure(self, business_impact):
        """Test that strategic value calculation returns correct structure"""
        strategic_value = business_impact.calculate_strategic_value()
        
        required_keys = [
            "retention_value",
            "innovation_value", 
            "competitive_value",
            "junior_boost_value",
            "total_strategic_value"
        ]
        
        for key in required_keys:
            assert key in strategic_value, f"Missing key: {key}"
            assert isinstance(strategic_value[key], (int, float)), f"{key} should be numeric"
            assert strategic_value[key] >= 0, f"{key} should be non-negative"
    
    def test_calculate_total_impact_structure(self, business_impact):
        """Test that total impact calculation returns correct structure"""
        total_impact = business_impact.calculate_total_impact()
        
        required_keys = [
            "time_value",
            "quality_value",
            "capacity_value", 
            "strategic_value",
            "total_annual_value",
            "value_per_developer",
            "value_as_percent_of_cost"
        ]
        
        for key in required_keys:
            assert key in total_impact, f"Missing key: {key}"
            assert isinstance(total_impact[key], (int, float)), f"{key} should be numeric"
    
    def test_total_impact_consistency(self, business_impact):
        """Test that total impact values are internally consistent"""
        total_impact = business_impact.calculate_total_impact()
        
        # Total annual value should equal sum of components
        expected_total = (
            total_impact["time_value"] +
            total_impact["quality_value"] +
            total_impact["capacity_value"] +
            total_impact["strategic_value"]
        )
        
        assert abs(total_impact["total_annual_value"] - expected_total) < 1, \
            "Total annual value should equal sum of all value components"
        
        # Value per developer should make sense
        expected_per_dev = total_impact["total_annual_value"] / business_impact.baseline.team_size
        assert abs(total_impact["value_per_developer"] - expected_per_dev) < 1, \
            "Value per developer calculation inconsistency"
    
    def test_adoption_rate_impact(self, baseline_metrics, impact_factors):
        """Test that adoption rate affects calculated values"""
        low_adoption = BusinessImpact(baseline_metrics, impact_factors, 0.1)
        high_adoption = BusinessImpact(baseline_metrics, impact_factors, 0.9)
        
        low_value = low_adoption.calculate_total_impact()["total_annual_value"]
        high_value = high_adoption.calculate_total_impact()["total_annual_value"]
        
        assert high_value > low_value, "Higher adoption should yield higher value"
        
        # Relationship should be roughly proportional
        ratio = high_value / low_value if low_value > 0 else float('inf')
        assert 5 < ratio < 15, f"Value ratio {ratio} seems unrealistic for 9x adoption difference"
    
    def test_zero_adoption_edge_case(self, baseline_metrics, impact_factors):
        """Test edge case with zero adoption"""
        zero_adoption = BusinessImpact(baseline_metrics, impact_factors, 0.0)
        impact = zero_adoption.calculate_total_impact()
        
        # With zero adoption, most values should be zero or very small
        assert impact["total_annual_value"] >= 0
        assert impact["value_per_developer"] >= 0
    
    def test_full_adoption_edge_case(self, baseline_metrics, impact_factors):
        """Test edge case with full adoption"""
        full_adoption = BusinessImpact(baseline_metrics, impact_factors, 1.0)
        impact = full_adoption.calculate_total_impact()
        
        # Values should be reasonable and positive
        assert impact["total_annual_value"] > 0
        assert impact["value_per_developer"] > 0
        
        # Shouldn't exceed team cost by an unreasonable amount
        value_to_cost_ratio = impact["value_as_percent_of_cost"]
        assert 0 <= value_to_cost_ratio <= 300, \
            f"Value to cost ratio {value_to_cost_ratio}% seems unrealistic"


class TestCreateImpactScenario:
    """Test scenario creation functions"""
    
    def test_conservative_scenario(self):
        """Test conservative impact scenario"""
        factors = create_impact_scenario("conservative")
        
        assert isinstance(factors, ImpactFactors)
        assert factors.feature_cycle_reduction <= 0.15  # Conservative improvements
        assert factors.junior_multiplier >= 1.0  # Some benefit to juniors
        
    def test_moderate_scenario(self):
        """Test moderate impact scenario"""
        factors = create_impact_scenario("moderate")
        
        assert isinstance(factors, ImpactFactors)
        assert 0.2 <= factors.feature_cycle_reduction <= 0.3  # Moderate improvements
        assert factors.junior_multiplier >= 1.3  # Good benefit to juniors
        
    def test_aggressive_scenario(self):
        """Test aggressive impact scenario"""
        factors = create_impact_scenario("aggressive")
        
        assert isinstance(factors, ImpactFactors)
        assert factors.feature_cycle_reduction >= 0.35  # Aggressive improvements
        assert factors.junior_multiplier >= 1.5  # High benefit to juniors
        
    def test_default_scenario(self):
        """Test that default returns moderate scenario"""
        default_factors = create_impact_scenario()
        moderate_factors = create_impact_scenario("moderate")
        
        assert asdict(default_factors) == asdict(moderate_factors)
        
    def test_invalid_scenario(self):
        """Test invalid scenario returns moderate scenario"""
        invalid_factors = create_impact_scenario("nonexistent")
        moderate_factors = create_impact_scenario("moderate")
        
        assert asdict(invalid_factors) == asdict(moderate_factors)


class TestCalculateTaskSpecificImpact:
    """Test task-specific impact calculations"""
    
    @pytest.fixture
    def baseline_metrics(self):
        return create_industry_baseline("enterprise")
    
    @pytest.fixture
    def impact_factors(self):
        return create_impact_scenario("moderate")
    
    @pytest.fixture
    def task_distribution(self):
        """Typical task distribution for developers"""
        return {
            "boilerplate": 0.15,
            "testing": 0.20,
            "documentation": 0.10,
            "code_review": 0.15,
            "debugging": 0.15,
            "feature_development": 0.20,
            "refactoring": 0.05
        }
    
    def test_task_specific_impact_structure(self, baseline_metrics, impact_factors, task_distribution):
        """Test task-specific impact calculation structure"""
        result = calculate_task_specific_impact(baseline_metrics, impact_factors, task_distribution)
        
        required_keys = [
            "weighted_effectiveness",
            "task_time_savings",
            "total_task_value"
        ]
        
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
        
        assert isinstance(result["weighted_effectiveness"], (int, float))
        assert isinstance(result["task_time_savings"], dict)
        assert isinstance(result["total_task_value"], (int, float))
    
    def test_task_specific_calculations(self, baseline_metrics, impact_factors, task_distribution):
        """Test task-specific calculation logic"""
        result = calculate_task_specific_impact(baseline_metrics, impact_factors, task_distribution)
        
        # Weighted effectiveness should be between 0 and 1
        assert 0 <= result["weighted_effectiveness"] <= 1
        
        # Total task value should be positive
        assert result["total_task_value"] >= 0
        
        # Each task should have time savings calculated
        for task in task_distribution.keys():
            if task in result["task_time_savings"]:
                assert result["task_time_savings"][task] >= 0
    
    def test_empty_task_distribution(self, baseline_metrics, impact_factors):
        """Test edge case with empty task distribution"""
        empty_distribution = {}
        result = calculate_task_specific_impact(baseline_metrics, impact_factors, empty_distribution)
        
        assert result["weighted_effectiveness"] == 0
        assert result["total_task_value"] == 0
        assert result["task_time_savings"] == {}
    
    def test_high_effectiveness_tasks(self, baseline_metrics, impact_factors):
        """Test with tasks that have high AI effectiveness"""
        high_effectiveness_tasks = {
            "boilerplate": 0.5,  # AI is very good at boilerplate
            "testing": 0.3,      # AI is good at test generation
            "documentation": 0.2  # AI is good at documentation
        }
        
        result = calculate_task_specific_impact(baseline_metrics, impact_factors, high_effectiveness_tasks)
        
        # Should have high weighted effectiveness
        assert result["weighted_effectiveness"] > 0.6
        assert result["total_task_value"] > 0


class TestImpactModelEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_team_size(self):
        """Test with zero team size baseline"""
        baseline = create_industry_baseline("enterprise")
        baseline.team_size = 0  # This should cause validation error
        factors = create_impact_scenario("moderate")
        
        # The baseline should validate team_size on creation
        # But if we manually set it to 0, impact calculations should handle it gracefully
        impact = BusinessImpact(baseline, factors, 0.5)
        result = impact.calculate_total_impact()
        
        # Should handle division by zero gracefully
        assert result["value_per_developer"] == 0
    
    def test_extreme_impact_factors(self):
        """Test with extreme but valid impact factors"""
        baseline = create_industry_baseline("startup")
        
        # Create extreme but valid factors
        extreme_factors = ImpactFactors(
            feature_cycle_reduction=0.9,   # 90% improvement
            bug_fix_reduction=0.9,
            onboarding_reduction=0.9,
            pr_review_reduction=0.9,
            defect_reduction=0.9,
            incident_reduction=0.9,
            rework_reduction=0.9,
            feature_capacity_gain=0.3,     # 30% more capacity
            tech_debt_capacity_gain=0.2,
            boilerplate_effectiveness=0.99,
            test_generation_effectiveness=0.99,
            documentation_effectiveness=0.99,
            code_review_effectiveness=0.99,
            debugging_effectiveness=0.99,
            junior_multiplier=3.0,
            mid_multiplier=2.0,
            senior_multiplier=1.5
        )
        
        impact = BusinessImpact(baseline, extreme_factors, 1.0)
        result = impact.calculate_total_impact()
        
        # Should still produce reasonable results
        assert result["total_annual_value"] > 0
        assert result["value_per_developer"] > 0
        # Very high impact but should be bounded to reasonable levels
        assert result["value_as_percent_of_cost"] < 2000  # Less than 20x cost