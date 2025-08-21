"""
Monte Carlo visualization and reporting utilities.
Provides text-based visualizations for Monte Carlo simulation results.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from ..utils.colors import *
from ..utils.math_helpers import safe_divide


def create_distribution_sparkline(data: np.ndarray, width: int = 50) -> str:
    """Create a text-based sparkline for a distribution"""
    chars = "▁▂▃▄▅▆▇█"
    
    # Calculate histogram
    counts, _ = np.histogram(data, bins=width)
    max_count = max(counts) if max(counts) > 0 else 1
    
    # Create sparkline
    sparkline = ""
    for count in counts:
        idx = min(int((count / max_count) * (len(chars) - 1)), len(chars) - 1)
        sparkline += chars[idx]
    
    return sparkline


def format_percentile_table(stats: Dict[str, float], currency: bool = False) -> str:
    """Format percentile statistics as a table"""
    lines = []
    
    percentiles = ['p5', 'p10', 'p25', 'p50', 'p75', 'p90', 'p95']
    
    for p in percentiles:
        if p in stats:
            value = stats[p]
            if currency:
                formatted = f"${value:,.0f}"
            else:
                formatted = f"{value:.1f}"
            
            # Color code based on percentile
            if p in ['p5', 'p10']:
                formatted = error(formatted)
            elif p in ['p25']:
                formatted = warning(formatted)
            elif p in ['p50']:
                formatted = metric(formatted)
            elif p in ['p75']:
                formatted = info(formatted)
            else:  # p90, p95
                formatted = success(formatted)
            
            lines.append(f"  {p.upper():<5} {formatted}")
    
    return "\n".join(lines)


def create_confidence_interval_visualization(lower: float, upper: float, mean: float, 
                                           currency: bool = False, width: int = 40) -> str:
    """Create a visual representation of confidence interval"""
    # Normalize values to [0, 1] range
    range_val = upper - lower
    if range_val == 0:
        return "─" * width
    
    mean_pos = int(((mean - lower) / range_val) * width)
    
    # Build visualization
    viz = ""
    for i in range(width):
        if i == mean_pos:
            viz += "│"
        elif i == 0:
            viz += "["
        elif i == width - 1:
            viz += "]"
        else:
            viz += "─"
    
    # Add labels
    if currency:
        lower_label = f"${lower/1000:.0f}K"
        upper_label = f"${upper/1000:.0f}K"
        mean_label = f"${mean/1000:.0f}K"
    else:
        lower_label = f"{lower:.1f}"
        upper_label = f"{upper:.1f}"
        mean_label = f"{mean:.1f}"
    
    return f"{lower_label} {viz} {upper_label}\n{' ' * (len(lower_label) + mean_pos)} ↑ {mean_label}"


def create_risk_gauge(probability: float, width: int = 30) -> str:
    """Create a risk gauge visualization"""
    filled = int(probability * width)
    empty = width - filled
    
    gauge = "█" * filled + "░" * empty
    
    # Color based on probability
    if probability >= 0.8:
        gauge = success(gauge)
    elif probability >= 0.6:
        gauge = warning(gauge)
    else:
        gauge = error(gauge)
    
    return f"[{gauge}] {probability:.1%}"


def create_sensitivity_tornado_chart(correlations: Dict[str, float], top_n: int = 10) -> str:
    """Create a tornado chart for sensitivity analysis"""
    # Sort by absolute correlation
    sorted_params = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)[:top_n]
    
    lines = []
    max_corr = max(abs(c) for _, c in sorted_params) if sorted_params else 1
    
    for param, corr in sorted_params:
        # Normalize to chart width
        bar_width = int(abs(corr / max_corr) * 30)
        
        if corr > 0:
            # Positive correlation - bar goes right
            bar = " " * 30 + "│" + "█" * bar_width
            bar = success("█" * bar_width)
            line = f"{param[:30]:<30} │{' ' * 30}{bar}"
        else:
            # Negative correlation - bar goes left
            bar = error("█" * bar_width)
            padding = 30 - bar_width
            line = f"{param[:30]:<30} │{' ' * padding}{bar}{'█' * 0}"
        
        lines.append(line)
        lines.append(f"{' ' * 30} │{' ' * 26}{corr:+.3f}")
    
    # Add axis
    lines.insert(0, f"{' ' * 30} │{' ' * 15}0")
    lines.insert(0, f"{' ' * 30} {'─' * 31}")
    
    return "\n".join(lines)


def create_outcome_probability_report(mc_results) -> str:
    """Create a comprehensive probability report for key outcomes"""
    lines = []
    
    lines.append(header("OUTCOME PROBABILITIES"))
    lines.append("")
    
    # NPV outcomes
    lines.append(f"{'NPV Outcomes':<30}")
    lines.append(f"  Positive NPV: {create_risk_gauge(mc_results.probability_positive_npv)}")
    
    npv_thresholds = [1_000_000, 2_000_000, 5_000_000]
    for threshold in npv_thresholds:
        prob = np.mean(mc_results.npv_distribution > threshold)
        lines.append(f"  NPV > ${threshold/1_000_000:.0f}M: {create_risk_gauge(prob)}")
    
    lines.append("")
    
    # ROI outcomes
    lines.append(f"{'ROI Outcomes':<30}")
    roi_thresholds = [50, 100, 150, 200]
    for threshold in roi_thresholds:
        prob = np.mean(mc_results.roi_distribution > threshold)
        lines.append(f"  ROI > {threshold}%: {create_risk_gauge(prob)}")
    
    lines.append("")
    
    # Breakeven outcomes
    lines.append(f"{'Breakeven Outcomes':<30}")
    breakeven_thresholds = [12, 18, 24, 36]
    for threshold in breakeven_thresholds:
        prob = np.mean(mc_results.breakeven_distribution <= threshold)
        lines.append(f"  Breakeven ≤ {threshold} months: {create_risk_gauge(prob)}")
    
    return "\n".join(lines)


def create_value_at_risk_report(mc_results, confidence_levels: List[float] = [0.05, 0.10, 0.25]) -> str:
    """Create Value at Risk (VaR) and Conditional Value at Risk (CVaR) report"""
    lines = []
    
    lines.append(header("VALUE AT RISK ANALYSIS"))
    lines.append("")
    
    for conf in confidence_levels:
        percentile = conf * 100
        var_npv = np.percentile(mc_results.npv_distribution, percentile)
        var_roi = np.percentile(mc_results.roi_distribution, percentile)
        
        # Calculate CVaR (expected value below VaR)
        cvar_npv = np.mean(mc_results.npv_distribution[mc_results.npv_distribution <= var_npv])
        cvar_roi = np.mean(mc_results.roi_distribution[mc_results.roi_distribution <= var_roi])
        
        lines.append(f"{int(percentile)}th Percentile Risk:")
        lines.append(f"  VaR NPV: {error(f'${var_npv:,.0f}')}")
        lines.append(f"  CVaR NPV: {error(f'${cvar_npv:,.0f}')} (expected loss if worse than VaR)")
        lines.append(f"  VaR ROI: {error(f'{var_roi:.1f}%')}")
        lines.append(f"  CVaR ROI: {error(f'{cvar_roi:.1f}%')}")
        lines.append("")
    
    return "\n".join(lines)


def create_scenario_comparison_matrix(mc_results_dict: Dict[str, any]) -> str:
    """Compare multiple Monte Carlo scenarios in a matrix"""
    lines = []
    
    lines.append(header("MONTE CARLO SCENARIO COMPARISON"))
    lines.append("")
    
    # Headers
    headers = ["Scenario", "NPV P50", "NPV P10-P90", "ROI P50", "P(NPV>0)", "P(BE<24m)"]
    
    # Data rows
    rows = []
    for scenario_name, results in mc_results_dict.items():
        row = [
            scenario_name[:20],
            f"${results.npv_stats['p50']/1_000_000:.1f}M",
            f"${results.npv_stats['p10']/1_000_000:.1f}M-${results.npv_stats['p90']/1_000_000:.1f}M",
            f"{results.roi_stats['p50']:.0f}%",
            f"{results.probability_positive_npv:.0%}",
            f"{results.probability_breakeven_within_24_months:.0%}"
        ]
        rows.append(row)
    
    # Create simple text table without tabulate dependency
    # Find column widths
    col_widths = [max(len(str(headers[i])), max(len(str(row[i])) for row in rows)) for i in range(len(headers))]
    
    # Create header row
    header_row = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
    lines.append(header_row)
    lines.append("-" * len(header_row))
    
    # Create data rows
    for row in rows:
        data_row = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
        lines.append(data_row)
    
    return "\n".join(lines)


def export_monte_carlo_report(mc_results, filename: str, scenario_name: str):
    """Export comprehensive Monte Carlo report to file"""
    from datetime import datetime
    
    lines = []
    
    # Header
    lines.append(f"# Monte Carlo Analysis Report: {scenario_name}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Iterations: {mc_results.iterations}")
    lines.append(f"Random Seed: {mc_results.random_seed or 'None'}")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append(f"- **NPV (P50)**: ${mc_results.npv_stats['p50']:,.0f}")
    lines.append(f"- **NPV Range (P10-P90)**: ${mc_results.npv_stats['p10']:,.0f} to ${mc_results.npv_stats['p90']:,.0f}")
    lines.append(f"- **Probability of Positive NPV**: {mc_results.probability_positive_npv:.1%}")
    lines.append(f"- **ROI (P50)**: {mc_results.roi_stats['p50']:.1f}%")
    lines.append(f"- **Probability of Breakeven < 24 months**: {mc_results.probability_breakeven_within_24_months:.1%}")
    lines.append("")
    
    # Distribution Statistics
    lines.append("## Distribution Statistics")
    lines.append("")
    lines.append("### NPV Distribution")
    lines.append(f"- Mean: ${mc_results.npv_stats['mean']:,.0f}")
    lines.append(f"- Std Dev: ${mc_results.npv_stats['std']:,.0f}")
    lines.append(f"- Skewness: {mc_results.npv_stats['skewness']:.2f}")
    lines.append(f"- Kurtosis: {mc_results.npv_stats['kurtosis']:.2f}")
    lines.append("")
    
    # Percentiles
    lines.append("### Percentiles")
    lines.append("```")
    lines.append(format_percentile_table(mc_results.npv_stats, currency=True))
    lines.append("```")
    lines.append("")
    
    # Risk Analysis
    lines.append("## Risk Analysis")
    lines.append(create_value_at_risk_report(mc_results))
    lines.append("")
    
    # Sensitivity Analysis
    lines.append("## Sensitivity Analysis")
    lines.append("Top 10 parameters by impact on NPV:")
    lines.append("```")
    for i, (param, importance) in enumerate(mc_results.parameter_importance[:10], 1):
        corr = mc_results.parameter_correlations[param]
        lines.append(f"{i:2}. {param:<40} Correlation: {corr:+.3f}")
    lines.append("```")
    lines.append("")
    
    # Outcome Probabilities
    lines.append("## Outcome Probabilities")
    lines.append(create_outcome_probability_report(mc_results))
    
    # Write to file
    with open(filename, 'w') as f:
        f.write("\n".join(lines))
    
    print(f"Monte Carlo report saved to: {info(filename)}")