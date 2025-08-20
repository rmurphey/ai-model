#!/usr/bin/env python3
"""
Generate all visualizations for the AI impact model
"""

import sys
from main import AIImpactModel
import plotly.io as pio

# Set default renderer to browser
pio.renderers.default = "browser"

def main():
    # Initialize model
    model = AIImpactModel()
    
    # Run all standard scenarios
    scenarios = ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']
    
    print("Running scenarios...")
    for scenario in scenarios:
        print(f"  - {scenario}")
        model.run_scenario(scenario)
    
    print("\nGenerating visualizations...")
    
    # Generate comparison chart
    print("Creating scenario comparison...")
    comparison_df = model.compare_scenarios(scenarios)
    
    # Generate individual scenario visualizations
    for scenario in scenarios:
        print(f"\nGenerating charts for {scenario}...")
        charts = model.generate_visualizations(scenario)
        
        # Show the dashboard
        if scenario == 'moderate_enterprise':
            print("Opening dashboard for moderate_enterprise scenario...")
            charts['dashboard'].show()
            
            print("\nSaving all charts to 'charts' directory...")
            model.visualizer.export_charts(charts, f"charts_{scenario}")
    
    print("\nVisualization generation complete!")
    print("Charts have been saved to charts_* directories")
    print("The dashboard should have opened in your browser.")

if __name__ == "__main__":
    main()