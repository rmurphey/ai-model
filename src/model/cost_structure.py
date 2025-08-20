"""
Cost structure model for AI-assisted development.
Models all direct and indirect costs associated with AI tool adoption.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
from .baseline import BaselineMetrics
from ..utils.math_helpers import safe_divide, validate_positive, validate_ratio
from ..utils.exceptions import CalculationError, ValidationError
from ..config.constants import (
    WORKING_HOURS_PER_YEAR, DEV_HOURS_PER_MONTH, ENTERPRISE_TEAM_SIZE_THRESHOLD,
    MONTHS_PER_YEAR
)

@dataclass
class AIToolCosts:
    """Cost structure for AI development tools"""
    
    # Licensing costs
    cost_per_seat_month: float         # Monthly license cost per developer
    enterprise_discount: float          # Discount for enterprise agreements (0-1)
    
    # Token/usage costs
    initial_tokens_per_dev_month: float # Starting token consumption
    token_price_per_million: float      # Current price per million tokens
    token_price_decline_annual: float   # Annual price decline rate (e.g., 0.2 = 20%)
    token_growth_rate_monthly: float    # Monthly growth in token usage
    token_plateau_month: int            # Month when token usage plateaus
    
    # Training and onboarding
    initial_training_cost_per_dev: float
    ongoing_training_cost_annual: float
    trainer_cost_per_day: float
    training_days_initial: float
    training_days_ongoing_annual: float
    
    # Infrastructure and support
    infrastructure_setup: float         # One-time setup cost
    infrastructure_monthly: float       # Ongoing infrastructure costs
    admin_overhead_percentage: float    # % of FTE for administration
    
    # Hidden costs
    context_switch_cost_month: float    # Productivity loss during adoption
    bad_code_cleanup_percentage: float  # % of AI code requiring cleanup
    security_review_overhead: float     # Extra security review time
    
    # Experimentation budget
    pilot_budget: float                 # Initial experimentation budget
    ongoing_experimentation: float      # Annual R&D budget for AI tools
    
    def __post_init__(self):
        """Validate all cost parameters"""
        # Validate positive costs
        validate_positive(self.cost_per_seat_month, "cost_per_seat_month")
        validate_positive(self.initial_tokens_per_dev_month, "initial_tokens_per_dev_month")
        validate_positive(self.token_price_per_million, "token_price_per_million")
        validate_positive(self.initial_training_cost_per_dev, "initial_training_cost_per_dev", allow_zero=True)
        validate_positive(self.ongoing_training_cost_annual, "ongoing_training_cost_annual", allow_zero=True)
        validate_positive(self.trainer_cost_per_day, "trainer_cost_per_day")
        validate_positive(self.training_days_initial, "training_days_initial", allow_zero=True)
        validate_positive(self.training_days_ongoing_annual, "training_days_ongoing_annual", allow_zero=True)
        validate_positive(self.infrastructure_setup, "infrastructure_setup", allow_zero=True)
        validate_positive(self.infrastructure_monthly, "infrastructure_monthly", allow_zero=True)
        validate_positive(self.context_switch_cost_month, "context_switch_cost_month", allow_zero=True)
        validate_positive(self.security_review_overhead, "security_review_overhead", allow_zero=True)
        validate_positive(self.pilot_budget, "pilot_budget", allow_zero=True)
        validate_positive(self.ongoing_experimentation, "ongoing_experimentation", allow_zero=True)
        
        # Validate ratios and percentages
        validate_ratio(self.enterprise_discount, "enterprise_discount")
        validate_ratio(self.token_price_decline_annual, "token_price_decline_annual")
        validate_ratio(self.admin_overhead_percentage, "admin_overhead_percentage")
        validate_ratio(self.bad_code_cleanup_percentage, "bad_code_cleanup_percentage")
        
        # Validate growth rate (can be higher than 1.0)
        validate_positive(self.token_growth_rate_monthly, "token_growth_rate_monthly")
        
        # Validate plateau month
        if self.token_plateau_month < 1:
            raise ValidationError(
                field_name="token_plateau_month",
                value=self.token_plateau_month,
                expected="positive integer >= 1",
                suggestion="Set token_plateau_month to a positive integer"
            )


class CostModel:
    """Models total cost of ownership for AI tools"""
    
    def __init__(self, costs: AIToolCosts, baseline: BaselineMetrics):
        self.costs = costs
        self.baseline = baseline
    
    def calculate_licensing_costs(self, months: int = 24, adoption_curve: np.ndarray = None) -> np.ndarray:
        """Calculate monthly licensing costs"""
        
        if adoption_curve is None:
            adoption_curve = np.ones(months)  # Assume full adoption if not provided
        
        monthly_costs = np.zeros(months)
        
        for month in range(months):
            adopted_devs = self.baseline.team_size * adoption_curve[month]
            base_cost = adopted_devs * self.costs.cost_per_seat_month
            
            # Apply enterprise discount for large teams
            if self.baseline.team_size >= ENTERPRISE_TEAM_SIZE_THRESHOLD:
                base_cost *= (1 - self.costs.enterprise_discount)
            
            monthly_costs[month] = base_cost
        
        return monthly_costs
    
    def calculate_token_costs(self, months: int = 24, adoption_curve: np.ndarray = None) -> np.ndarray:
        """Calculate monthly token consumption costs"""
        
        if adoption_curve is None:
            adoption_curve = np.ones(months)
        
        monthly_costs = np.zeros(months)
        
        for month in range(months):
            # Calculate token price at this month (declining over time)
            years_elapsed = month / MONTHS_PER_YEAR
            current_price = self.costs.token_price_per_million * (
                (1 - self.costs.token_price_decline_annual) ** years_elapsed
            )
            
            # Calculate token usage per developer (linear growth then plateau)
            # Use linear growth instead of exponential to be more realistic
            if month < self.costs.token_plateau_month:
                # Linear growth: start + (growth_rate * initial * month)
                tokens_per_dev = self.costs.initial_tokens_per_dev_month * (
                    1 + (self.costs.token_growth_rate_monthly * month)
                )
            else:
                # Plateau at the level reached
                tokens_per_dev = self.costs.initial_tokens_per_dev_month * (
                    1 + (self.costs.token_growth_rate_monthly * self.costs.token_plateau_month)
                )
            
            # Calculate total cost
            adopted_devs = self.baseline.team_size * adoption_curve[month]
            total_tokens = adopted_devs * tokens_per_dev
            monthly_costs[month] = (total_tokens / 1_000_000) * current_price
        
        return monthly_costs
    
    def calculate_training_costs(self, months: int = 24, adoption_curve: np.ndarray = None) -> np.ndarray:
        """Calculate training costs over time"""
        
        if adoption_curve is None:
            adoption_curve = np.ones(months)
        
        monthly_costs = np.zeros(months)
        
        # Initial training burst
        for month in range(min(3, months)):  # First 3 months
            new_adopters = self.baseline.team_size * (
                adoption_curve[month] - (adoption_curve[month-1] if month > 0 else 0)
            )
            monthly_costs[month] = new_adopters * self.costs.initial_training_cost_per_dev
            
            # Add trainer costs
            if new_adopters > 0:
                trainer_days = self.costs.training_days_initial * (new_adopters / 10)  # 1 trainer per 10 devs
                monthly_costs[month] += trainer_days * self.costs.trainer_cost_per_day
        
        # Ongoing training (quarterly)
        for month in range(3, months):
            if month % 3 == 0:  # Quarterly training
                adopted_devs = self.baseline.team_size * adoption_curve[month]
                monthly_costs[month] = (self.costs.ongoing_training_cost_annual / 4) * (adopted_devs / self.baseline.team_size)
        
        return monthly_costs
    
    def calculate_hidden_costs(self, months: int = 24, adoption_curve: np.ndarray = None) -> np.ndarray:
        """Calculate hidden and indirect costs"""
        
        if adoption_curve is None:
            adoption_curve = np.ones(months)
        
        monthly_costs = np.zeros(months)
        
        for month in range(months):
            adopted_devs = self.baseline.team_size * adoption_curve[month]
            
            # Context switching cost (highest in early months)
            # This is a monthly cost per developer
            if month < 6:
                context_cost = self.costs.context_switch_cost_month * adopted_devs * (1 - month/12)
            else:
                context_cost = self.costs.context_switch_cost_month * adopted_devs * 0.5
            
            # Bad code cleanup cost - percentage of dev time spent fixing AI mistakes
            hourly_rate = safe_divide(
                self.baseline.weighted_avg_flc,
                WORKING_HOURS_PER_YEAR,
                default=0.0,
                context="hourly rate calculation"
            )
            dev_hours_month = DEV_HOURS_PER_MONTH
            bad_code_hours = dev_hours_month * self.costs.bad_code_cleanup_percentage * adopted_devs
            bad_code_cost = bad_code_hours * hourly_rate
            
            # Security review overhead - additional hours per month per developer
            # Convert to hours (security_review_overhead is in hours per month)
            security_hours = adopted_devs * self.costs.security_review_overhead
            security_cost = security_hours * hourly_rate
            
            monthly_costs[month] = context_cost + bad_code_cost + security_cost
        
        return monthly_costs
    
    def calculate_total_costs(self, months: int = 24, adoption_curve: np.ndarray = None) -> Dict[str, np.ndarray]:
        """Calculate all cost components"""
        
        licensing = self.calculate_licensing_costs(months, adoption_curve)
        tokens = self.calculate_token_costs(months, adoption_curve)
        training = self.calculate_training_costs(months, adoption_curve)
        hidden = self.calculate_hidden_costs(months, adoption_curve)
        
        # Infrastructure costs (constant after setup)
        infrastructure = np.full(months, self.costs.infrastructure_monthly)
        infrastructure[0] += self.costs.infrastructure_setup
        
        # Admin overhead
        admin_cost_monthly = self.costs.admin_overhead_percentage * safe_divide(
            self.baseline.weighted_avg_flc,
            MONTHS_PER_YEAR,
            default=0.0,
            context="admin cost monthly calculation"
        )
        admin = np.full(months, admin_cost_monthly)
        
        # Experimentation costs
        experimentation = np.zeros(months)
        experimentation[0] = self.costs.pilot_budget
        for month in range(months):
            if month > 0 and month % MONTHS_PER_YEAR == 0:
                experimentation[month] = self.costs.ongoing_experimentation
        
        total = licensing + tokens + training + hidden + infrastructure + admin + experimentation
        
        return {
            "licensing": licensing,
            "tokens": tokens,
            "training": training,
            "hidden": hidden,
            "infrastructure": infrastructure,
            "admin": admin,
            "experimentation": experimentation,
            "total": total,
            "cumulative": np.cumsum(total)
        }
    
    def calculate_cost_per_developer(self, months: int = 24, adoption_curve: np.ndarray = None) -> np.ndarray:
        """Calculate average cost per adopted developer"""
        
        if adoption_curve is None:
            adoption_curve = np.ones(months)
        
        total_costs = self.calculate_total_costs(months, adoption_curve)["total"]
        cost_per_dev = np.zeros(months)
        
        for month in range(months):
            adopted_devs = self.baseline.team_size * adoption_curve[month]
            if adopted_devs > 0:
                cost_per_dev[month] = total_costs[month] / adopted_devs
            else:
                cost_per_dev[month] = 0
        
        return cost_per_dev
    
    def project_future_costs(self, years: int = 5) -> Dict[str, float]:
        """Project costs over multiple years with learning effects"""
        
        months = years * MONTHS_PER_YEAR
        # Assume S-curve adoption reaching 80% over 2 years
        adoption = np.minimum(np.arange(months) / 24, 0.8)
        
        costs = self.calculate_total_costs(months, adoption)
        
        yearly_costs = {}
        for year in range(years):
            start_month = year * MONTHS_PER_YEAR
            end_month = min((year + 1) * MONTHS_PER_YEAR, months)
            yearly_costs[f"year_{year+1}"] = costs["total"][start_month:end_month].sum()
        
        return yearly_costs


def create_cost_scenario(scenario: str = "standard") -> AIToolCosts:
    """Create cost structure for different scenarios"""
    
    scenarios = {
        "startup": AIToolCosts(
            cost_per_seat_month=30,
            enterprise_discount=0.0,
            initial_tokens_per_dev_month=200_000,  # 200K tokens/month for startup
            token_price_per_million=10,
            token_price_decline_annual=0.3,
            token_growth_rate_monthly=0.15,
            token_plateau_month=9,
            initial_training_cost_per_dev=500,
            ongoing_training_cost_annual=200,
            trainer_cost_per_day=1500,
            training_days_initial=2,
            training_days_ongoing_annual=1,
            infrastructure_setup=5_000,
            infrastructure_monthly=500,
            admin_overhead_percentage=0.02,
            context_switch_cost_month=500,
            bad_code_cleanup_percentage=0.05,
            security_review_overhead=2,  # 2 hours per month per developer
            pilot_budget=10_000,
            ongoing_experimentation=5_000
        ),
        
        "enterprise": AIToolCosts(
            cost_per_seat_month=50,
            enterprise_discount=0.3,
            initial_tokens_per_dev_month=500_000,  # 500K tokens/month is more realistic
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
            security_review_overhead=4,  # 4 hours per month per developer
            pilot_budget=100_000,
            ongoing_experimentation=50_000
        ),
        
        "aggressive": AIToolCosts(
            cost_per_seat_month=100,
            enterprise_discount=0.2,
            initial_tokens_per_dev_month=1_000_000,  # 1M tokens/month for aggressive usage
            token_price_per_million=6,
            token_price_decline_annual=0.35,
            token_growth_rate_monthly=0.20,
            token_plateau_month=6,
            initial_training_cost_per_dev=3_000,
            ongoing_training_cost_annual=1_000,
            trainer_cost_per_day=2_500,
            training_days_initial=7,
            training_days_ongoing_annual=4,
            infrastructure_setup=20_000,
            infrastructure_monthly=2_000,
            admin_overhead_percentage=0.03,
            context_switch_cost_month=2_000,
            bad_code_cleanup_percentage=0.10,
            security_review_overhead=3,  # 3 hours per month per developer
            pilot_budget=50_000,
            ongoing_experimentation=25_000
        )
    }
    
    return scenarios.get(scenario, scenarios["enterprise"])


def calculate_breakeven(
    costs: Dict[str, np.ndarray],
    value: Dict[str, np.ndarray]
) -> Optional[int]:
    """Calculate breakeven month where cumulative value exceeds cumulative costs"""
    
    cumulative_costs = costs.get("cumulative", np.cumsum(costs.get("total", [])))
    cumulative_value = np.cumsum(value.get("total", []))
    
    for month in range(len(cumulative_costs)):
        if cumulative_value[month] >= cumulative_costs[month]:
            return month
    
    return None  # No breakeven within timeframe