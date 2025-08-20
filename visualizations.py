"""
Visualization module for AI development impact model.
Creates executive-ready charts and dashboards.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
from typing import Dict, List, Tuple, Optional

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class ModelVisualizer:
    """Create visualizations for model outputs"""
    
    def __init__(self, figsize=(12, 8)):
        self.figsize = figsize
        self.colors = {
            'adoption': '#2E86AB',
            'cost': '#E63946',
            'value': '#06D6A0',
            'roi': '#7209B7',
            'baseline': '#A8DADC'
        }
    
    def plot_adoption_curve(self, adoption_data: np.ndarray, efficiency_data: np.ndarray = None) -> go.Figure:
        """Plot adoption and efficiency curves"""
        
        months = np.arange(len(adoption_data))
        
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=("AI Tool Adoption Over Time",),
            specs=[[{"secondary_y": True}]]
        )
        
        # Adoption curve
        fig.add_trace(
            go.Scatter(
                x=months,
                y=adoption_data * 100,
                mode='lines',
                name='Adoption Rate',
                line=dict(color=self.colors['adoption'], width=3),
                fill='tonexty',
                fillcolor='rgba(46, 134, 171, 0.2)'
            ),
            secondary_y=False
        )
        
        # Efficiency curve if provided
        if efficiency_data is not None:
            fig.add_trace(
                go.Scatter(
                    x=months,
                    y=efficiency_data * 100,
                    mode='lines',
                    name='User Efficiency',
                    line=dict(color=self.colors['value'], width=2, dash='dash')
                ),
                secondary_y=True
            )
        
        fig.update_xaxes(title_text="Month", gridcolor='lightgray')
        fig.update_yaxes(title_text="Adoption (%)", secondary_y=False, gridcolor='lightgray')
        fig.update_yaxes(title_text="Efficiency (%)", secondary_y=True)
        
        fig.update_layout(
            height=500,
            hovermode='x unified',
            legend=dict(x=0.02, y=0.98),
            plot_bgcolor='white'
        )
        
        return fig
    
    def plot_cost_breakdown(self, cost_data: Dict[str, np.ndarray]) -> go.Figure:
        """Create stacked area chart of costs over time"""
        
        months = np.arange(len(cost_data['total']))
        
        fig = go.Figure()
        
        # Define cost categories and colors
        categories = ['licensing', 'tokens', 'training', 'hidden', 'infrastructure', 'admin']
        colors = px.colors.qualitative.Set2
        
        # Create stacked area chart
        for i, category in enumerate(categories):
            if category in cost_data:
                fig.add_trace(go.Scatter(
                    x=months,
                    y=cost_data[category],
                    mode='lines',
                    name=category.capitalize(),
                    stackgroup='costs',
                    fillcolor=colors[i % len(colors)],
                    line=dict(width=0.5, color=colors[i % len(colors)])
                ))
        
        # Add total cost line
        fig.add_trace(go.Scatter(
            x=months,
            y=cost_data['total'],
            mode='lines',
            name='Total',
            line=dict(color='black', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Monthly Cost Breakdown",
            xaxis_title="Month",
            yaxis_title="Cost ($)",
            height=500,
            hovermode='x unified',
            yaxis=dict(tickformat='$,.0f'),
            plot_bgcolor='white'
        )
        
        return fig
    
    def plot_roi_timeline(self, costs: np.ndarray, value: np.ndarray, breakeven_month: Optional[int] = None) -> go.Figure:
        """Plot ROI timeline with breakeven point"""
        
        months = np.arange(len(costs))
        cumulative_costs = np.cumsum(costs)
        cumulative_value = np.cumsum(value)
        net_value = cumulative_value - cumulative_costs
        
        fig = go.Figure()
        
        # Cumulative costs
        fig.add_trace(go.Scatter(
            x=months,
            y=cumulative_costs,
            mode='lines',
            name='Cumulative Costs',
            line=dict(color=self.colors['cost'], width=3),
            fill='tonexty',
            fillcolor='rgba(230, 57, 70, 0.1)'
        ))
        
        # Cumulative value
        fig.add_trace(go.Scatter(
            x=months,
            y=cumulative_value,
            mode='lines',
            name='Cumulative Value',
            line=dict(color=self.colors['value'], width=3),
            fill='tonexty',
            fillcolor='rgba(6, 214, 160, 0.1)'
        ))
        
        # Net value
        fig.add_trace(go.Scatter(
            x=months,
            y=net_value,
            mode='lines',
            name='Net Value',
            line=dict(color=self.colors['roi'], width=2)
        ))
        
        # Add breakeven line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Breakeven")
        
        # Mark breakeven point
        if breakeven_month is not None and breakeven_month < len(months):
            fig.add_vline(
                x=breakeven_month,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Breakeven: Month {breakeven_month}"
            )
        
        fig.update_layout(
            title="ROI Timeline",
            xaxis_title="Month",
            yaxis_title="Value ($)",
            height=500,
            hovermode='x unified',
            yaxis=dict(tickformat='$,.0f'),
            plot_bgcolor='white',
            legend=dict(x=0.02, y=0.98)
        )
        
        return fig
    
    def plot_value_components(self, impact_data: Dict[str, float]) -> go.Figure:
        """Create waterfall chart of value components"""
        
        fig = go.Figure(go.Waterfall(
            name="Value Components",
            orientation="v",
            x=["Time Value", "Quality Value", "Capacity Value", "Strategic Value", "Total"],
            y=[
                impact_data.get('time_value', 0),
                impact_data.get('quality_value', 0),
                impact_data.get('capacity_value', 0),
                impact_data.get('strategic_value', 0),
                None  # Total will be calculated
            ],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": self.colors['value']}},
            totals={"marker": {"color": self.colors['roi']}}
        ))
        
        fig.update_layout(
            title="Annual Value Creation Breakdown",
            yaxis_title="Annual Value ($)",
            height=500,
            yaxis=dict(tickformat='$,.0f'),
            plot_bgcolor='white'
        )
        
        return fig
    
    def plot_sensitivity_tornado(self, sensitivity_results: Dict[str, Tuple[float, float]], base_value: float) -> go.Figure:
        """Create tornado chart for sensitivity analysis"""
        
        parameters = list(sensitivity_results.keys())
        low_values = [base_value - v[0] for v in sensitivity_results.values()]
        high_values = [v[1] - base_value for v in sensitivity_results.values()]
        
        fig = go.Figure()
        
        # Low scenario (negative direction)
        fig.add_trace(go.Bar(
            y=parameters,
            x=[-v for v in low_values],
            orientation='h',
            name='Downside',
            marker_color=self.colors['cost']
        ))
        
        # High scenario (positive direction)
        fig.add_trace(go.Bar(
            y=parameters,
            x=high_values,
            orientation='h',
            name='Upside',
            marker_color=self.colors['value']
        ))
        
        fig.update_layout(
            title="Sensitivity Analysis - Impact on NPV",
            xaxis_title="Change in NPV ($)",
            barmode='relative',
            height=500,
            xaxis=dict(tickformat='$,.0f'),
            plot_bgcolor='white'
        )
        
        return fig
    
    def plot_scenario_comparison(self, scenarios: Dict[str, Dict]) -> go.Figure:
        """Compare multiple scenarios side by side"""
        
        scenario_names = list(scenarios.keys())
        metrics = ['NPV', 'Payback (months)', 'Peak Adoption (%)', 'Annual ROI (%)']
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=metrics,
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        for i, metric in enumerate(metrics, 1):
            row = (i - 1) // 2 + 1
            col = (i - 1) % 2 + 1
            
            values = [scenarios[s].get(metric.lower().replace(' ', '_').replace('(%)', '').replace('(months)', ''), 0) 
                     for s in scenario_names]
            
            fig.add_trace(
                go.Bar(x=scenario_names, y=values, name=metric, showlegend=False),
                row=row, col=col
            )
        
        fig.update_layout(height=600, title_text="Scenario Comparison", plot_bgcolor='white')
        return fig
    
    def create_executive_dashboard(self, model_results: Dict) -> go.Figure:
        """Create comprehensive executive dashboard"""
        
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Adoption & Efficiency", "Monthly Costs",
                "Cumulative ROI", "Value Components",
                "Cost per Developer", "Risk Scenarios"
            ),
            specs=[
                [{"secondary_y": True}, {}],
                [{}, {"type": "pie"}],
                [{}, {}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.15
        )
        
        months = np.arange(len(model_results['adoption']))
        
        # 1. Adoption curve
        fig.add_trace(
            go.Scatter(x=months, y=model_results['adoption'] * 100, name='Adoption %',
                      line=dict(color=self.colors['adoption'], width=2)),
            row=1, col=1, secondary_y=False
        )
        
        if 'efficiency' in model_results:
            fig.add_trace(
                go.Scatter(x=months, y=model_results['efficiency'] * 100, name='Efficiency %',
                          line=dict(color=self.colors['value'], width=2, dash='dash')),
                row=1, col=1, secondary_y=True
            )
        
        # 2. Monthly costs
        fig.add_trace(
            go.Scatter(x=months, y=model_results['costs']['total'], name='Monthly Cost',
                      line=dict(color=self.colors['cost'], width=2)),
            row=1, col=2
        )
        
        # 3. Cumulative ROI
        cumulative_value = np.cumsum(model_results.get('value', np.zeros_like(months)))
        cumulative_costs = model_results['costs']['cumulative']
        
        fig.add_trace(
            go.Scatter(x=months, y=cumulative_value, name='Cum. Value',
                      line=dict(color=self.colors['value'], width=2)),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=months, y=cumulative_costs, name='Cum. Cost',
                      line=dict(color=self.colors['cost'], width=2)),
            row=2, col=1
        )
        
        # 4. Value components (pie chart)
        if 'impact_breakdown' in model_results:
            fig.add_trace(
                go.Pie(
                    labels=['Time', 'Quality', 'Capacity', 'Strategic'],
                    values=[
                        model_results['impact_breakdown'].get('time_value', 0),
                        model_results['impact_breakdown'].get('quality_value', 0),
                        model_results['impact_breakdown'].get('capacity_value', 0),
                        model_results['impact_breakdown'].get('strategic_value', 0)
                    ],
                    hole=0.3
                ),
                row=2, col=2
            )
        
        # 5. Cost per developer
        if 'cost_per_dev' in model_results:
            fig.add_trace(
                go.Scatter(x=months, y=model_results['cost_per_dev'], name='Cost/Dev',
                          line=dict(color=self.colors['roi'], width=2)),
                row=3, col=1
            )
        
        # 6. Risk scenarios (if available)
        if 'risk_scenarios' in model_results:
            fig.add_trace(
                go.Scatter(x=months, y=model_results['risk_scenarios']['p90'], name='P90',
                          line=dict(color='lightgreen', width=1)),
                row=3, col=2
            )
            fig.add_trace(
                go.Scatter(x=months, y=model_results['risk_scenarios']['p50'], name='P50',
                          line=dict(color='orange', width=2)),
                row=3, col=2
            )
            fig.add_trace(
                go.Scatter(x=months, y=model_results['risk_scenarios']['p10'], name='P10',
                          line=dict(color='lightcoral', width=1)),
                row=3, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=1000,
            showlegend=True,
            title_text="AI Development Impact - Executive Dashboard",
            plot_bgcolor='white'
        )
        
        # Update axes
        fig.update_xaxes(title_text="Month", gridcolor='lightgray')
        fig.update_yaxes(gridcolor='lightgray')
        
        return fig
    
    def export_charts(self, figures: Dict[str, go.Figure], output_dir: str = "charts"):
        """Export all charts to files"""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        for name, fig in figures.items():
            # Save as HTML (interactive)
            fig.write_html(f"{output_dir}/{name}.html")
            
            # Save as PNG (static)
            fig.write_image(f"{output_dir}/{name}.png", width=1200, height=800)
        
        print(f"Charts exported to {output_dir}/")


def create_summary_table(model_results: Dict) -> pd.DataFrame:
    """Create executive summary table"""
    
    summary_data = {
        'Metric': [
            'Total Investment (3 years)',
            'Total Value Created (3 years)',
            'Net Present Value',
            'ROI %',
            'Payback Period (months)',
            'Peak Adoption Rate',
            'Cost per Developer (annual)',
            'Value per Developer (annual)',
            'Breakeven Month',
            'Risk-Adjusted NPV (P50)'
        ],
        'Value': [
            f"${model_results.get('total_cost_3y', 0):,.0f}",
            f"${model_results.get('total_value_3y', 0):,.0f}",
            f"${model_results.get('npv', 0):,.0f}",
            f"{model_results.get('roi_percent', 0):.1f}%",
            f"{model_results.get('payback_months', 'N/A')}",
            f"{model_results.get('peak_adoption', 0)*100:.1f}%",
            f"${model_results.get('annual_cost_per_dev', 0):,.0f}",
            f"${model_results.get('annual_value_per_dev', 0):,.0f}",
            f"{model_results.get('breakeven_month', 'N/A')}",
            f"${model_results.get('risk_adjusted_npv', 0):,.0f}"
        ]
    }
    
    return pd.DataFrame(summary_data)