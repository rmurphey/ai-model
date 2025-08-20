#!/usr/bin/env python3
"""
Monte Carlo analysis for AI impact model - showing uncertainty in outcomes
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from scipy import stats

from baseline import create_industry_baseline
from impact_model import create_impact_scenario, BusinessImpact
from adoption_dynamics import create_adoption_scenario, AdoptionModel, simulate_adoption_monte_carlo
from cost_structure import create_cost_scenario, CostModel

def run_monte_carlo_scenario(scenario_name, n_simulations=1000):
    """Run Monte Carlo simulation for a specific scenario"""
    
    print(f"Running Monte Carlo for {scenario_name} ({n_simulations} simulations)...")
    
    # Parse scenario name
    approach, company = scenario_name.rsplit('_', 1)
    
    # Get base parameters
    if company == 'startup':
        baseline = create_industry_baseline('startup')
        costs = create_cost_scenario('startup')
        months = 24
    elif company == 'enterprise':
        baseline = create_industry_baseline('enterprise')
        costs = create_cost_scenario('enterprise')
        months = 36
    else:  # scaleup
        baseline = create_industry_baseline('scale_up')
        costs = create_cost_scenario('aggressive')
        months = 24
    
    # Get adoption and impact scenarios
    if approach == 'conservative':
        adoption_base = create_adoption_scenario('organic')
        impact_base = create_impact_scenario('conservative')
    elif approach == 'moderate':
        adoption_base = create_adoption_scenario('grassroots')
        impact_base = create_impact_scenario('moderate')
    else:  # aggressive
        adoption_base = create_adoption_scenario('mandated')
        impact_base = create_impact_scenario('aggressive')
    
    # Run simulations
    npvs = []
    rois = []
    paybacks = []
    peak_adoptions = []
    
    for sim in range(n_simulations):
        # Add variation to parameters (±20% for most parameters)
        
        # Vary adoption parameters
        adoption_params = create_adoption_scenario(
            'organic' if approach == 'conservative' else 
            'grassroots' if approach == 'moderate' else 'mandated'
        )
        adoption_params.dropout_rate_month *= np.random.uniform(0.5, 1.5)
        adoption_params.learning_rate *= np.random.uniform(0.7, 1.3)
        adoption_params.plateau_efficiency *= np.random.uniform(0.9, 1.05)
        
        # Vary impact factors
        impact_variation = np.random.uniform(0.8, 1.2)
        impact_factors = create_impact_scenario(
            'conservative' if approach == 'conservative' else
            'moderate' if approach == 'moderate' else 'aggressive'
        )
        impact_factors.feature_cycle_reduction *= impact_variation
        impact_factors.defect_reduction *= impact_variation
        impact_factors.incident_reduction *= impact_variation
        
        # Vary costs
        cost_variation = np.random.uniform(0.9, 1.3)
        varied_costs = create_cost_scenario(
            'startup' if company == 'startup' else
            'enterprise' if company == 'enterprise' else 'aggressive'
        )
        varied_costs.cost_per_seat_month *= cost_variation
        varied_costs.token_price_per_million *= np.random.uniform(0.7, 1.5)
        
        # Calculate adoption curve
        adoption_model = AdoptionModel(adoption_params)
        adoption_curve = adoption_model.calculate_adoption_curve(months)
        efficiency_curve = adoption_model.calculate_efficiency_curve(months)
        effective_adoption = adoption_curve * efficiency_curve
        
        # Calculate costs
        cost_model = CostModel(varied_costs, baseline)
        costs_data = cost_model.calculate_total_costs(months, effective_adoption)
        
        # Calculate value
        monthly_value = np.zeros(months)
        for month in range(months):
            impact = BusinessImpact(baseline, impact_factors, effective_adoption[month])
            monthly_impact = impact.calculate_total_impact()
            monthly_value[month] = monthly_impact['total_annual_value'] / 12
        
        # Calculate metrics
        cumulative_value = np.cumsum(monthly_value)
        cumulative_costs = costs_data['cumulative']
        
        # NPV (10% annual discount rate)
        discount_rate = 0.10 / 12
        discount_factors = [(1 + discount_rate) ** -i for i in range(months)]
        npv = sum((monthly_value[i] - costs_data['total'][i]) * discount_factors[i] 
                 for i in range(months))
        
        # ROI
        total_cost = sum(costs_data['total'])
        total_value = sum(monthly_value)
        roi = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        # Payback
        payback = None
        for m in range(months):
            if cumulative_value[m] >= cumulative_costs[m]:
                payback = m
                break
        
        npvs.append(npv)
        rois.append(roi)
        paybacks.append(payback if payback else 999)
        peak_adoptions.append(max(adoption_curve))
    
    return {
        'npvs': np.array(npvs),
        'rois': np.array(rois),
        'paybacks': np.array(paybacks),
        'peak_adoptions': np.array(peak_adoptions),
        'scenario': scenario_name
    }

def create_monte_carlo_visualization(results_dict):
    """Create visualization of Monte Carlo results"""
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'NPV Distribution',
            'ROI Distribution',
            'Payback Period Distribution',
            'Risk-Return Analysis'
        ),
        specs=[
            [{"type": "box"}, {"type": "box"}],
            [{"type": "histogram"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    colors = px.colors.qualitative.Set2
    scenarios = list(results_dict.keys())
    
    # 1. NPV Box plots
    for i, scenario in enumerate(scenarios):
        fig.add_trace(
            go.Box(
                y=results_dict[scenario]['npvs'],
                name=scenario.replace('_', ' ').title(),
                marker_color=colors[i % len(colors)],
                showlegend=True
            ),
            row=1, col=1
        )
    
    # 2. ROI Box plots
    for i, scenario in enumerate(scenarios):
        fig.add_trace(
            go.Box(
                y=results_dict[scenario]['rois'],
                name=scenario.replace('_', ' ').title(),
                marker_color=colors[i % len(colors)],
                showlegend=False
            ),
            row=1, col=2
        )
    
    # 3. Payback histogram for selected scenario (moderate_enterprise)
    if 'moderate_enterprise' in results_dict:
        paybacks = results_dict['moderate_enterprise']['paybacks']
        paybacks_filtered = paybacks[paybacks < 999]
        
        fig.add_trace(
            go.Histogram(
                x=paybacks_filtered,
                nbinsx=20,
                name='Moderate Enterprise',
                marker_color=colors[1],
                showlegend=False
            ),
            row=2, col=1
        )
    
    # 4. Risk-Return scatter
    for i, scenario in enumerate(scenarios):
        npv_mean = np.mean(results_dict[scenario]['npvs'])
        npv_std = np.std(results_dict[scenario]['npvs'])
        roi_mean = np.mean(results_dict[scenario]['rois'])
        
        fig.add_trace(
            go.Scatter(
                x=[npv_std],
                y=[npv_mean],
                mode='markers+text',
                name=scenario.replace('_', ' ').title(),
                text=[scenario.split('_')[0]],
                textposition='top center',
                marker=dict(
                    size=roi_mean/10,  # Size based on ROI
                    color=colors[i % len(colors)],
                    line=dict(width=2, color='white')
                ),
                showlegend=False
            ),
            row=2, col=2
        )
    
    # Update layouts
    fig.update_layout(
        title='Monte Carlo Analysis - Uncertainty in AI Impact Model',
        height=800,
        showlegend=True
    )
    
    fig.update_yaxes(title_text="NPV ($)", row=1, col=1, tickformat='$,.0f')
    fig.update_yaxes(title_text="ROI (%)", row=1, col=2)
    fig.update_xaxes(title_text="Payback (months)", row=2, col=1)
    fig.update_xaxes(title_text="Risk (NPV Std Dev)", row=2, col=2, tickformat='$,.0f')
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    fig.update_yaxes(title_text="Expected Return (Mean NPV)", row=2, col=2, tickformat='$,.0f')
    
    return fig

def create_confidence_bands_visualization(results_dict):
    """Create visualization showing confidence bands for key metrics"""
    
    fig = go.Figure()
    
    scenarios = list(results_dict.keys())
    metrics_data = []
    
    for scenario in scenarios:
        npvs = results_dict[scenario]['npvs']
        
        # Calculate percentiles
        p10 = np.percentile(npvs, 10)
        p25 = np.percentile(npvs, 25)
        p50 = np.percentile(npvs, 50)
        p75 = np.percentile(npvs, 75)
        p90 = np.percentile(npvs, 90)
        mean = np.mean(npvs)
        
        metrics_data.append({
            'scenario': scenario,
            'p10': p10,
            'p25': p25,
            'p50': p50,
            'p75': p75,
            'p90': p90,
            'mean': mean
        })
    
    # Sort by median NPV
    metrics_data.sort(key=lambda x: x['p50'], reverse=True)
    scenario_labels = [m['scenario'].replace('_', ' ').title() for m in metrics_data]
    
    # Create candlestick-like chart
    for i, m in enumerate(metrics_data):
        # 10-90 percentile range (thin line)
        fig.add_trace(go.Scatter(
            x=[i, i],
            y=[m['p10'], m['p90']],
            mode='lines',
            line=dict(color='lightgray', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # 25-75 percentile box
        fig.add_trace(go.Bar(
            x=[i],
            y=[m['p75'] - m['p25']],
            base=m['p25'],
            width=0.3,
            marker_color='lightblue',
            opacity=0.7,
            showlegend=False,
            hovertemplate=f"{m['scenario']}<br>P25: ${m['p25']:,.0f}<br>P75: ${m['p75']:,.0f}<extra></extra>"
        ))
        
        # Median line
        fig.add_trace(go.Scatter(
            x=[i - 0.15, i + 0.15],
            y=[m['p50'], m['p50']],
            mode='lines',
            line=dict(color='darkblue', width=3),
            showlegend=False,
            hovertemplate=f"Median: ${m['p50']:,.0f}<extra></extra>"
        ))
        
        # Mean marker
        fig.add_trace(go.Scatter(
            x=[i],
            y=[m['mean']],
            mode='markers',
            marker=dict(symbol='diamond', size=8, color='red'),
            showlegend=False,
            hovertemplate=f"Mean: ${m['mean']:,.0f}<extra></extra>"
        ))
    
    fig.update_layout(
        title='NPV Confidence Intervals Across Scenarios (1000 simulations)',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(scenario_labels))),
            ticktext=scenario_labels,
            tickangle=-45
        ),
        yaxis=dict(
            title='Net Present Value ($)',
            tickformat='$,.0f',
            gridcolor='lightgray'
        ),
        height=600,
        showlegend=False,
        hovermode='x unified',
        plot_bgcolor='white'
    )
    
    # Add annotations for interpretation
    fig.add_annotation(
        text="Box: 25-75 percentile | Line: 10-90 percentile | Blue bar: Median | Red ◆: Mean",
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        font=dict(size=10)
    )
    
    return fig

def calculate_probability_metrics(results_dict):
    """Calculate probability-based metrics for decision making"""
    
    metrics = []
    
    for scenario, results in results_dict.items():
        npvs = results['npvs']
        rois = results['rois']
        paybacks = results['paybacks']
        
        metrics.append({
            'Scenario': scenario.replace('_', ' ').title(),
            'P(NPV > 0)': f"{(npvs > 0).mean() * 100:.1f}%",
            'P(ROI > 100%)': f"{(rois > 100).mean() * 100:.1f}%",
            'P(Payback < 6mo)': f"{(paybacks < 6).mean() * 100:.1f}%",
            'P(NPV > $1M)': f"{(npvs > 1_000_000).mean() * 100:.1f}%",
            'Expected NPV': f"${np.mean(npvs):,.0f}",
            'NPV Std Dev': f"${np.std(npvs):,.0f}",
            'Worst Case (P10)': f"${np.percentile(npvs, 10):,.0f}",
            'Best Case (P90)': f"${np.percentile(npvs, 90):,.0f}"
        })
    
    return pd.DataFrame(metrics)

if __name__ == "__main__":
    # Define scenarios to analyze
    scenarios_to_analyze = [
        'conservative_startup',
        'moderate_startup',
        'aggressive_startup',
        'conservative_enterprise',
        'moderate_enterprise',
        'aggressive_enterprise',
        'moderate_scaleup',
        'aggressive_scaleup'
    ]
    
    # Run Monte Carlo simulations
    results = {}
    for scenario in scenarios_to_analyze:
        results[scenario] = run_monte_carlo_scenario(scenario, n_simulations=1000)
    
    print("\n" + "="*80)
    print("MONTE CARLO ANALYSIS COMPLETE")
    print("="*80)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    
    # 1. Main Monte Carlo visualization
    mc_fig = create_monte_carlo_visualization(results)
    mc_fig.write_html("monte_carlo_analysis.html")
    mc_fig.show()
    
    # 2. Confidence bands visualization
    conf_fig = create_confidence_bands_visualization(results)
    conf_fig.write_html("confidence_bands.html")
    conf_fig.show()
    
    # 3. Probability metrics table
    prob_metrics = calculate_probability_metrics(results)
    print("\n" + "="*80)
    print("PROBABILITY-BASED DECISION METRICS")
    print("="*80)
    print(prob_metrics.to_string(index=False))
    
    # Save to CSV
    prob_metrics.to_csv("monte_carlo_metrics.csv", index=False)
    
    print("\n✅ Files created:")
    print("  - monte_carlo_analysis.html (distribution analysis)")
    print("  - confidence_bands.html (confidence intervals)")
    print("  - monte_carlo_metrics.csv (probability metrics)")
    
    # Key insights
    print("\n💡 KEY INSIGHTS FROM MONTE CARLO ANALYSIS:")
    
    # Find most reliable scenario (lowest std dev relative to mean)
    cv_scores = {}
    for scenario, res in results.items():
        mean_npv = np.mean(res['npvs'])
        std_npv = np.std(res['npvs'])
        cv = (std_npv / abs(mean_npv)) if mean_npv != 0 else float('inf')
        cv_scores[scenario] = cv
    
    most_reliable = min(cv_scores, key=cv_scores.get)
    print(f"  - Most reliable scenario: {most_reliable} (lowest coefficient of variation)")
    
    # Find highest expected value
    expected_values = {s: np.mean(r['npvs']) for s, r in results.items()}
    best_expected = max(expected_values, key=expected_values.get)
    print(f"  - Highest expected NPV: {best_expected} (${expected_values[best_expected]:,.0f})")
    
    # Find best risk-adjusted return (Sharpe-like ratio)
    sharpe_ratios = {}
    for scenario, res in results.items():
        mean_npv = np.mean(res['npvs'])
        std_npv = np.std(res['npvs'])
        sharpe = mean_npv / std_npv if std_npv > 0 else 0
        sharpe_ratios[scenario] = sharpe
    
    best_sharpe = max(sharpe_ratios, key=sharpe_ratios.get)
    print(f"  - Best risk-adjusted return: {best_sharpe} (highest Sharpe-like ratio)")
    
    print("\n📊 The Monte Carlo analysis shows uncertainty ranges and helps identify")
    print("   scenarios that are not just high-return but also reliable and lower-risk.")