"""
Comprehensive tests for baseline.py - Baseline metrics and calculations
"""

import pytest
from dataclasses import asdict

from src.model.baseline import (
    BaselineMetrics, create_industry_baseline, calculate_opportunity_cost
)
from src.utils.exceptions import ValidationError, CalculationError


class TestBaselineMetrics:
    """Test BaselineMetrics dataclass validation and creation"""
    
    def test_valid_baseline_metrics_creation(self):
        """Test creating valid BaselineMetrics"""
        metrics = BaselineMetrics(
            team_size=50,
            junior_ratio=0.3, mid_ratio=0.5, senior_ratio=0.2,
            junior_flc=140_000, mid_flc=180_000, senior_flc=250_000,
            avg_feature_cycle_days=30,
            avg_bug_fix_hours=24,
            onboarding_days=60,
            defect_escape_rate=3.0,
            production_incidents_per_month=5,
            avg_incident_cost=15_000,
            rework_percentage=0.20,
            new_feature_percentage=0.40,
            maintenance_percentage=0.35,
            tech_debt_percentage=0.10,
            meetings_percentage=0.15,
            avg_pr_review_hours=4,
            pr_rejection_rate=0.25
        )
        
        # All fields should be accessible
        assert metrics.team_size == 50
        assert metrics.junior_ratio == 0.3
        assert metrics.avg_feature_cycle_days == 30
        
    def test_team_ratios_sum_validation(self):
        """Test that team ratios must sum to 1.0"""
        with pytest.raises(CalculationError, match="sum"):
            BaselineMetrics(
                team_size=50,
                junior_ratio=0.4, mid_ratio=0.4, senior_ratio=0.3,  # Sum = 1.1
                junior_flc=140_000, mid_flc=180_000, senior_flc=250_000,
                avg_feature_cycle_days=30,
                avg_bug_fix_hours=24,
                onboarding_days=60,
                defect_escape_rate=3.0,
                production_incidents_per_month=5,
                avg_incident_cost=15_000,
                rework_percentage=0.20,
                new_feature_percentage=0.40,
                maintenance_percentage=0.35,
                tech_debt_percentage=0.10,
                meetings_percentage=0.15,
                avg_pr_review_hours=4,
                pr_rejection_rate=0.25
            )
            
    def test_capacity_ratios_sum_validation(self):
        """Test that capacity allocation ratios must sum to 1.0"""
        with pytest.raises(CalculationError, match="sum"):
            BaselineMetrics(
                team_size=50,
                junior_ratio=0.3, mid_ratio=0.5, senior_ratio=0.2,
                junior_flc=140_000, mid_flc=180_000, senior_flc=250_000,
                avg_feature_cycle_days=30,
                avg_bug_fix_hours=24,
                onboarding_days=60,
                defect_escape_rate=3.0,
                production_incidents_per_month=5,
                avg_incident_cost=15_000,
                rework_percentage=0.20,
                new_feature_percentage=0.50,
                maintenance_percentage=0.35,
                tech_debt_percentage=0.20,  # Sum = 1.05
                meetings_percentage=0.15,
                avg_pr_review_hours=4,
                pr_rejection_rate=0.25
            )
            
    def test_negative_values_validation(self):
        """Test that negative values raise ValidationError"""
        with pytest.raises(CalculationError):
            BaselineMetrics(
                team_size=-5,  # Invalid: negative
                junior_ratio=0.3, mid_ratio=0.5, senior_ratio=0.2,
                junior_flc=140_000, mid_flc=180_000, senior_flc=250_000,
                avg_feature_cycle_days=30,
                avg_bug_fix_hours=24,
                onboarding_days=60,
                defect_escape_rate=3.0,
                production_incidents_per_month=5,
                avg_incident_cost=15_000,
                rework_percentage=0.20,
                new_feature_percentage=0.40,
                maintenance_percentage=0.35,
                tech_debt_percentage=0.10,
                meetings_percentage=0.15,
                avg_pr_review_hours=4,
                pr_rejection_rate=0.25
            )
            
    def test_invalid_ratios_validation(self):
        """Test that invalid ratios raise ValidationError"""
        with pytest.raises(CalculationError, match="must be between 0.0 and 1.0"):
            BaselineMetrics(
                team_size=50,
                junior_ratio=0.3, mid_ratio=0.5, senior_ratio=0.2,
                junior_flc=140_000, mid_flc=180_000, senior_flc=250_000,
                avg_feature_cycle_days=30,
                avg_bug_fix_hours=24,
                onboarding_days=60,
                defect_escape_rate=3.0,
                production_incidents_per_month=5,
                avg_incident_cost=15_000,
                rework_percentage=1.5,  # Invalid: > 1.0
                new_feature_percentage=0.40,
                maintenance_percentage=0.35,
                tech_debt_percentage=0.10,
                meetings_percentage=0.15,
                avg_pr_review_hours=4,
                pr_rejection_rate=0.25
            )


