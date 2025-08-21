"""
Financial calculations module for NPV, IRR, and other financial metrics.
Provides centralized, validated financial calculations for the AI impact model.
"""

from typing import List, Union, Optional, Tuple
import numpy as np
import numpy_financial as npf
from scipy import optimize
from ..utils.math_helpers import safe_divide
from ..utils.exceptions import CalculationError


def calculate_npv(
    cash_flows: Union[List[float], np.ndarray],
    discount_rate: float,
    periods: Optional[Union[List[float], np.ndarray]] = None
) -> float:
    """
    Calculate Net Present Value of cash flows.
    
    Args:
        cash_flows: Array of cash flows (positive = inflow, negative = outflow)
        discount_rate: Annual discount rate (e.g., 0.10 for 10%)
        periods: Optional array of time periods for each cash flow (in years).
                If None, assumes regular intervals starting at t=0
    
    Returns:
        Net Present Value
        
    Raises:
        CalculationError: If inputs are invalid
    """
    cash_flows = np.asarray(cash_flows)
    
    if len(cash_flows) == 0:
        raise CalculationError("NPV calculation", "Cash flows array is empty")
    
    if discount_rate <= -1:
        raise CalculationError("NPV calculation", f"Discount rate {discount_rate} would cause division by zero")
    
    if periods is None:
        # Assume regular intervals (0, 1, 2, ...)
        periods = np.arange(len(cash_flows))
    else:
        periods = np.asarray(periods)
        
    if len(periods) != len(cash_flows):
        raise CalculationError(
            "NPV calculation",
            f"Periods array length ({len(periods)}) must match cash flows length ({len(cash_flows)})"
        )
    
    # Calculate present value factors
    pv_factors = 1 / (1 + discount_rate) ** periods
    
    # Calculate NPV
    npv = np.sum(cash_flows * pv_factors)
    
    return float(npv)


def calculate_npv_monthly(
    monthly_cash_flows: Union[List[float], np.ndarray],
    annual_discount_rate: float
) -> float:
    """
    Calculate NPV for monthly cash flows using annual discount rate.
    
    Args:
        monthly_cash_flows: Array of monthly cash flows
        annual_discount_rate: Annual discount rate (e.g., 0.10 for 10%)
    
    Returns:
        Net Present Value
    """
    # Convert annual rate to monthly
    monthly_rate = (1 + annual_discount_rate) ** (1/12) - 1
    
    # Create monthly periods (0, 1/12, 2/12, ...)
    n_months = len(monthly_cash_flows)
    periods_years = np.arange(n_months) / 12
    
    return calculate_npv(monthly_cash_flows, annual_discount_rate, periods_years)


def calculate_irr(
    cash_flows: Union[List[float], np.ndarray],
    guess: float = 0.1
) -> Optional[float]:
    """
    Calculate Internal Rate of Return.
    
    Args:
        cash_flows: Array of cash flows (typically first value is negative investment)
        guess: Initial guess for IRR (default 10%)
    
    Returns:
        Internal Rate of Return or None if cannot be calculated
    """
    cash_flows = np.asarray(cash_flows)
    
    if len(cash_flows) < 2:
        return None
    
    # Check if there's at least one sign change (required for IRR)
    signs = np.sign(cash_flows[cash_flows != 0])
    if len(np.unique(signs)) < 2:
        return None  # No sign change, IRR undefined
    
    try:
        # Use numpy_financial's IRR calculation
        result = npf.irr(cash_flows)
        if np.isnan(result):
            # Try scipy optimization as fallback
            def npv_func(rate):
                return calculate_npv(cash_flows, rate)
            
            try:
                result = optimize.brentq(npv_func, -0.99, 10, maxiter=100)
            except:
                return None
        
        return float(result) if not np.isnan(result) else None
    except:
        return None


