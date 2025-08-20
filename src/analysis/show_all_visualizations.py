#!/usr/bin/env python3
"""
Show comprehensive visualizations of the AI impact model
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from main import AIImpactModel

def create_comprehensive_visualization():
    """Create a comprehensive dashboard showing all key insights"""
    
    # Initialize model and run scenarios
    model = AIImpactModel()
    
    # Define all 9 scenarios
    scenarios = []
    for company in ['startup', 'enterprise', 'scaleup']:
        for approach in ['conservative', 'moderate', 'aggressive']:
            scenarios.append(f"{approach}_{company}")
    
    # Run all scenarios
    print("Running all scenarios...")
    results = {}
    for scenario in scenarios:
        print(f"  {scenario}")
        results[scenario] = model.run_scenario(scenario)
    
    # Create comprehensive figure
    fig = make_subplots(
        rows=4, cols=3,
        subplot_titles=(
            'Adoption Curves - Startup', 'Adoption Curves - Enterprise', 'Adoption Curves - Scale-up',
            'NPV by Company Type', 'ROI by Company Type', 'Payback Period',
            'Monthly Costs - Startup', 'Monthly Costs - Enterprise', 'Monthly Costs - Scale-up',
            'Cumulative ROI - Best of Each', 'Value Breakdown Comparison', 'Adoption vs ROI Matrix'
        ),
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}],
            [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "bar"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.10,
        figure=go.Figure(layout=go.Layout(height=1400))
    )
    
    colors = {
        'conservative': '#2E86AB',
        'moderate': '#A23B72', 
        'aggressive': '#F18F01'
    }
    
    # Row 1: Adoption Curves by Company Type
    for col, company in enumerate(['startup', 'enterprise', 'scaleup'], 1):
        for approach in ['conservative', 'moderate', 'aggressive']:
            scenario = f"{approach}_{company}"
            if scenario in results:
                months = np.arange(len(results[scenario]['adoption']))
                
                # Show actual adoption (not effective adoption)
                adoption_pct = results[scenario]['adoption'] * 100
                
                fig.add_trace(
                    go.Scatter(
                        x=months,
                        y=adoption_pct,
                        mode='lines',
                        name=approach.capitalize(),
                        line=dict(color=colors[approach], width=2.5),
                        showlegend=(col==1),
                        hovertemplate=f"{approach}<br>Month: %{{x}}<br>Adoption: %{{y:.1f}}%<extra></extra>"
                    ),
                    row=1, col=col
                )
                
                # Add annotation for peak adoption
                peak_idx = np.argmax(adoption_pct)
                if approach == 'moderate':  # Only annotate moderate to avoid clutter
                    fig.add_annotation(
                        x=peak_idx,
                        y=adoption_pct[peak_idx],
                        text=f"{adoption_pct[peak_idx]:.0f}%",
                        showarrow=False,
                        row=1, col=col,
                        font=dict(size=10)
                    )
    
    # Row 2: Key Metrics Comparison
    # NPV by Company Type
    for approach in ['conservative', 'moderate', 'aggressive']:
        npvs = []
        companies = ['startup', 'enterprise', 'scaleup']
        for company in companies:
            scenario = f"{approach}_{company}"
            npvs.append(results[scenario]['npv'] if scenario in results else 0)
        
        fig.add_trace(
            go.Bar(
                x=['Startup', 'Enterprise', 'Scale-up'],
                y=npvs,
                name=approach.capitalize(),
                marker_color=colors[approach],
                showlegend=False,
                text=[f"${v/1e6:.1f}M" if v > 1e6 else f"${v/1e3:.0f}K" for v in npvs],
                textposition='outside'
            ),
            row=2, col=1
        )
    
    # ROI by Company Type
    for approach in ['conservative', 'moderate', 'aggressive']:
        rois = []
        for company in ['startup', 'enterprise', 'scaleup']:
            scenario = f"{approach}_{company}"
            rois.append(results[scenario]['roi_percent'] if scenario in results else 0)
        
        fig.add_trace(
            go.Bar(
                x=['Startup', 'Enterprise', 'Scale-up'],
                y=rois,
                name=approach.capitalize(),
                marker_color=colors[approach],
                showlegend=False,
                text=[f"{v:.0f}%" for v in rois],
                textposition='outside'
            ),
            row=2, col=2
        )
    
    # Payback Period
    for approach in ['conservative', 'moderate', 'aggressive']:
        paybacks = []
        for company in ['startup', 'enterprise', 'scaleup']:
            scenario = f"{approach}_{company}"
            pb = results[scenario].get('breakeven_month', None) if scenario in results else None
            paybacks.append(pb if pb else 0)
        
        fig.add_trace(
            go.Bar(
                x=['Startup', 'Enterprise', 'Scale-up'],
                y=paybacks,
                name=approach.capitalize(),
                marker_color=colors[approach],
                showlegend=False,
                text=[f"{v} mo" if v > 0 else "N/A" for v in paybacks],
                textposition='outside'
            ),
            row=2, col=3
        )
    
    # Row 3: Monthly Costs by Company Type
    for col, company in enumerate(['startup', 'enterprise', 'scaleup'], 1):
        for approach in ['conservative', 'moderate', 'aggressive']:
            scenario = f"{approach}_{company}"
            if scenario in results:
                months = np.arange(len(results[scenario]['costs']['total']))
                
                fig.add_trace(
                    go.Scatter(
                        x=months,
                        y=results[scenario]['costs']['total'],
                        mode='lines',
                        name=approach.capitalize(),
                        line=dict(color=colors[approach], width=2),
                        showlegend=False,
                        hovertemplate=f"{approach}<br>Month: %{{x}}<br>Cost: $%{{y:,.0f}}<extra></extra>"
                    ),
                    row=3, col=col
                )
    
    # Row 4: Special Analyses
    
    # Cumulative ROI for best scenarios
    best_scenarios = ['moderate_startup', 'moderate_enterprise', 'aggressive_scaleup']
    for scenario in best_scenarios:
        if scenario in results:
            months = np.arange(len(results[scenario]['cumulative_value']))
            net_value = results[scenario]['cumulative_value'] - results[scenario]['costs']['cumulative']
            
            company = scenario.split('_')[1]
            approach = scenario.split('_')[0]
            
            fig.add_trace(
                go.Scatter(
                    x=months,
                    y=net_value,
                    mode='lines',
                    name=scenario.replace('_', ' ').title(),
                    line=dict(width=2.5),
                    hovertemplate=f"{scenario}<br>Month: %{{x}}<br>Net Value: $%{{y:,.0f}}<extra></extra>"
                ),
                row=4, col=1
            )
    
    # Add breakeven line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=4, col=1)
    
    # Value Breakdown for moderate scenarios
    for company in ['startup', 'enterprise', 'scaleup']:
        scenario = f"moderate_{company}"
        if scenario in results:
            breakdown = results[scenario]['impact_breakdown']
            
            fig.add_trace(
                go.Bar(
                    x=['Time', 'Quality', 'Capacity', 'Strategic'],
                    y=[breakdown['time_value'], breakdown['quality_value'], 
                       breakdown['capacity_value'], breakdown['strategic_value']],
                    name=company.capitalize(),
                    showlegend=True
                ),
                row=4, col=2
            )
    
    # Adoption vs ROI scatter
    for scenario in scenarios:
        if scenario in results:
            peak_adoption = max(results[scenario]['adoption']) * 100
            roi = results[scenario]['roi_percent']
            approach = scenario.split('_')[0]
            company = scenario.split('_')[1]
            
            # Size based on NPV
            npv = results[scenario]['npv']
            size = 10 + (npv / 1e6) * 5  # Scale size by NPV in millions
            
            fig.add_trace(
                go.Scatter(
                    x=[peak_adoption],
                    y=[roi],
                    mode='markers+text',
                    name=scenario,
                    text=[f"{approach[0].upper()}{company[0].upper()}"],
                    textposition='middle center',
                    marker=dict(
                        size=size,
                        color=colors[approach],
                        line=dict(width=2, color='white')
                    ),
                    showlegend=False,
                    hovertemplate=f"{scenario}<br>Peak Adoption: %{{x:.1f}}%<br>ROI: %{{y:.0f}}%<br>NPV: ${npv:,.0f}<extra></extra>"
                ),
                row=4, col=3
            )
    
    # Update layouts
    fig.update_layout(
        title='AI Development Impact Model - Comprehensive Analysis<br><sub>Fixed Adoption Curves & Complete Scenario Matrix</sub>',
        height=1400,
        showlegend=True,
        barmode='group',
        legend=dict(x=0.01, y=0.99),
        font=dict(size=10)
    )
    
    # Update axes
    # Row 1 - Adoption
    for col in range(1, 4):
        fig.update_xaxes(title_text="Month", row=1, col=col)
        fig.update_yaxes(title_text="Adoption %", row=1, col=col, range=[0, 100])
    
    # Row 2 - Metrics
    fig.update_yaxes(title_text="NPV ($)", row=2, col=1, tickformat='$,.0f')
    fig.update_yaxes(title_text="ROI (%)", row=2, col=2)
    fig.update_yaxes(title_text="Months", row=2, col=3)
    
    # Row 3 - Costs
    for col in range(1, 4):
        fig.update_xaxes(title_text="Month", row=3, col=col)
        fig.update_yaxes(title_text="Monthly Cost ($)", row=3, col=col, tickformat='$,.0f')
    
    # Row 4 - Special
    fig.update_xaxes(title_text="Month", row=4, col=1)
    fig.update_yaxes(title_text="Cumulative Net Value ($)", row=4, col=1, tickformat='$,.0f')
    
    fig.update_yaxes(title_text="Annual Value ($)", row=4, col=2, tickformat='$,.0f')
    
    fig.update_xaxes(title_text="Peak Adoption (%)", row=4, col=3, range=[60, 100])
    fig.update_yaxes(title_text="ROI (%)", row=4, col=3, range=[0, 1000])
    
    return fig, results

def create_summary_metrics_table(results):
    """Create a summary table of key metrics"""
    
    print("\n" + "="*100)
    print("COMPREHENSIVE METRICS SUMMARY - ALL 9 SCENARIOS")
    print("="*100)
    
    # Headers
    headers = ['Scenario', 'Peak Adopt%', 'Month 12%', 'Final%', 'NPV', 'ROI%', 'Payback', 'Val/Dev/Yr']
    
    # Prepare data
    rows = []
    for scenario in sorted(results.keys()):
        r = results[scenario]
        row = [
            scenario.replace('_', ' ').title(),
            f"{max(r['adoption'])*100:.1f}",
            f"{r['adoption'][11]*100:.1f}",
            f"{r['adoption'][-1]*100:.1f}",
            f"${r['npv']/1e6:.2f}M" if r['npv'] > 1e6 else f"${r['npv']/1e3:.0f}K",
            f"{r['roi_percent']:.0f}",
            f"{r['breakeven_month']}" if r['breakeven_month'] else "N/A",
            f"${r['annual_value_per_dev']/1e3:.0f}K"
        ]
        rows.append(row)
    
    # Print table
    col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
    
    # Print header
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))
    
    # Print rows
    for row in rows:
        print(" | ".join(str(v).ljust(w) for v, w in zip(row, col_widths)))
    
    print("\n" + "="*100)
    
    # Key insights
    print("\n🔍 KEY INSIGHTS:")
    
    # Best overall NPV
    best_npv = max(results.items(), key=lambda x: x[1]['npv'])
    print(f"  ✅ Highest NPV: {best_npv[0]} (${best_npv[1]['npv']/1e6:.2f}M)")
    
    # Best ROI
    best_roi = max(results.items(), key=lambda x: x[1]['roi_percent'])
    print(f"  📈 Highest ROI: {best_roi[0]} ({best_roi[1]['roi_percent']:.0f}%)")
    
    # Fastest payback
    valid_paybacks = [(k, v['breakeven_month']) for k, v in results.items() if v['breakeven_month']]
    if valid_paybacks:
        fastest = min(valid_paybacks, key=lambda x: x[1])
        print(f"  ⚡ Fastest Payback: {fastest[0]} ({fastest[1]} months)")
    
    # Highest sustained adoption
    best_sustained = max(results.items(), key=lambda x: x[1]['adoption'][-1])
    print(f"  🎯 Best Sustained Adoption: {best_sustained[0]} ({best_sustained[1]['adoption'][-1]*100:.1f}% at end)")
    
    print("\n" + "="*100)

if __name__ == "__main__":
    print("\nGenerating comprehensive visualization...")
    
    # Create and show the visualization
    fig, results = create_comprehensive_visualization()
    
    # Save and display
    fig.write_html("comprehensive_analysis.html")
    fig.show()
    
    # Print summary metrics
    create_summary_metrics_table(results)
    
    print("\n✅ Visualization saved to: comprehensive_analysis.html")
    print("\n📊 The dashboard shows:")
    print("  - Fixed adoption curves maintaining 60-95% peak adoption")
    print("  - All 9 scenario combinations (3x3 matrix)")
    print("  - NPV, ROI, and payback comparisons")
    print("  - Monthly cost evolution")
    print("  - Value breakdown by category")
    print("  - Adoption vs ROI relationship (bubble size = NPV)")