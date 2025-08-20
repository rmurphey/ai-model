#!/usr/bin/env python3
"""
Create a comprehensive comparison visualization of all scenarios
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from main import AIImpactModel

def create_comprehensive_comparison():
    """Create a comprehensive comparison dashboard"""
    
    # Initialize model and run scenarios
    model = AIImpactModel()
    scenarios = ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']
    
    for scenario in scenarios:
        model.run_scenario(scenario)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=(
            'NPV Comparison', 'ROI Comparison', 'Adoption Curves',
            'Monthly Costs', 'Cumulative Value', 'Value per Developer'
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}, {"type": "bar"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    colors = {
        'conservative_startup': '#2E86AB',
        'moderate_enterprise': '#A23B72',
        'aggressive_scaleup': '#F18F01'
    }
    
    # 1. NPV Comparison
    npvs = [model.results[s]['npv'] for s in scenarios]
    fig.add_trace(
        go.Bar(x=scenarios, y=npvs, marker_color=list(colors.values()), name='NPV'),
        row=1, col=1
    )
    
    # 2. ROI Comparison
    rois = [model.results[s]['roi_percent'] for s in scenarios]
    fig.add_trace(
        go.Bar(x=scenarios, y=rois, marker_color=list(colors.values()), name='ROI %'),
        row=1, col=2
    )
    
    # 3. Adoption Curves
    for scenario in scenarios:
        months = np.arange(len(model.results[scenario]['adoption']))
        fig.add_trace(
            go.Scatter(
                x=months,
                y=model.results[scenario]['adoption'] * 100,
                mode='lines',
                name=scenario.replace('_', ' ').title(),
                line=dict(color=colors[scenario], width=2)
            ),
            row=1, col=3
        )
    
    # 4. Monthly Costs
    for scenario in scenarios:
        months = np.arange(len(model.results[scenario]['costs']['total']))
        fig.add_trace(
            go.Scatter(
                x=months,
                y=model.results[scenario]['costs']['total'],
                mode='lines',
                name=scenario.replace('_', ' ').title(),
                line=dict(color=colors[scenario], width=2)
            ),
            row=2, col=1
        )
    
    # 5. Cumulative Value
    for scenario in scenarios:
        months = np.arange(len(model.results[scenario]['cumulative_value']))
        fig.add_trace(
            go.Scatter(
                x=months,
                y=model.results[scenario]['cumulative_value'],
                mode='lines',
                name=scenario.replace('_', ' ').title(),
                line=dict(color=colors[scenario], width=2)
            ),
            row=2, col=2
        )
    
    # 6. Value per Developer
    value_per_dev = [model.results[s]['annual_value_per_dev'] for s in scenarios]
    fig.add_trace(
        go.Bar(x=scenarios, y=value_per_dev, marker_color=list(colors.values()), name='Value/Dev'),
        row=2, col=3
    )
    
    # Update layout
    fig.update_layout(
        title='AI Development Impact Model - Scenario Comparison',
        height=800,
        showlegend=True,
        plot_bgcolor='white'
    )
    
    # Update axes
    fig.update_xaxes(gridcolor='lightgray')
    fig.update_yaxes(gridcolor='lightgray')
    
    # Format specific axes
    fig.update_yaxes(title_text="NPV ($)", row=1, col=1, tickformat='$,.0f')
    fig.update_yaxes(title_text="ROI (%)", row=1, col=2)
    fig.update_yaxes(title_text="Adoption (%)", row=1, col=3)
    fig.update_xaxes(title_text="Month", row=1, col=3)
    
    fig.update_yaxes(title_text="Monthly Cost ($)", row=2, col=1, tickformat='$,.0f')
    fig.update_xaxes(title_text="Month", row=2, col=1)
    
    fig.update_yaxes(title_text="Cumulative Value ($)", row=2, col=2, tickformat='$,.0f')
    fig.update_xaxes(title_text="Month", row=2, col=2)
    
    fig.update_yaxes(title_text="Annual Value ($)", row=2, col=3, tickformat='$,.0f')
    
    return fig

def create_value_breakdown_comparison():
    """Create value breakdown comparison across scenarios"""
    
    model = AIImpactModel()
    scenarios = ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']
    
    for scenario in scenarios:
        model.run_scenario(scenario)
    
    # Create grouped bar chart
    categories = ['Time Value', 'Quality Value', 'Capacity Value', 'Strategic Value']
    
    fig = go.Figure()
    
    for scenario in scenarios:
        values = [
            model.results[scenario]['impact_breakdown']['time_value'],
            model.results[scenario]['impact_breakdown']['quality_value'],
            model.results[scenario]['impact_breakdown']['capacity_value'],
            model.results[scenario]['impact_breakdown']['strategic_value']
        ]
        
        fig.add_trace(go.Bar(
            name=scenario.replace('_', ' ').title(),
            x=categories,
            y=values
        ))
    
    fig.update_layout(
        title='Value Creation Breakdown by Scenario',
        xaxis_title='Value Category',
        yaxis_title='Annual Value ($)',
        barmode='group',
        height=500,
        yaxis=dict(tickformat='$,.0f'),
        plot_bgcolor='white'
    )
    
    return fig

if __name__ == "__main__":
    print("Creating comprehensive comparison chart...")
    comparison_fig = create_comprehensive_comparison()
    comparison_fig.show()
    comparison_fig.write_html("scenario_comparison.html")
    print("Saved to scenario_comparison.html")
    
    print("\nCreating value breakdown comparison...")
    value_fig = create_value_breakdown_comparison()
    value_fig.show()
    value_fig.write_html("value_breakdown.html")
    print("Saved to value_breakdown.html")
    
    print("\nVisualization complete!")