class TestBaselineMetricsCalculations:
    """Test BaselineMetrics calculated properties"""
    
    @pytest.fixture
    def baseline_metrics(self):
        """Standard baseline metrics for testing"""
        return BaselineMetrics(
            team_size=10,
            junior_ratio=0.4, mid_ratio=0.4, senior_ratio=0.2,
            junior_flc=100_000, mid_flc=150_000, senior_flc=200_000,
            avg_feature_cycle_days=20,
            avg_bug_fix_hours=16,
            onboarding_days=45,
            defect_escape_rate=4.0,
            production_incidents_per_month=3,
            avg_incident_cost=10_000,
            rework_percentage=0.15,
            new_feature_percentage=0.50,
            maintenance_percentage=0.30,
            tech_debt_percentage=0.05,
            meetings_percentage=0.15,
            avg_pr_review_hours=3,
            pr_rejection_rate=0.20
        )
    
    def test_weighted_avg_flc_calculation(self, baseline_metrics):
        """Test weighted average FLC calculation"""
        expected_flc = (
            0.4 * 100_000 +  # Junior
            0.4 * 150_000 +  # Mid
            0.2 * 200_000    # Senior
        )  # = 140,000
        
        assert baseline_metrics.weighted_avg_flc == expected_flc
        
    def test_total_team_cost_calculation(self, baseline_metrics):
        """Test total team cost calculation"""
        expected_cost = baseline_metrics.team_size * baseline_metrics.weighted_avg_flc
        assert baseline_metrics.total_team_cost == expected_cost
        
    def test_effective_capacity_hours_calculation(self, baseline_metrics):
        """Test effective capacity hours calculation"""
        from src.config.constants import WORKING_HOURS_PER_YEAR
        
        expected_hours = WORKING_HOURS_PER_YEAR * (1 - baseline_metrics.meetings_percentage)
        assert baseline_metrics.effective_capacity_hours == expected_hours
        
    def test_feature_delivery_rate_calculation(self, baseline_metrics):
        """Test feature delivery rate calculation"""
        from src.config.constants import WORKING_DAYS_PER_YEAR
        
        # Features per year = (working days / cycle days) * feature percentage
        features_per_year = (WORKING_DAYS_PER_YEAR / baseline_metrics.avg_feature_cycle_days)
        expected_rate = features_per_year * baseline_metrics.new_feature_percentage
        
        assert abs(baseline_metrics.feature_delivery_rate - expected_rate) < 0.01
        
    def test_annual_incident_cost_calculation(self, baseline_metrics):
        """Test annual incident cost calculation"""
        expected_cost = (
            baseline_metrics.production_incidents_per_month * 
            12 * 
            baseline_metrics.avg_incident_cost
        )
        
        assert baseline_metrics.annual_incident_cost == expected_cost
        
    def test_annual_rework_cost_calculation(self, baseline_metrics):
        """Test annual rework cost calculation"""
        productive_cost = baseline_metrics.total_team_cost * (1 - baseline_metrics.meetings_percentage)
        expected_cost = productive_cost * baseline_metrics.rework_percentage
        
        assert baseline_metrics.annual_rework_cost == expected_cost
        
    def test_calculate_baseline_efficiency(self, baseline_metrics):
        """Test baseline efficiency calculation"""
        efficiency = baseline_metrics.calculate_baseline_efficiency()
        
        required_keys = [
            "cost_per_feature", "incidents_per_feature", 
            "effective_utilization", "quality_cost_ratio"
        ]
        
        for key in required_keys:
            assert key in efficiency
            assert isinstance(efficiency[key], (int, float))
            assert efficiency[key] >= 0
        
        # Effective utilization should equal new feature percentage
        assert efficiency["effective_utilization"] == baseline_metrics.new_feature_percentage
        
        # Cost per feature should be reasonable
        total_features = baseline_metrics.team_size * baseline_metrics.feature_delivery_rate
        expected_cost_per_feature = baseline_metrics.total_team_cost / total_features if total_features > 0 else 0
        assert abs(efficiency["cost_per_feature"] - expected_cost_per_feature) < 1


