"""
Text-based visualization utilities for AI development impact model.
Creates console-friendly charts and summary tables.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional


def create_summary_table(data: Dict, title: str = "Summary") -> str:
    """Create a formatted text table from data dictionary"""
    
    max_key_length = max(len(str(k)) for k in data.keys())
    max_val_length = max(len(str(v)) for v in data.values())
    
    # Create table header
    header = f"{title}"
    separator = "-" * max(len(header), max_key_length + max_val_length + 3)
    
    table = f"{header}\n{separator}\n"
    
    for key, value in data.items():
        table += f"{key:<{max_key_length}} : {value}\n"
    
    return table


def format_currency(value: float) -> str:
    """Format value as currency string"""
    if value >= 1e6:
        return f"${value/1e6:.1f}M"
    elif value >= 1e3:
        return f"${value/1e3:.0f}K"
    else:
        return f"${value:.0f}"


def format_percentage(value: float) -> str:
    """Format value as percentage string"""
    return f"{value*100:.1f}%"


def create_ascii_chart(values: List[float], labels: List[str] = None, 
                      title: str = "Chart", width: int = 60) -> str:
    """Create simple ASCII bar chart"""
    
    if not values:
        return f"{title}\nNo data to display"
    
    max_val = max(values)
    min_val = min(values)
    
    # Normalize values to chart width
    if max_val > min_val:
        normalized = [(v - min_val) / (max_val - min_val) * width for v in values]
    else:
        normalized = [width // 2 for _ in values]
    
    chart = f"{title}\n{'=' * len(title)}\n"
    
    for i, (val, norm) in enumerate(zip(values, normalized)):
        label = labels[i] if labels and i < len(labels) else f"Item {i+1}"
        bar = "█" * int(norm)
        chart += f"{label[:15]:<15} |{bar:<{width}} {format_currency(val)}\n"
    
    return chart


def create_timeline_chart(values: List[float], title: str = "Timeline", 
                         months: int = None) -> str:
    """Create ASCII timeline chart"""
    
    if not values:
        return f"{title}\nNo data to display"
    
    chart = f"{title}\n{'=' * len(title)}\n"
    
    max_val = max(values)
    min_val = min(values) if min(values) < 0 else 0
    
    # Create simple timeline representation
    for i, val in enumerate(values):
        month = i + 1
        if val >= 0:
            bar_len = int((val / max_val) * 30) if max_val > 0 else 0
            bar = "+" * bar_len
            chart += f"Month {month:2d} |{bar:<30} {format_currency(val)}\n"
        else:
            bar_len = int((abs(val) / abs(min_val)) * 30) if min_val < 0 else 0
            bar = "-" * bar_len
            chart += f"Month {month:2d} |{bar:<30} {format_currency(val)}\n"
    
    return chart


class ModelVisualizer:
    """Create text-based visualizations for model outputs"""
    
    def __init__(self):
        self.charts = {}
    
    def create_adoption_summary(self, adoption_curve: np.ndarray, 
                              efficiency_curve: np.ndarray) -> str:
        """Create text summary of adoption patterns"""
        
        max_adoption = max(adoption_curve)
        final_adoption = adoption_curve[-1]
        months_to_50pct = None
        
        # Find month when 50% adoption reached
        for i, adoption in enumerate(adoption_curve):
            if adoption >= 0.5:
                months_to_50pct = i + 1
                break
        
        summary = "ADOPTION ANALYSIS\n"
        summary += "=" * 17 + "\n"
        summary += f"Peak Adoption Rate    : {format_percentage(max_adoption)}\n"
        summary += f"Final Adoption Rate   : {format_percentage(final_adoption)}\n"
        summary += f"Months to 50% Adoption: {months_to_50pct or 'Not reached'}\n"
        summary += f"Final Efficiency      : {format_percentage(efficiency_curve[-1])}\n"
        
        return summary
    
    def create_cost_breakdown(self, costs: Dict) -> str:
        """Create text breakdown of costs"""
        
        total_costs = sum(costs['total'])
        
        breakdown = "COST BREAKDOWN\n"
        breakdown += "=" * 14 + "\n"
        breakdown += f"Total Investment      : {format_currency(total_costs)}\n"
        breakdown += f"Monthly Average       : {format_currency(total_costs / len(costs['total']))}\n"
        
        if 'licensing' in costs:
            licensing_total = sum(costs['licensing'])
            breakdown += f"Licensing Costs       : {format_currency(licensing_total)}\n"
        
        if 'tokens' in costs:
            token_total = sum(costs['tokens'])
            breakdown += f"Token Costs           : {format_currency(token_total)}\n"
        
        if 'training' in costs:
            training_total = sum(costs['training'])
            breakdown += f"Training Costs        : {format_currency(training_total)}\n"
        
        return breakdown
    
    def create_value_summary(self, impact_breakdown: Dict) -> str:
        """Create text summary of value creation"""
        
        summary = "VALUE CREATION\n"
        summary += "=" * 14 + "\n"
        summary += f"Total Annual Value    : {format_currency(impact_breakdown['total_annual_value'])}\n"
        summary += f"Time-to-Market Value  : {format_currency(impact_breakdown['time_value'])}\n"
        summary += f"Quality Value         : {format_currency(impact_breakdown['quality_value'])}\n"
        summary += f"Capacity Value        : {format_currency(impact_breakdown['capacity_value'])}\n"
        summary += f"Strategic Value       : {format_currency(impact_breakdown['strategic_value'])}\n"
        summary += f"Value per Developer   : {format_currency(impact_breakdown['value_per_developer'])}\n"
        
        return summary
    
    def create_executive_summary(self, results: Dict) -> str:
        """Create comprehensive executive summary"""
        
        summary = f"EXECUTIVE SUMMARY: {results['scenario_name'].upper()}\n"
        summary += "=" * (19 + len(results['scenario_name'])) + "\n\n"
        
        # Key metrics
        summary += "KEY METRICS\n"
        summary += "-" * 11 + "\n"
        summary += f"Net Present Value     : {format_currency(results['npv'])}\n"
        summary += f"Return on Investment  : {results['roi_percent']:.1f}%\n"
        summary += f"Breakeven Month       : {results['breakeven_month'] or 'Not reached'}\n"
        summary += f"Peak Adoption         : {format_percentage(results['peak_adoption'])}\n"
        summary += f"Team Size             : {results['baseline'].team_size} developers\n\n"
        
        # Financial summary
        summary += "FINANCIAL IMPACT (3 YEARS)\n"
        summary += "-" * 26 + "\n"
        summary += f"Total Investment      : {format_currency(results['total_cost_3y'])}\n"
        summary += f"Total Value Created   : {format_currency(results['total_value_3y'])}\n"
        summary += f"Net Benefit           : {format_currency(results['total_value_3y'] - results['total_cost_3y'])}\n\n"
        
        # Per-developer metrics
        summary += "PER DEVELOPER (ANNUAL)\n"
        summary += "-" * 22 + "\n"
        summary += f"Cost per Developer    : {format_currency(results['annual_cost_per_dev'])}\n"
        summary += f"Value per Developer   : {format_currency(results['annual_value_per_dev'])}\n\n"
        
        return summary
    
    def export_charts(self, charts: Dict, output_dir: str = "outputs/charts"):
        """Export text summaries to files (no-op for compatibility)"""
        # This method exists for compatibility but does nothing
        # since we're now text-only
        pass


# Utility functions for backward compatibility
def plot_adoption_curve(*args, **kwargs):
    """Compatibility function - returns empty dict"""
    return {}


def plot_cost_breakdown(*args, **kwargs):
    """Compatibility function - returns empty dict"""  
    return {}


def plot_roi_timeline(*args, **kwargs):
    """Compatibility function - returns empty dict"""
    return {}


def plot_value_components(*args, **kwargs):
    """Compatibility function - returns empty dict"""
    return {}