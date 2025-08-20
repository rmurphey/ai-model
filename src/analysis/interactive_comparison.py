#!/usr/bin/env python3
"""
Create an interactive comparison tool for exploring scenarios
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from main import AIImpactModel

def create_interactive_comparison():
    """Create an interactive dashboard for comparing selected scenarios"""
    
    # Run all scenarios first
    model = AIImpactModel()
    
    company_types = ['startup', 'enterprise', 'scaleup']
    adoption_approaches = ['conservative', 'moderate', 'aggressive']
    
    all_scenarios = []
    all_results = {}
    
    print("Running all scenarios...")
    for company in company_types:
        for approach in adoption_approaches:
            scenario_name = f"{approach}_{company}"
            all_scenarios.append(scenario_name)
            print(f"  {scenario_name}...")
            all_results[scenario_name] = model.run_scenario(scenario_name)
    
    # Create figure with dropdowns
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'ROI Timeline Comparison',
            'Monthly Cost Comparison', 
            'Adoption Curves',
            'Value Breakdown'
        ),
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "bar"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    # Color palette
    colors = px.colors.qualitative.Set2
    
    # Create traces for all scenarios (initially hidden)
    for i, scenario in enumerate(all_scenarios):
        color = colors[i % len(colors)]
        results = all_results[scenario]
        months = np.arange(len(results['costs']['total']))
        
        # ROI Timeline (top-left)
        cumulative_value = results['cumulative_value']
        cumulative_costs = results['costs']['cumulative']
        net_value = cumulative_value - cumulative_costs
        
        fig.add_trace(
            go.Scatter(
                x=months,
                y=net_value,
                mode='lines',
                name=scenario,
                line=dict(color=color, width=2),
                visible=False,
                legendgroup=scenario
            ),
            row=1, col=1
        )
        
        # Monthly Costs (top-right)
        fig.add_trace(
            go.Scatter(
                x=months,
                y=results['costs']['total'],
                mode='lines',
                name=scenario,
                line=dict(color=color, width=2),
                visible=False,
                showlegend=False,
                legendgroup=scenario
            ),
            row=1, col=2
        )
        
        # Adoption Curves (bottom-left)
        fig.add_trace(
            go.Scatter(
                x=months,
                y=results['adoption'] * 100,
                mode='lines',
                name=scenario,
                line=dict(color=color, width=2),
                visible=False,
                showlegend=False,
                legendgroup=scenario
            ),
            row=2, col=1
        )
        
        # Value Breakdown (bottom-right)
        fig.add_trace(
            go.Bar(
                x=['Time', 'Quality', 'Capacity', 'Strategic'],
                y=[
                    results['impact_breakdown']['time_value'],
                    results['impact_breakdown']['quality_value'],
                    results['impact_breakdown']['capacity_value'],
                    results['impact_breakdown']['strategic_value']
                ],
                name=scenario,
                marker_color=color,
                visible=False,
                showlegend=False,
                legendgroup=scenario
            ),
            row=2, col=2
        )
    
    # Make first 3 scenarios visible by default
    default_scenarios = ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']
    for i, scenario in enumerate(all_scenarios):
        if scenario in default_scenarios:
            for j in range(4):  # 4 traces per scenario
                fig.data[i*4 + j].visible = True
    
    # Create dropdown buttons for scenario selection
    buttons = []
    
    # Add preset comparisons
    preset_comparisons = [
        {
            'label': 'Startup Comparison',
            'scenarios': ['conservative_startup', 'moderate_startup', 'aggressive_startup']
        },
        {
            'label': 'Enterprise Comparison',
            'scenarios': ['conservative_enterprise', 'moderate_enterprise', 'aggressive_enterprise']
        },
        {
            'label': 'Scale-up Comparison',
            'scenarios': ['conservative_scaleup', 'moderate_scaleup', 'aggressive_scaleup']
        },
        {
            'label': 'Conservative Across Companies',
            'scenarios': ['conservative_startup', 'conservative_enterprise', 'conservative_scaleup']
        },
        {
            'label': 'Moderate Across Companies',
            'scenarios': ['moderate_startup', 'moderate_enterprise', 'moderate_scaleup']
        },
        {
            'label': 'Aggressive Across Companies',
            'scenarios': ['aggressive_startup', 'aggressive_enterprise', 'aggressive_scaleup']
        },
        {
            'label': 'Best of Each Type',
            'scenarios': ['aggressive_startup', 'aggressive_enterprise', 'moderate_scaleup']
        }
    ]
    
    for preset in preset_comparisons:
        visibility = []
        for scenario in all_scenarios:
            is_visible = scenario in preset['scenarios']
            for _ in range(4):  # 4 traces per scenario
                visibility.append(is_visible)
        
        buttons.append(dict(
            label=preset['label'],
            method='update',
            args=[{'visible': visibility}]
        ))
    
    # Update layout with dropdown
    fig.update_layout(
        title='Interactive Scenario Comparison Tool',
        height=800,
        showlegend=True,
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.15,
                yanchor="top"
            )
        ],
        annotations=[
            dict(
                text="Select Comparison:",
                showarrow=False,
                x=0.01,
                xref="paper",
                y=1.18,
                yref="paper",
                align="left"
            )
        ]
    )
    
    # Update axes
    fig.update_yaxes(title_text="Net Value ($)", row=1, col=1, tickformat='$,.0f')
    fig.update_yaxes(title_text="Monthly Cost ($)", row=1, col=2, tickformat='$,.0f')
    fig.update_yaxes(title_text="Adoption (%)", row=2, col=1)
    fig.update_yaxes(title_text="Annual Value ($)", row=2, col=2, tickformat='$,.0f')
    
    fig.update_xaxes(title_text="Month", row=1, col=1)
    fig.update_xaxes(title_text="Month", row=1, col=2)
    fig.update_xaxes(title_text="Month", row=2, col=1)
    fig.update_xaxes(title_text="Value Component", row=2, col=2)
    
    # Add horizontal line at y=0 for ROI timeline
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    return fig, all_results

def create_summary_table(results):
    """Create a summary table for all scenarios"""
    
    data = []
    for scenario, r in results.items():
        data.append({
            'Scenario': scenario.replace('_', ' ').title(),
            'Team Size': r['baseline'].team_size,
            'NPV': f"${r['npv']:,.0f}",
            'ROI %': f"{r['roi_percent']:.1f}%",
            'Payback (mo)': r['breakeven_month'] or 'Never',
            'Peak Adoption': f"{r['peak_adoption']*100:.1f}%",
            'Cost/Dev/Year': f"${r['annual_cost_per_dev']:,.0f}",
            'Value/Dev/Year': f"${r['annual_value_per_dev']:,.0f}"
        })
    
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    print("\nCreating interactive comparison dashboard...")
    
    # Create interactive figure
    fig, results = create_interactive_comparison()
    
    # Save and show
    fig.write_html("interactive_comparison.html")
    fig.show()
    
    print("\nCreating summary table...")
    summary_df = create_summary_table(results)
    
    print("\n" + "="*100)
    print("ALL SCENARIOS SUMMARY")
    print("="*100)
    print(summary_df.to_string(index=False))
    
    # Save summary to CSV
    summary_df.to_csv("scenario_summary.csv", index=False)
    
    print("\n✅ Files created:")
    print("  - interactive_comparison.html (interactive dashboard)")
    print("  - scenario_summary.csv (data export)")
    
    print("\n💡 Use the dropdown menu in the dashboard to compare different scenario groups!")