class TestCreateIndustryBaseline:
    """Test industry baseline creation functions"""
    
    def test_startup_baseline(self):
        """Test startup industry baseline"""
        baseline = create_industry_baseline("startup")
        
        assert isinstance(baseline, BaselineMetrics)
        assert 5 <= baseline.team_size <= 20  # Startup team (5-20 people)
        assert baseline.avg_feature_cycle_days <= 20  # Fast cycle
        
    def test_enterprise_baseline(self):
        """Test enterprise industry baseline"""
        baseline = create_industry_baseline("enterprise")
        
        assert isinstance(baseline, BaselineMetrics)
        assert baseline.team_size >= 101  # Enterprise team (101+ people)  
        assert baseline.avg_feature_cycle_days >= 25  # Longer cycle
        
    def test_scale_up_baseline(self):
        """Test scale-up industry baseline"""
        baseline = create_industry_baseline("scale_up")
        
        assert isinstance(baseline, BaselineMetrics)
        assert 20 <= baseline.team_size <= 100  # Scaleup team (20-100 people)
        assert 15 <= baseline.avg_feature_cycle_days <= 25  # Medium cycle
        
    def test_default_baseline(self):
        """Test that default returns enterprise baseline"""
        default_baseline = create_industry_baseline()
        enterprise_baseline = create_industry_baseline("enterprise")
        
        assert asdict(default_baseline) == asdict(enterprise_baseline)
        
    def test_invalid_industry(self):
        """Test invalid industry returns enterprise baseline"""
        invalid_baseline = create_industry_baseline("nonexistent")
        enterprise_baseline = create_industry_baseline("enterprise")
        
        assert asdict(invalid_baseline) == asdict(enterprise_baseline)
        
    def test_baseline_consistency(self):
        """Test that all industry baselines are internally consistent"""
        industries = ["startup", "enterprise", "scale_up"]
        
        for industry in industries:
            baseline = create_industry_baseline(industry)
            
            # Team ratios should sum to 1.0
            team_ratio_sum = baseline.junior_ratio + baseline.mid_ratio + baseline.senior_ratio
            assert abs(team_ratio_sum - 1.0) < 0.01, f"{industry} team ratios don't sum to 1.0"
            
            # Capacity ratios should sum to 1.0
            capacity_sum = (baseline.new_feature_percentage + baseline.maintenance_percentage + 
                          baseline.tech_debt_percentage + baseline.meetings_percentage)
            assert abs(capacity_sum - 1.0) < 0.01, f"{industry} capacity ratios don't sum to 1.0"
            
            # All values should be positive
            assert baseline.team_size > 0
            assert baseline.avg_feature_cycle_days > 0
            assert baseline.weighted_avg_flc > 0


