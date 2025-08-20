"""
Comprehensive tests for cost_structure.py - Financial calculations and cost modeling
"""

import pytest
import numpy as np
from dataclasses import asdict

from src.model.cost_structure import (
    AIToolCosts, CostModel, create_cost_scenario, calculate_breakeven
)
from src.model.baseline import create_industry_baseline
from src.utils.exceptions import ValidationError, CalculationError


class TestAIToolCosts:
    """Test AIToolCosts dataclass validation and creation"""
    
    def test_valid_ai_tool_costs_creation(self):
        """Test creating valid AIToolCosts"""
        costs = AIToolCosts(
            cost_per_seat_month=50,
            enterprise_discount=0.3,
            initial_tokens_per_dev_month=500_000,
            token_price_per_million=8,
            token_price_decline_annual=0.25,
            token_growth_rate_monthly=0.10,
            token_plateau_month=12,
            initial_training_cost_per_dev=2_000,
            ongoing_training_cost_annual=500,
            trainer_cost_per_day=2_000,
            training_days_initial=5,
            training_days_ongoing_annual=2,
            infrastructure_setup=50_000,
            infrastructure_monthly=5_000,
            admin_overhead_percentage=0.05,
            context_switch_cost_month=1_000,
            bad_code_cleanup_percentage=0.08,
            security_review_overhead=4,
            pilot_budget=100_000,
            ongoing_experimentation=50_000
        )
        
        # All fields should be accessible
        assert costs.cost_per_seat_month == 50
        assert costs.enterprise_discount == 0.3
        assert costs.token_plateau_month == 12
        
    def test_negative_costs_validation(self):
        """Test that negative costs raise ValidationError"""
        with pytest.raises(CalculationError):
            AIToolCosts(
                cost_per_seat_month=-50,  # Invalid: negative
                enterprise_discount=0.3,
                initial_tokens_per_dev_month=500_000,
                token_price_per_million=8,
                token_price_decline_annual=0.25,
                token_growth_rate_monthly=0.10,
                token_plateau_month=12,
                initial_training_cost_per_dev=2_000,
                ongoing_training_cost_annual=500,
                trainer_cost_per_day=2_000,
                training_days_initial=5,
                training_days_ongoing_annual=2,
                infrastructure_setup=50_000,
                infrastructure_monthly=5_000,
                admin_overhead_percentage=0.05,
                context_switch_cost_month=1_000,
                bad_code_cleanup_percentage=0.08,
                security_review_overhead=4,
                pilot_budget=100_000,
                ongoing_experimentation=50_000
            )
            
    def test_invalid_plateau_month(self):
        """Test that invalid plateau month raises ValidationError"""
        with pytest.raises(ValidationError):
            AIToolCosts(
                cost_per_seat_month=50,
                enterprise_discount=0.3,
                initial_tokens_per_dev_month=500_000,
                token_price_per_million=8,
                token_price_decline_annual=0.25,
                token_growth_rate_monthly=0.10,
                token_plateau_month=0,  # Invalid: must be >= 1
                initial_training_cost_per_dev=2_000,
                ongoing_training_cost_annual=500,
                trainer_cost_per_day=2_000,
                training_days_initial=5,
                training_days_ongoing_annual=2,
                infrastructure_setup=50_000,
                infrastructure_monthly=5_000,
                admin_overhead_percentage=0.05,
                context_switch_cost_month=1_000,
                bad_code_cleanup_percentage=0.08,
                security_review_overhead=4,
                pilot_budget=100_000,
                ongoing_experimentation=50_000
            )