def calculate_payback_period(
    cash_flows: Union[List[float], np.ndarray],
    periods: Optional[Union[List[float], np.ndarray]] = None
) -> Optional[float]:
    """
    Calculate payback period (time to recover initial investment).
    
    Args:
        cash_flows: Array of cash flows
        periods: Optional array of time periods (in years)
    
    Returns:
        Payback period in years or None if never recovers
    """
    cash_flows = np.asarray(cash_flows)
    
    if len(cash_flows) == 0:
        return None
    
    if periods is None:
        periods = np.arange(len(cash_flows))
    else:
        periods = np.asarray(periods)
    
    # Calculate cumulative cash flow
    cumulative = np.cumsum(cash_flows)
    
    # Find first period where cumulative becomes positive
    positive_indices = np.where(cumulative > 0)[0]
    
    if len(positive_indices) == 0:
        return None  # Never recovers
    
    first_positive_idx = positive_indices[0]
    
    if first_positive_idx == 0:
        return 0.0  # Immediate payback
    
    # Linear interpolation for more precise payback period
    prev_cumulative = cumulative[first_positive_idx - 1]
    curr_cumulative = cumulative[first_positive_idx]
    
    # Fraction of period needed to break even
    fraction = -prev_cumulative / (curr_cumulative - prev_cumulative)
    
    # Calculate exact payback period
    if first_positive_idx > 0:
        prev_period = periods[first_positive_idx - 1]
        curr_period = periods[first_positive_idx]
        payback = prev_period + fraction * (curr_period - prev_period)
    else:
        payback = periods[first_positive_idx] * fraction
    
    return float(payback)


def calculate_roi(
    total_value: float,
    total_cost: float
) -> float:
    """
    Calculate Return on Investment.
    
    Args:
        total_value: Total value generated
        total_cost: Total cost incurred
    
    Returns:
        ROI as a ratio (e.g., 1.5 for 150% ROI)
    """
    if total_cost == 0:
        return float('inf') if total_value > 0 else 0.0
    
    return (total_value - total_cost) / total_cost


def calculate_profitability_index(
    future_cash_flows: Union[List[float], np.ndarray],
    initial_investment: float,
    discount_rate: float,
    periods: Optional[Union[List[float], np.ndarray]] = None
) -> float:
    """
    Calculate Profitability Index (PI).
    
    PI = PV of future cash flows / Initial Investment
    
    Args:
        future_cash_flows: Array of future cash flows (excluding initial investment)
        initial_investment: Initial investment amount (positive value)
        discount_rate: Discount rate
        periods: Optional array of time periods
    
    Returns:
        Profitability Index
    """
    if initial_investment <= 0:
        raise CalculationError("Profitability Index", "Initial investment must be positive")
    
    pv_future_flows = calculate_npv(future_cash_flows, discount_rate, periods)
    
    return pv_future_flows / initial_investment


def calculate_discounted_payback(
    cash_flows: Union[List[float], np.ndarray],
    discount_rate: float,
    periods: Optional[Union[List[float], np.ndarray]] = None
) -> Optional[float]:
    """
    Calculate discounted payback period.
    
    Args:
        cash_flows: Array of cash flows
        discount_rate: Discount rate
        periods: Optional array of time periods
    
    Returns:
        Discounted payback period or None if never recovers
    """
    cash_flows = np.asarray(cash_flows)
    
    if periods is None:
        periods = np.arange(len(cash_flows))
    else:
        periods = np.asarray(periods)
    
    # Calculate present value of each cash flow
    pv_factors = 1 / (1 + discount_rate) ** periods
    discounted_flows = cash_flows * pv_factors
    
    # Use regular payback calculation on discounted flows
    return calculate_payback_period(discounted_flows, periods)


def calculate_break_even_point(
    fixed_costs: float,
    variable_cost_per_unit: float,
    price_per_unit: float
) -> Optional[float]:
    """
    Calculate break-even point in units.
    
    Args:
        fixed_costs: Total fixed costs
        variable_cost_per_unit: Variable cost per unit
        price_per_unit: Selling price per unit
    
    Returns:
        Break-even quantity or None if impossible
    """
    contribution_margin = price_per_unit - variable_cost_per_unit
    
    if contribution_margin <= 0:
        return None  # Cannot break even if contribution margin is negative
    
    return fixed_costs / contribution_margin


def calculate_monthly_to_annual_rate(monthly_rate: float) -> float:
    """Convert monthly rate to annual rate."""
    return (1 + monthly_rate) ** 12 - 1


def calculate_annual_to_monthly_rate(annual_rate: float) -> float:
    """Convert annual rate to monthly rate."""
    return (1 + annual_rate) ** (1/12) - 1