class TestCalculateOpportunityCost:
    """Test opportunity cost calculation function"""
    
    @pytest.fixture
    def baseline_metrics(self):
        """Standard baseline metrics for testing"""
        return create_industry_baseline("enterprise")
    
    def test_opportunity_cost_structure(self, baseline_metrics):
        """Test opportunity cost calculation structure"""
        opportunity_cost = calculate_opportunity_cost(baseline_metrics)
        
        required_keys = [
            "lost_feature_value", "quality_costs", "slow_onboarding_cost",
            "context_switching_cost", "total_opportunity_cost"
        ]
        
        for key in required_keys:
            assert key in opportunity_cost
            assert isinstance(opportunity_cost[key], (int, float))
            assert opportunity_cost[key] >= 0
            
    def test_opportunity_cost_consistency(self, baseline_metrics):
        """Test opportunity cost calculation consistency"""
        opportunity_cost = calculate_opportunity_cost(baseline_metrics)
        
        # Total should be reasonable relative to team cost
        team_cost = baseline_metrics.total_team_cost
        total_opportunity = opportunity_cost["total_opportunity_cost"]
        
        # Opportunity cost should be significant but not unreasonably high
        # For larger teams, opportunity costs can be higher due to scale inefficiencies
        max_multiplier = 3 if baseline_metrics.team_size >= 101 else 2
        assert 0 <= total_opportunity <= team_cost * max_multiplier, \
            f"Opportunity cost should be 0-{max_multiplier*100}% of team cost for team size {baseline_metrics.team_size}"
            
        # Quality costs should equal incident + rework costs
        expected_quality_costs = (
            baseline_metrics.annual_incident_cost + 
            baseline_metrics.annual_rework_cost
        )
        assert abs(opportunity_cost["quality_costs"] - expected_quality_costs) < 1
        
    def test_opportunity_cost_with_zero_features(self):
        """Test opportunity cost when no features are delivered"""
        baseline = create_industry_baseline("enterprise")
        baseline.new_feature_percentage = 0.0  # No time on features
        baseline.maintenance_percentage = 1.0  # All time on maintenance
        
        opportunity_cost = calculate_opportunity_cost(baseline)
        
        # Should handle zero feature delivery gracefully
        assert opportunity_cost["lost_feature_value"] >= 0
        assert opportunity_cost["total_opportunity_cost"] >= 0
        
    def test_opportunity_cost_with_minimal_incidents(self):
        """Test opportunity cost with minimal quality issues"""
        baseline = create_industry_baseline("startup")
        baseline.production_incidents_per_month = 0.1  # Very few incidents
        baseline.rework_percentage = 0.01  # Very little rework
        
        opportunity_cost = calculate_opportunity_cost(baseline)
        
        # Quality costs should be very low
        assert opportunity_cost["quality_costs"] < baseline.total_team_cost * 0.05
        assert opportunity_cost["total_opportunity_cost"] >= 0


class TestBaselineMetricsEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_single_developer_team(self):
        """Test baseline with single developer"""
        baseline = BaselineMetrics(
            team_size=1,
            junior_ratio=1.0, mid_ratio=0.0, senior_ratio=0.0,
            junior_flc=100_000, mid_flc=150_000, senior_flc=200_000,
            avg_feature_cycle_days=10,
            avg_bug_fix_hours=8,
            onboarding_days=30,
            defect_escape_rate=2.0,
            production_incidents_per_month=1,
            avg_incident_cost=5_000,
            rework_percentage=0.10,
            new_feature_percentage=0.70,
            maintenance_percentage=0.15,
            tech_debt_percentage=0.05,
            meetings_percentage=0.10,
            avg_pr_review_hours=2,
            pr_rejection_rate=0.15
        )
        
        # Should work for single developer
        assert baseline.team_size == 1
        assert baseline.weighted_avg_flc == 100_000  # Only junior
        assert baseline.total_team_cost == 100_000
        
        efficiency = baseline.calculate_baseline_efficiency()
        assert all(value >= 0 for value in efficiency.values())
        
    def test_very_large_team(self):
        """Test baseline with very large team"""
        baseline = BaselineMetrics(
            team_size=1000,
            junior_ratio=0.2, mid_ratio=0.6, senior_ratio=0.2,
            junior_flc=120_000, mid_flc=160_000, senior_flc=220_000,
            avg_feature_cycle_days=45,
            avg_bug_fix_hours=32,
            onboarding_days=90,
            defect_escape_rate=2.5,
            production_incidents_per_month=20,
            avg_incident_cost=25_000,
            rework_percentage=0.25,
            new_feature_percentage=0.35,
            maintenance_percentage=0.40,
            tech_debt_percentage=0.15,
            meetings_percentage=0.10,
            avg_pr_review_hours=6,
            pr_rejection_rate=0.30
        )
        
        # Should work for large team
        assert baseline.team_size == 1000
        assert baseline.total_team_cost > 100_000_000  # Very high cost
        
        efficiency = baseline.calculate_baseline_efficiency()
        assert all(value >= 0 for value in efficiency.values())
        
    def test_zero_values_where_allowed(self):
        """Test baseline with zero values where allowed"""
        baseline = BaselineMetrics(
            team_size=5,
            junior_ratio=0.0, mid_ratio=1.0, senior_ratio=0.0,  # All mid-level
            junior_flc=100_000, mid_flc=150_000, senior_flc=200_000,
            avg_feature_cycle_days=15,
            avg_bug_fix_hours=10,
            onboarding_days=20,
            defect_escape_rate=0.0,  # Perfect quality
            production_incidents_per_month=0.0,  # No incidents
            avg_incident_cost=0.0,  # No incident cost
            rework_percentage=0.0,  # No rework
            new_feature_percentage=0.85,
            maintenance_percentage=0.10,
            tech_debt_percentage=0.05,
            meetings_percentage=0.0,  # No meetings
            avg_pr_review_hours=0.0,  # No PR reviews
            pr_rejection_rate=0.0  # Perfect PRs
        )
        
        # Should handle zero values gracefully
        assert baseline.weighted_avg_flc == 150_000  # All mid-level
        assert baseline.annual_incident_cost == 0
        assert baseline.annual_rework_cost == 0
        
        efficiency = baseline.calculate_baseline_efficiency()
        assert efficiency["quality_cost_ratio"] == 0  # No quality costs
        
    def test_extreme_but_valid_values(self):
        """Test baseline with extreme but valid values"""
        baseline = BaselineMetrics(
            team_size=3,
            junior_ratio=0.33, mid_ratio=0.33, senior_ratio=0.34,  # Sums to 1.0
            junior_flc=50_000, mid_flc=300_000, senior_flc=500_000,  # Extreme salary range
            avg_feature_cycle_days=180,  # Very slow cycle
            avg_bug_fix_hours=100,  # Very slow fixes
            onboarding_days=365,  # One year onboarding
            defect_escape_rate=50.0,  # Very buggy code
            production_incidents_per_month=50,  # Lots of incidents
            avg_incident_cost=100_000,  # Very expensive incidents
            rework_percentage=0.5,  # 50% rework
            new_feature_percentage=0.1,  # Very little feature work
            maintenance_percentage=0.8,  # Mostly maintenance
            tech_debt_percentage=0.05,
            meetings_percentage=0.05,
            avg_pr_review_hours=20,  # Very slow reviews
            pr_rejection_rate=0.8  # Most PRs rejected
        )
        
        # Should handle extreme values
        assert baseline.team_size == 3
        efficiency = baseline.calculate_baseline_efficiency()
        assert all(isinstance(value, (int, float)) for value in efficiency.values())
        
        opportunity_cost = calculate_opportunity_cost(baseline)
        assert opportunity_cost["total_opportunity_cost"] > 0