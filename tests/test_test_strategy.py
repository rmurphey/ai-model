"""
Tests for test strategy model.
"""

import pytest
from src.model.test_strategy import (
    TestPyramid, TestAutomation, TDDStrategy, TestingCulture,
    CompleteTestStrategy, create_basic_test_strategy,
    TestingApproach, TestLevel
)
from src.utils.exceptions import ValidationError


class TestTestPyramid:
    """Test test pyramid model."""
    
    def test_valid_pyramid(self):
        """Test valid test pyramid creation."""
        pyramid = TestPyramid(
            unit_percentage=0.70,
            integration_percentage=0.20,
            e2e_percentage=0.10
        )
        
        assert pyramid.unit_percentage == 0.70
        assert pyramid.integration_percentage == 0.20
        assert pyramid.e2e_percentage == 0.10
    
    def test_invalid_pyramid_percentages(self):
        """Test that percentages must sum to 1.0."""
        with pytest.raises(ValidationError):
            TestPyramid(
                unit_percentage=0.50,
                integration_percentage=0.30,
                e2e_percentage=0.30  # Total = 1.10
            )
    
    def test_ai_effectiveness_by_level(self):
        """Test AI effectiveness varies by test level."""
        pyramid = TestPyramid()
        
        unit_effectiveness = pyramid.get_ai_effectiveness(TestLevel.UNIT)
        e2e_effectiveness = pyramid.get_ai_effectiveness(TestLevel.E2E)
        
        # AI should be better at unit tests than E2E
        assert unit_effectiveness > e2e_effectiveness


class TestTestAutomation:
    """Test test automation model."""
    
    def test_automation_validation(self):
        """Test automation parameter validation."""
        automation = TestAutomation(
            coverage_target=0.80,
            current_coverage=0.65,
            automation_percentage=0.50,
            manual_test_time=4.0,
            automated_test_time=0.1,
            maintenance_overhead=0.20
        )
        
        assert automation.coverage_target == 0.80
        assert automation.current_coverage == 0.65
    
    def test_testing_time_calculation(self):
        """Test testing time calculation with AI impact."""
        automation = TestAutomation(
            coverage_target=0.80,
            current_coverage=0.65,
            automation_percentage=0.50,
            manual_test_time=4.0,
            automated_test_time=0.1,
            maintenance_overhead=0.20
        )
        
        # No AI
        time_no_ai = automation.calculate_testing_time(1.0, 0.0)
        assert 'total_time' in time_no_ai
        assert 'automation_roi' in time_no_ai
        
        # With AI
        time_with_ai = automation.calculate_testing_time(1.0, 1.0)
        
        # AI should change testing dynamics
        assert time_with_ai['total_time'] != time_no_ai['total_time']
    
    def test_defect_detection_rate(self):
        """Test defect detection rate calculation."""
        automation = TestAutomation(
            coverage_target=0.80,
            current_coverage=0.80,  # At target
            automation_percentage=0.70,
            manual_test_time=4.0,
            automated_test_time=0.1,
            maintenance_overhead=0.20
        )
        
        detection_no_ai = automation.get_defect_detection_rate(0.0)
        detection_with_ai = automation.get_defect_detection_rate(1.0)
        
        # AI tests should be less effective
        assert detection_with_ai < detection_no_ai


class TestTDDStrategy:
    """Test TDD strategy model."""
    
    def test_tdd_validation(self):
        """Test TDD strategy validation."""
        tdd = TDDStrategy(adoption_percentage=0.30)
        assert tdd.adoption_percentage == 0.30
        
        # Invalid overhead should raise
        with pytest.raises(ValidationError):
            TDDStrategy(
                adoption_percentage=0.30,
                cycle_time_overhead=3.0  # Too high
            )
    
    def test_tdd_ai_conflict(self):
        """Test that AI conflicts with TDD."""
        tdd = TDDStrategy(adoption_percentage=0.50)
        
        impact_no_ai = tdd.calculate_impact(0.0)
        impact_with_ai = tdd.calculate_impact(1.0)
        
        # Effective TDD should decrease with AI
        assert impact_with_ai['effective_tdd_adoption'] < impact_no_ai['effective_tdd_adoption']
        
        # AI-TDD conflict should be present
        assert impact_with_ai['ai_tdd_conflict'] > 0