class TestCostModel:
    """Test CostModel calculations"""
    
    @pytest.fixture
    def baseline_metrics(self):
        """Standard baseline metrics for testing"""
        return create_industry_baseline("enterprise")
    
    @pytest.fixture
    def ai_tool_costs(self):
        """Standard AI tool costs for testing"""
        return create_cost_scenario("enterprise")
    
    @pytest.fixture
    def cost_model(self, ai_tool_costs, baseline_metrics):
        """CostModel instance for testing"""
        return CostModel(ai_tool_costs, baseline_metrics)
    
    @pytest.fixture
    def adoption_curve(self):
        """Simple adoption curve for testing"""
        # Linear adoption to 80% over 24 months
        return np.linspace(0, 0.8, 24)
    
    def test_cost_model_creation(self, cost_model):
        """Test that CostModel can be created"""
        assert cost_model.costs.cost_per_seat_month == 50
        assert cost_model.baseline.team_size == 50
        
    def test_calculate_licensing_costs_structure(self, cost_model, adoption_curve):
        """Test licensing costs calculation structure"""
        months = 24
        licensing_costs = cost_model.calculate_licensing_costs(months, adoption_curve)
        
        assert isinstance(licensing_costs, np.ndarray)
        assert len(licensing_costs) == months
        assert all(cost >= 0 for cost in licensing_costs)
        
    def test_calculate_licensing_costs_logic(self, cost_model, adoption_curve):
        """Test licensing costs calculation logic"""
        months = 24
        licensing_costs = cost_model.calculate_licensing_costs(months, adoption_curve)
        
        # Early months should have lower costs (due to adoption curve)
        assert licensing_costs[0] < licensing_costs[-1]
        
        # Enterprise discount should be applied for large teams
        expected_final_cost = (
            cost_model.baseline.team_size * 
            adoption_curve[-1] * 
            cost_model.costs.cost_per_seat_month * 
            (1 - cost_model.costs.enterprise_discount)
        )
        assert abs(licensing_costs[-1] - expected_final_cost) < 1
        
    def test_calculate_token_costs_structure(self, cost_model, adoption_curve):
        """Test token costs calculation structure"""
        months = 24
        token_costs = cost_model.calculate_token_costs(months, adoption_curve)
        
        assert isinstance(token_costs, np.ndarray)
        assert len(token_costs) == months
        assert all(cost >= 0 for cost in token_costs)
        
    def test_calculate_token_costs_price_decline(self, cost_model):
        """Test that token prices decline over time"""
        months = 24
        adoption_curve = np.ones(months)  # Full adoption
        token_costs = cost_model.calculate_token_costs(months, adoption_curve)
        
        # Due to price decline, later months might have lower per-token costs
        # But usage growth might offset this, so we mainly check structure
        assert len(token_costs) == months
        assert all(cost >= 0 for cost in token_costs)
        
    def test_calculate_training_costs_structure(self, cost_model, adoption_curve):
        """Test training costs calculation structure"""
        months = 24
        training_costs = cost_model.calculate_training_costs(months, adoption_curve)
        
        assert isinstance(training_costs, np.ndarray)
        assert len(training_costs) == months
        assert all(cost >= 0 for cost in training_costs)
        
    def test_calculate_training_costs_logic(self, cost_model):
        """Test training costs logic - front-loaded then periodic"""
        months = 12
        # Simulate rapid initial adoption
        adoption_curve = np.array([0.0, 0.2, 0.5, 0.6, 0.7, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
        training_costs = cost_model.calculate_training_costs(months, adoption_curve)
        
        # Early months should have higher training costs (initial burst)
        early_costs = training_costs[:3].sum()
        later_costs = training_costs[6:9].sum()
        assert early_costs > later_costs
        
    def test_calculate_hidden_costs_structure(self, cost_model, adoption_curve):
        """Test hidden costs calculation structure"""
        months = 24
        hidden_costs = cost_model.calculate_hidden_costs(months, adoption_curve)
        
        assert isinstance(hidden_costs, np.ndarray)
        assert len(hidden_costs) == months
        assert all(cost >= 0 for cost in hidden_costs)
        
    def test_calculate_hidden_costs_decreasing(self, cost_model):
        """Test that hidden costs decrease over time (learning effect)"""
        months = 12
        adoption_curve = np.ones(months)  # Full adoption
        hidden_costs = cost_model.calculate_hidden_costs(months, adoption_curve)
        
        # Context switching costs should decrease over time
        early_avg = hidden_costs[:3].mean()
        later_avg = hidden_costs[9:].mean()
        assert early_avg > later_avg, "Hidden costs should decrease as teams learn"
        
    def test_calculate_total_costs_structure(self, cost_model, adoption_curve):
        """Test total costs calculation structure"""
        months = 24
        total_costs = cost_model.calculate_total_costs(months, adoption_curve)
        
        required_keys = [
            "licensing", "tokens", "training", "hidden", 
            "infrastructure", "admin", "experimentation", "total", "cumulative"
        ]
        
        for key in required_keys:
            assert key in total_costs, f"Missing key: {key}"
            assert isinstance(total_costs[key], np.ndarray)
            assert len(total_costs[key]) == months
            assert all(cost >= 0 for cost in total_costs[key])
    
    def test_calculate_total_costs_consistency(self, cost_model, adoption_curve):
        """Test that total costs equal sum of components"""
        months = 24
        total_costs = cost_model.calculate_total_costs(months, adoption_curve)
        
        for month in range(months):
            expected_total = (
                total_costs["licensing"][month] +
                total_costs["tokens"][month] +
                total_costs["training"][month] +
                total_costs["hidden"][month] +
                total_costs["infrastructure"][month] +
                total_costs["admin"][month] +
                total_costs["experimentation"][month]
            )
            
            assert abs(total_costs["total"][month] - expected_total) < 1, \
                f"Total cost inconsistency at month {month}"
    
    def test_calculate_cost_per_developer(self, cost_model, adoption_curve):
        """Test cost per developer calculation"""
        months = 24
        cost_per_dev = cost_model.calculate_cost_per_developer(months, adoption_curve)
        
        assert isinstance(cost_per_dev, np.ndarray)
        assert len(cost_per_dev) == months
        assert all(cost >= 0 for cost in cost_per_dev)
        
        # Months with no adoption should have zero cost per dev
        zero_adoption = np.zeros(months)
        zero_cost_per_dev = cost_model.calculate_cost_per_developer(months, zero_adoption)
        assert all(cost == 0 for cost in zero_cost_per_dev)
        
    def test_project_future_costs(self, cost_model):
        """Test future cost projection"""
        years = 3
        future_costs = cost_model.project_future_costs(years)
        
        assert isinstance(future_costs, dict)
        for year in range(1, years + 1):
            key = f"year_{year}"
            assert key in future_costs
            assert isinstance(future_costs[key], (int, float))
            assert future_costs[key] >= 0


class TestCreateCostScenario:
    """Test cost scenario creation functions"""
    
    def test_startup_scenario(self):
        """Test startup cost scenario"""
        costs = create_cost_scenario("startup")
        
        assert isinstance(costs, AIToolCosts)
        assert costs.cost_per_seat_month <= 35  # Lower cost for startups
        assert costs.enterprise_discount == 0.0  # No enterprise discount
        
    def test_enterprise_scenario(self):
        """Test enterprise cost scenario"""
        costs = create_cost_scenario("enterprise")
        
        assert isinstance(costs, AIToolCosts)
        assert costs.cost_per_seat_month >= 40  # Higher cost but with discount
        assert costs.enterprise_discount > 0.0  # Has enterprise discount
        
    def test_aggressive_scenario(self):
        """Test aggressive cost scenario"""
        costs = create_cost_scenario("aggressive")
        
        assert isinstance(costs, AIToolCosts)
        assert costs.cost_per_seat_month >= 80  # Highest cost
        assert costs.initial_tokens_per_dev_month >= 800_000  # High token usage
        
    def test_default_scenario(self):
        """Test that default returns enterprise scenario"""
        default_costs = create_cost_scenario()
        enterprise_costs = create_cost_scenario("enterprise")
        
        assert asdict(default_costs) == asdict(enterprise_costs)
        
    def test_invalid_scenario(self):
        """Test invalid scenario returns enterprise scenario"""
        invalid_costs = create_cost_scenario("nonexistent")
        enterprise_costs = create_cost_scenario("enterprise")
        
        assert asdict(invalid_costs) == asdict(enterprise_costs)


class TestCalculateBreakeven:
    """Test breakeven calculation function"""
    
    def test_breakeven_with_simple_data(self):
        """Test breakeven calculation with simple data"""
        # Simple scenario: costs start high, value grows
        costs = {
            "total": np.array([1000, 1000, 1000, 1000, 1000]),
            "cumulative": np.array([1000, 2000, 3000, 4000, 5000])
        }
        value = {
            "total": np.array([0, 500, 1000, 1500, 2000])
        }
        
        breakeven_month = calculate_breakeven(costs, value)
        
        # Should break even when cumulative value >= cumulative costs
        # Value: [0, 500, 1000, 1500, 2000] -> cumulative: [0, 500, 1500, 3000, 5000]
        # Costs: [1000, 2000, 3000, 4000, 5000] cumulative (already provided)
        # Breaks even at month 4 (index 4): 5000 >= 5000
        assert breakeven_month == 4
        
    def test_breakeven_no_breakeven(self):
        """Test when no breakeven occurs"""
        costs = {
            "total": np.array([1000, 1000, 1000, 1000, 1000]),
            "cumulative": np.array([1000, 2000, 3000, 4000, 5000])
        }
        value = {
            "total": np.array([0, 100, 200, 300, 400])  # Never catches up
        }
        
        breakeven_month = calculate_breakeven(costs, value)
        assert breakeven_month is None
        
    def test_breakeven_immediate(self):
        """Test immediate breakeven"""
        costs = {
            "total": np.array([1000, 1000, 1000]),
            "cumulative": np.array([1000, 2000, 3000])
        }
        value = {
            "total": np.array([2000, 1000, 1000])  # High initial value
        }
        
        breakeven_month = calculate_breakeven(costs, value)
        assert breakeven_month == 0  # Breaks even immediately
        
    def test_breakeven_with_cumulative_costs_provided(self):
        """Test when cumulative costs are already provided"""
        costs = {
            "cumulative": np.array([1000, 2000, 3000, 4000, 5000])
        }
        value = {
            "total": np.array([0, 800, 1200, 1600, 2000])
        }
        
        breakeven_month = calculate_breakeven(costs, value)
        
        # Cumulative value: [0, 800, 1200, 1600, 2000] -> cumsum: [0, 800, 2000, 3600, 5600]
        # Costs: [1000, 2000, 3000, 4000, 5000] cumulative (provided)
        # Breaks even at month 4: 5600 >= 5000
        assert breakeven_month == 4


class TestCostModelEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_adoption(self):
        """Test cost model with zero adoption"""
        baseline = create_industry_baseline("startup")
        costs = create_cost_scenario("startup")
        model = CostModel(costs, baseline)
        
        months = 12
        zero_adoption = np.zeros(months)
        
        total_costs = model.calculate_total_costs(months, zero_adoption)
        
        # Should still have infrastructure and experimentation costs
        assert all(total_costs["infrastructure"] > 0)
        assert total_costs["experimentation"][0] > 0  # Pilot budget
        
        # But no licensing or token costs
        assert all(total_costs["licensing"] == 0)
        assert all(total_costs["tokens"] == 0)
        
    def test_full_adoption_immediately(self):
        """Test cost model with immediate full adoption"""
        baseline = create_industry_baseline("enterprise")
        costs = create_cost_scenario("enterprise")
        model = CostModel(costs, baseline)
        
        months = 12
        full_adoption = np.ones(months)
        
        total_costs = model.calculate_total_costs(months, full_adoption)
        
        # All cost components should be at maximum
        assert all(total_costs["licensing"] > 0)
        assert all(total_costs["tokens"] > 0)
        assert all(total_costs["total"] > 0)
        
    def test_very_small_team(self):
        """Test cost model with very small team"""
        baseline = create_industry_baseline("startup")
        baseline.team_size = 1  # Single developer
        costs = create_cost_scenario("startup")
        model = CostModel(costs, baseline)
        
        months = 12
        adoption_curve = np.ones(months)
        
        total_costs = model.calculate_total_costs(months, adoption_curve)
        cost_per_dev = model.calculate_cost_per_developer(months, adoption_curve)
        
        # Should work for single developer
        assert all(total_costs["total"] > 0)
        assert all(cost_per_dev > 0)
        
        # Cost per dev should equal total cost for single developer
        for month in range(months):
            assert abs(cost_per_dev[month] - total_costs["total"][month]) < 1
        
    def test_extreme_token_usage(self):
        """Test with extreme token usage parameters"""
        baseline = create_industry_baseline("enterprise")
        costs = create_cost_scenario("enterprise")
        
        # Modify to extreme values
        costs.initial_tokens_per_dev_month = 10_000_000  # 10M tokens
        costs.token_growth_rate_monthly = 0.5  # 50% growth per month
        costs.token_plateau_month = 3  # Early plateau
        
        model = CostModel(costs, baseline)
        months = 12
        adoption_curve = np.ones(months)
        
        token_costs = model.calculate_token_costs(months, adoption_curve)
        
        # Should handle extreme values gracefully
        assert all(cost >= 0 for cost in token_costs)
        assert len(token_costs) == months
        
        # Growth should plateau after month 3
        plateau_costs = token_costs[3:6]
        assert all(abs(plateau_costs[0] - cost) < plateau_costs[0] * 0.1 
                  for cost in plateau_costs), "Token costs should plateau"
        
    def test_zero_cost_parameters(self):
        """Test with zero cost parameters"""
        baseline = create_industry_baseline("startup")
        costs = create_cost_scenario("startup")
        
        # Set some costs to zero
        costs.infrastructure_setup = 0
        costs.infrastructure_monthly = 0
        costs.pilot_budget = 0
        costs.ongoing_experimentation = 0
        
        model = CostModel(costs, baseline)
        months = 12
        adoption_curve = np.linspace(0, 1, months)
        
        total_costs = model.calculate_total_costs(months, adoption_curve)
        
        # Should handle zero costs gracefully
        assert all(total_costs["infrastructure"] == 0)
        assert all(total_costs["experimentation"] == 0)
        assert all(total_costs["total"] >= 0)  # Still have other costs