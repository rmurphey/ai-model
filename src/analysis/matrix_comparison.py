#!/usr/bin/env python3
"""
Create comprehensive matrix comparison of all 9 scenarios
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from main import AIImpactModel

def run_all_scenarios():
    """Run all 9 scenario combinations and return results"""
    
    model = AIImpactModel()
    
    # Define the matrix
    company_types = ['startup', 'enterprise', 'scaleup']
    adoption_approaches = ['conservative', 'moderate', 'aggressive']
    
    results = {}
    
    print("Running all 9 scenarios...")
    for company in company_types:
        for approach in adoption_approaches:
            scenario_name = f"{approach}_{company}"
            print(f"  Running {scenario_name}...")
            try:
                result = model.run_scenario(scenario_name)
                results[scenario_name] = result
            except Exception as e:
                print(f"    Error: {e}")
    
    return results, company_types, adoption_approaches

def create_heatmap_matrix(results, company_types, adoption_approaches, metric='npv'):
    """Create a heatmap showing a metric across all scenarios"""
    
    # Create matrix data
    matrix_data = []
    for company in company_types:
        row = []
        for approach in adoption_approaches:
            scenario_name = f"{approach}_{company}"
            if scenario_name in results:
                if metric == 'npv':
                    value = results[scenario_name]['npv']
                elif metric == 'roi':
                    value = results[scenario_name]['roi_percent']
                elif metric == 'payback':
                    value = results[scenario_name]['breakeven_month'] or 999
                elif metric == 'value_per_dev':
                    value = results[scenario_name]['annual_value_per_dev']
                else:
                    value = 0
            else:
                value = 0
            row.append(value)
        matrix_data.append(row)
    
    # Create labels
    company_labels = ['Startup\n(10 devs)', 'Enterprise\n(50 devs)', 'Scale-up\n(25 devs)']
    approach_labels = ['Conservative', 'Moderate', 'Aggressive']
    
    # Create heatmap
    if metric == 'npv':
        title = 'Net Present Value (NPV) Matrix'
        colorscale = 'RdYlGn'
        text_format = '$,.0f'
    elif metric == 'roi':
        title = 'Return on Investment (%) Matrix'
        colorscale = 'RdYlGn'
        text_format = '.1f%'
    elif metric == 'payback':
        title = 'Payback Period (Months) Matrix'
        colorscale = 'RdYlGn_r'  # Reversed - lower is better
        text_format = '.0f'
    else:
        title = 'Annual Value per Developer Matrix'
        colorscale = 'RdYlGn'
        text_format = '$,.0f'
    
    # Format text annotations
    text_values = []
    for row in matrix_data:
        text_row = []
        for val in row:
            if metric == 'roi':
                text_row.append(f"{val:.1f}%")
            elif metric == 'payback':
                if val == 999:
                    text_row.append("Never")
                else:
                    text_row.append(f"{val:.0f} mo")
            else:
                text_row.append(f"${val:,.0f}")
        text_values.append(text_row)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix_data,
        x=approach_labels,
        y=company_labels,
        text=text_values,
        texttemplate="%{text}",
        textfont={"size": 14},
        colorscale=colorscale,
        showscale=True,
        colorbar=dict(title=metric.upper())
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Adoption Approach",
        yaxis_title="Company Type",
        height=500,
        font=dict(size=12)
    )
    
    return fig

def create_comprehensive_dashboard(results, company_types, adoption_approaches):
    """Create a comprehensive dashboard with multiple views"""
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=3,
        subplot_titles=(
            'NPV by Company Type', 'ROI by Company Type', 'Payback by Company Type',
            'NPV by Adoption Approach', 'ROI by Adoption Approach', 'Value/Dev by Adoption',
            'Adoption Curves - Startup', 'Adoption Curves - Enterprise', 'Adoption Curves - Scale-up'
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.10
    )
    
    colors = {
        'conservative': '#2E86AB',
        'moderate': '#A23B72',
        'aggressive': '#F18F01'
    }
    
    # Row 1: Metrics by Company Type
    for col, metric in enumerate(['npv', 'roi_percent', 'breakeven_month'], 1):
        for approach in adoption_approaches:
            values = []
            for company in company_types:
                scenario = f"{approach}_{company}"
                if scenario in results:
                    val = results[scenario].get(metric, 0)
                    if metric == 'breakeven_month' and val is None:
                        val = 0
                    values.append(val)
                else:
                    values.append(0)
            
            fig.add_trace(
                go.Bar(
                    x=company_types,
                    y=values,
                    name=approach.capitalize(),
                    marker_color=colors[approach],
                    showlegend=(col==1)
                ),
                row=1, col=col
            )
    
    # Row 2: Metrics by Adoption Approach
    for col, metric in enumerate(['npv', 'roi_percent', 'annual_value_per_dev'], 1):
        for company in company_types:
            values = []
            for approach in adoption_approaches:
                scenario = f"{approach}_{company}"
                if scenario in results:
                    values.append(results[scenario].get(metric, 0))
                else:
                    values.append(0)
            
            fig.add_trace(
                go.Bar(
                    x=adoption_approaches,
                    y=values,
                    name=company.capitalize(),
                    showlegend=(col==1 and company=='startup')
                ),
                row=2, col=col
            )
    
    # Row 3: Adoption Curves by Company Type
    for col, company in enumerate(company_types, 1):
        for approach in adoption_approaches:
            scenario = f"{approach}_{company}"
            if scenario in results:
                months = np.arange(len(results[scenario]['adoption']))
                fig.add_trace(
                    go.Scatter(
                        x=months,
                        y=results[scenario]['adoption'] * 100,
                        mode='lines',
                        name=approach.capitalize(),
                        line=dict(color=colors[approach], width=2),
                        showlegend=False
                    ),
                    row=3, col=col
                )
    
    # Update layout
    fig.update_layout(
        title='AI Development Impact - 3x3 Scenario Matrix Analysis',
        height=1000,
        showlegend=True,
        barmode='group'
    )
    
    # Update axes
    fig.update_yaxes(title_text="NPV ($)", row=1, col=1, tickformat='$,.0f')
    fig.update_yaxes(title_text="ROI (%)", row=1, col=2)
    fig.update_yaxes(title_text="Months", row=1, col=3)
    
    fig.update_yaxes(title_text="NPV ($)", row=2, col=1, tickformat='$,.0f')
    fig.update_yaxes(title_text="ROI (%)", row=2, col=2)
    fig.update_yaxes(title_text="Value/Dev ($)", row=2, col=3, tickformat='$,.0f')
    
    fig.update_yaxes(title_text="Adoption (%)", row=3, col=1)
    fig.update_yaxes(title_text="Adoption (%)", row=3, col=2)
    fig.update_yaxes(title_text="Adoption (%)", row=3, col=3)
    fig.update_xaxes(title_text="Month", row=3, col=1)
    fig.update_xaxes(title_text="Month", row=3, col=2)
    fig.update_xaxes(title_text="Month", row=3, col=3)
    
    return fig

def create_insights_summary(results, company_types, adoption_approaches):
    """Generate insights from the matrix analysis"""
    
    insights = {
        'best_overall': None,
        'best_by_company': {},
        'best_by_approach': {},
        'highest_roi': None,
        'fastest_payback': None,
        'highest_value_per_dev': None
    }
    
    best_npv = float('-inf')
    best_roi = float('-inf')
    fastest_payback = float('inf')
    best_value_per_dev = float('-inf')
    
    # Analyze all scenarios
    for company in company_types:
        company_best_npv = float('-inf')
        company_best_scenario = None
        
        for approach in adoption_approaches:
            scenario = f"{approach}_{company}"
            if scenario in results:
                r = results[scenario]
                
                # Overall best NPV
                if r['npv'] > best_npv:
                    best_npv = r['npv']
                    insights['best_overall'] = scenario
                
                # Best for this company type
                if r['npv'] > company_best_npv:
                    company_best_npv = r['npv']
                    company_best_scenario = scenario
                
                # Highest ROI
                if r['roi_percent'] > best_roi:
                    best_roi = r['roi_percent']
                    insights['highest_roi'] = (scenario, r['roi_percent'])
                
                # Fastest payback
                if r['breakeven_month'] and r['breakeven_month'] < fastest_payback:
                    fastest_payback = r['breakeven_month']
                    insights['fastest_payback'] = (scenario, r['breakeven_month'])
                
                # Highest value per developer
                if r['annual_value_per_dev'] > best_value_per_dev:
                    best_value_per_dev = r['annual_value_per_dev']
                    insights['highest_value_per_dev'] = (scenario, r['annual_value_per_dev'])
        
        insights['best_by_company'][company] = company_best_scenario
    
    # Best approach for each adoption strategy
    for approach in adoption_approaches:
        approach_best_npv = float('-inf')
        approach_best_scenario = None
        
        for company in company_types:
            scenario = f"{approach}_{company}"
            if scenario in results and results[scenario]['npv'] > approach_best_npv:
                approach_best_npv = results[scenario]['npv']
                approach_best_scenario = scenario
        
        insights['best_by_approach'][approach] = approach_best_scenario
    
    return insights

def print_insights(insights, results):
    """Print insights in a readable format"""
    
    print("\n" + "="*80)
    print("KEY INSIGHTS FROM 3x3 SCENARIO MATRIX")
    print("="*80)
    
    print(f"\n🏆 BEST OVERALL SCENARIO: {insights['best_overall']}")
    if insights['best_overall'] in results:
        r = results[insights['best_overall']]
        print(f"   NPV: ${r['npv']:,.0f}")
        print(f"   ROI: {r['roi_percent']:.1f}%")
        print(f"   Payback: Month {r['breakeven_month']}")
    
    print("\n📊 BEST SCENARIO BY COMPANY TYPE:")
    for company, scenario in insights['best_by_company'].items():
        if scenario in results:
            r = results[scenario]
            print(f"   {company.capitalize()}: {scenario} (NPV: ${r['npv']:,.0f})")
    
    print("\n🎯 BEST COMPANY FOR EACH APPROACH:")
    for approach, scenario in insights['best_by_approach'].items():
        if scenario in results:
            r = results[scenario]
            company = scenario.replace(f"{approach}_", "")
            print(f"   {approach.capitalize()}: {company} (NPV: ${r['npv']:,.0f})")
    
    print("\n🚀 RECORD HOLDERS:")
    if insights['highest_roi']:
        scenario, roi = insights['highest_roi']
        print(f"   Highest ROI: {scenario} ({roi:.1f}%)")
    
    if insights['fastest_payback']:
        scenario, months = insights['fastest_payback']
        print(f"   Fastest Payback: {scenario} ({months} months)")
    
    if insights['highest_value_per_dev']:
        scenario, value = insights['highest_value_per_dev']
        print(f"   Highest Value/Dev: {scenario} (${value:,.0f}/year)")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    # Run all scenarios
    results, company_types, adoption_approaches = run_all_scenarios()
    
    # Create visualizations
    print("\nCreating visualizations...")
    
    # 1. NPV Heatmap
    npv_heatmap = create_heatmap_matrix(results, company_types, adoption_approaches, 'npv')
    npv_heatmap.write_html("matrix_npv.html")
    npv_heatmap.show()
    
    # 2. ROI Heatmap
    roi_heatmap = create_heatmap_matrix(results, company_types, adoption_approaches, 'roi')
    roi_heatmap.write_html("matrix_roi.html")
    
    # 3. Comprehensive Dashboard
    dashboard = create_comprehensive_dashboard(results, company_types, adoption_approaches)
    dashboard.write_html("matrix_dashboard.html")
    dashboard.show()
    
    # 4. Generate and print insights
    insights = create_insights_summary(results, company_types, adoption_approaches)
    print_insights(insights, results)
    
    print("\nVisualizations saved:")
    print("  - matrix_npv.html")
    print("  - matrix_roi.html")
    print("  - matrix_dashboard.html")