class TestTestingCulture:
    """Test testing culture model."""
    
    def test_culture_validation(self):
        """Test culture parameter validation."""
        culture = TestingCulture(
            testing_first_mindset=0.6,
            peer_review_thoroughness=0.7,
            regression_test_discipline=0.6,
            test_documentation_quality=0.5,
            qa_developer_ratio=0.2
        )
        
        assert culture.testing_first_mindset == 0.6
    
    def test_quality_multiplier_with_ai(self):
        """Test quality multiplier calculation with AI disruption."""
        culture = TestingCulture(
            testing_first_mindset=0.8,
            peer_review_thoroughness=0.8,
            regression_test_discipline=0.7,
            test_documentation_quality=0.6,
            qa_developer_ratio=0.2
        )
        
        quality_no_ai = culture.get_quality_multiplier(0.0)
        quality_with_ai = culture.get_quality_multiplier(1.0)
        
        # AI should disrupt testing culture
        assert quality_with_ai < quality_no_ai


class TestCompleteTestStrategy:
    """Test complete test strategy integration."""
    
    def test_comprehensive_impact_calculation(self):
        """Test comprehensive impact calculation."""
        pyramid = TestPyramid()
        automation = TestAutomation(
            coverage_target=0.80,
            current_coverage=0.65,
            automation_percentage=0.50,
            manual_test_time=4.0,
            automated_test_time=0.1,
            maintenance_overhead=0.20
        )
        tdd = TDDStrategy(adoption_percentage=0.20)
        culture = TestingCulture(
            testing_first_mindset=0.6,
            peer_review_thoroughness=0.7,
            regression_test_discipline=0.6,
            test_documentation_quality=0.5
        )
        
        strategy = CompleteTestStrategy(
            pyramid=pyramid,
            automation=automation,
            tdd=tdd,
            culture=culture,
            approaches=[TestingApproach.AUTOMATED, TestingApproach.TDD]
        )
        
        impact = strategy.calculate_comprehensive_impact(0.5, 1.0)
        
        # Should have all key metrics
        assert 'total_cycle_time' in impact
        assert 'defect_escape_rate' in impact
        assert 'quality_score' in impact
        assert 'testing_confidence' in impact
        assert 'testing_roi' in impact
        assert 'flakiness_rate' in impact
    
    def test_create_startup_strategy(self):
        """Test creating startup test strategy."""
        strategy = create_basic_test_strategy("startup")
        
        # Should have startup characteristics
        assert strategy.automation.automation_percentage < 0.5  # Low automation
        assert strategy.culture.qa_developer_ratio < 0.15  # Low QA ratio
        assert strategy.tdd is None  # No TDD
    
    def test_create_enterprise_strategy(self):
        """Test creating enterprise test strategy."""
        strategy = create_basic_test_strategy("enterprise")
        
        # Should have enterprise characteristics
        assert strategy.automation.automation_percentage > 0.7  # High automation
        assert strategy.culture.qa_developer_ratio > 0.2  # Higher QA ratio
        assert strategy.tdd is not None  # Has TDD
        assert strategy.tdd.adoption_percentage > 0.2
    
    def test_flakiness_increases_with_ai(self):
        """Test that AI increases test flakiness."""
        strategy = create_basic_test_strategy("balanced")
        
        impact_no_ai = strategy.calculate_comprehensive_impact(0.0, 1.0)
        impact_with_ai = strategy.calculate_comprehensive_impact(1.0, 1.0)
        
        # Flakiness should increase with AI
        assert impact_with_ai['flakiness_rate'] > impact_no_ai['flakiness_rate']
        
        # Testing confidence should decrease
        assert impact_with_ai['testing_confidence'] < impact_no_ai['testing_confidence']
    
    def test_tdd_vs_no_tdd_impact(self):
        """Test impact difference between TDD and non-TDD strategies."""
        tdd_strategy = create_basic_test_strategy("enterprise")  # Has TDD
        no_tdd_strategy = create_basic_test_strategy("startup")  # No TDD
        
        tdd_impact = tdd_strategy.calculate_comprehensive_impact(0.0, 1.0)
        no_tdd_impact = no_tdd_strategy.calculate_comprehensive_impact(0.0, 1.0)
        
        # TDD should have different quality characteristics
        # (May be higher or lower cycle time, but should be different)
        assert tdd_impact['total_cycle_time'] != no_tdd_impact['total_cycle_time']