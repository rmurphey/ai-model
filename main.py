#!/usr/bin/env python3
"""
AI Development Impact Model - Main Orchestration
Run scenarios and generate reports for AI tool adoption impact.
"""

import yaml
import numpy as np
import pandas as pd
from typing import Dict, Optional, List
import argparse
from tabulate import tabulate
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from utils.colors import *

from src.model.baseline import BaselineMetrics, create_industry_baseline, calculate_opportunity_cost
from src.model.impact_model import ImpactFactors, BusinessImpact, create_impact_scenario
from src.model.adoption_dynamics import AdoptionParameters, AdoptionModel, create_adoption_scenario
from src.model.cost_structure import AIToolCosts, CostModel, create_cost_scenario, calculate_breakeven


class AIImpactModel:
    """Main orchestration class for the AI impact model"""
    
    def __init__(self, scenario_file: str = "src/scenarios/scenarios.yaml"):
        """Initialize with scenario configurations"""
        with open(scenario_file, 'r') as f:
            self.scenarios = yaml.safe_load(f)
        
        self.results = {}
    
    def load_scenario(self, scenario_name: str) -> Dict:
        """Load a specific scenario configuration"""
        if scenario_name not in self.scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found. Available: {list(self.scenarios.keys())}")
        
        return self.scenarios[scenario_name]
    
    def run_scenario(self, scenario_name: str) -> Dict:
        """Run a complete scenario analysis"""
        
        print(section_divider(f"Running Scenario: {scenario_name}"))
        
        config = self.load_scenario(scenario_name)
        months = config.get('timeframe_months', 24)
        
        # 1. Setup baseline
        if isinstance(config['baseline'], dict) and 'profile' in config['baseline']:
            baseline = create_industry_baseline(config['baseline']['profile'])
        elif isinstance(config['baseline'], str):
            baseline = create_industry_baseline(config['baseline'])
        else:
            baseline = BaselineMetrics(**config['baseline'])
        
        # 2. Setup adoption model
        if isinstance(config['adoption'], dict) and 'scenario' in config['adoption']:
            adoption_params = create_adoption_scenario(config['adoption']['scenario'])
        else:
            adoption_params = AdoptionParameters(**config['adoption'])
        
        adoption_model = AdoptionModel(adoption_params)
        adoption_curve = adoption_model.calculate_adoption_curve(months)
        efficiency_curve = adoption_model.calculate_efficiency_curve(months)
        effective_adoption = adoption_model.calculate_effective_adoption(months)
        
        # 3. Setup impact model
        if isinstance(config['impact'], dict) and 'scenario' in config['impact']:
            impact_factors = create_impact_scenario(config['impact']['scenario'])
        else:
            impact_factors = ImpactFactors(**config['impact'])
        
        # 4. Setup cost model
        if isinstance(config['costs'], dict) and 'scenario' in config['costs']:
            cost_structure = create_cost_scenario(config['costs']['scenario'])
        else:
            cost_structure = AIToolCosts(**config['costs'])
        
        cost_model = CostModel(cost_structure, baseline)
        
        # 5. Calculate costs
        costs = cost_model.calculate_total_costs(months, effective_adoption)
        cost_per_dev = cost_model.calculate_cost_per_developer(months, effective_adoption)
        
        # 6. Calculate value for each month
        monthly_value = np.zeros(months)
        for month in range(months):
            # Create impact model with current adoption
            impact = BusinessImpact(baseline, impact_factors, effective_adoption[month])
            monthly_impact = impact.calculate_total_impact()
            # Convert annual value to monthly
            monthly_value[month] = monthly_impact['total_annual_value'] / 12
        
        # 7. Calculate key metrics
        cumulative_value = np.cumsum(monthly_value)
        cumulative_costs = costs['cumulative']
        
        breakeven = calculate_breakeven(costs, {'total': monthly_value})
        
        # Calculate NPV (assuming 10% discount rate)
        discount_rate = 0.10 / 12  # Monthly discount rate
        discount_factors = [(1 + discount_rate) ** -i for i in range(months)]
        npv = sum((monthly_value[i] - costs['total'][i]) * discount_factors[i] for i in range(months))
        
        # Calculate final impact at full adoption
        final_impact = BusinessImpact(baseline, impact_factors, effective_adoption[-1])
        final_impact_breakdown = final_impact.calculate_total_impact()
        
        # Compile results
        results = {
            'scenario_name': scenario_name,
            'config': config,
            'baseline': baseline,
            'adoption': adoption_curve,
            'efficiency': efficiency_curve,
            'effective_adoption': effective_adoption,
            'costs': costs,
            'cost_per_dev': cost_per_dev,
            'value': monthly_value,
            'cumulative_value': cumulative_value,
            'impact_breakdown': final_impact_breakdown,
            'breakeven_month': breakeven,
            'npv': npv,
            'roi_percent': ((cumulative_value[-1] - cumulative_costs[-1]) / cumulative_costs[-1]) * 100 if cumulative_costs[-1] > 0 else 0,
            'peak_adoption': max(adoption_curve),
            'total_cost_3y': sum(costs['total'][:min(36, months)]),
            'total_value_3y': sum(monthly_value[:min(36, months)]),
            'annual_cost_per_dev': (sum(costs['total'][:12]) / (baseline.team_size * np.mean(adoption_curve[:12]))) if np.mean(adoption_curve[:12]) > 0 else 0,
            'annual_value_per_dev': final_impact_breakdown['value_per_developer']
        }
        
        self.results[scenario_name] = results
        return results
    
    def print_summary(self, results: Dict):
        """Print colorful summary of scenario results"""
        
        print(subsection_divider(f"EXECUTIVE SUMMARY: {results['scenario_name']}"))
        
        # Key metrics with colors
        print(f"{metric('Team Size'):<30} {info(str(results['baseline'].team_size) + ' developers')}")
        print(f"{metric('Timeframe'):<30} {info(str(results['config']['timeframe_months']) + ' months')}")
        print(f"{metric('Peak Adoption'):<30} {percentage(f'{results["peak_adoption"]*100:.1f}%')}")
        print()
        
        # Financial metrics
        print(header("FINANCIAL METRICS"))
        print(f"{metric('Total Investment (3 years)'):<30} {format_currency(results['total_cost_3y'], positive_good=False)}")
        print(f"{metric('Total Value Created (3 years)'):<30} {format_currency(results['total_value_3y'])}")
        print(f"{metric('Net Present Value'):<30} {format_currency(results['npv'])}")
        print(f"{metric('ROI'):<30} {format_percentage(results['roi_percent']/100)}")
        
        breakeven_text = f"Month {results['breakeven_month']}" if results['breakeven_month'] else "Not reached"
        breakeven_color = success(breakeven_text) if results['breakeven_month'] and results['breakeven_month'] <= 12 else warning(breakeven_text)
        print(f"{metric('Breakeven'):<30} {breakeven_color}")
        print()
        
        # Per developer metrics
        print(header("PER DEVELOPER METRICS"))
        print(f"{metric('Annual Cost per Developer'):<30} {format_currency(results['annual_cost_per_dev'], positive_good=False)}")
        print(f"{metric('Annual Value per Developer'):<30} {format_currency(results['annual_value_per_dev'])}")
        print()
        
        # Value breakdown
        print(header("VALUE BREAKDOWN"))
        print(f"{metric('Time-to-Market Value'):<30} {format_currency(results['impact_breakdown']['time_value'])}")
        print(f"{metric('Quality Improvement Value'):<30} {format_currency(results['impact_breakdown']['quality_value'])}")
        print(f"{metric('Capacity Reallocation Value'):<30} {format_currency(results['impact_breakdown']['capacity_value'])}")
        print(f"{metric('Strategic Value'):<30} {format_currency(results['impact_breakdown']['strategic_value'])}")
        
        # Print opportunity cost comparison
        opportunity = calculate_opportunity_cost(results['baseline'])
        print()
        print(header("OPPORTUNITY COST ANALYSIS"))
        print(f"{metric('Current inefficiency cost'):<30} {error(f'${opportunity["total_opportunity_cost"]:,.0f}/year')}")
        print(f"{metric('AI tool value capture'):<30} {success(f'${results["impact_breakdown"]["total_annual_value"]:,.0f}/year')}")
        
        efficiency_gain = (results['impact_breakdown']['total_annual_value']/opportunity['total_opportunity_cost'])*100
        efficiency_color = success(f'{efficiency_gain:.1f}%') if efficiency_gain > 20 else warning(f'{efficiency_gain:.1f}%')
        print(f"{metric('Efficiency gain'):<30} {efficiency_color}")
    
    def compare_scenarios(self, scenario_names: List[str] = None):
        """Compare multiple scenarios"""
        
        if scenario_names is None:
            scenario_names = list(self.results.keys())
        
        comparison_data = []
        
        for name in scenario_names:
            if name not in self.results:
                print(f"Warning: Scenario '{name}' not found in results")
                continue
            
            r = self.results[name]
            comparison_data.append({
                'Scenario': name,
                'NPV': f"${r['npv']:,.0f}",
                'ROI %': f"{r['roi_percent']:.1f}%",
                'Breakeven': f"Month {r['breakeven_month']}" if r['breakeven_month'] else "N/A",
                'Peak Adoption': f"{r['peak_adoption']*100:.1f}%",
                'Cost/Dev/Year': f"${r['annual_cost_per_dev']:,.0f}",
                'Value/Dev/Year': f"${r['annual_value_per_dev']:,.0f}"
            })
        
        df = pd.DataFrame(comparison_data)
        print(section_divider("SCENARIO COMPARISON", 80))
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        return df


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='AI Development Impact Model')
    parser.add_argument('--scenario', '-s', default='moderate_enterprise',
                       help='Scenario to run (or "all" for all scenarios)')
    parser.add_argument('--compare', '-c', action='store_true',
                       help='Compare all scenarios')
    
    args = parser.parse_args()
    
    # Initialize model
    model = AIImpactModel()
    
    # Run scenarios
    if args.scenario == 'all':
        # Run all non-task-distribution scenarios
        for scenario_name in model.scenarios.keys():
            if scenario_name not in ['task_distributions', 'sensitivity']:
                results = model.run_scenario(scenario_name)
                model.print_summary(results)
    else:
        results = model.run_scenario(args.scenario)
        model.print_summary(results)
    
    # Compare scenarios if requested
    if args.compare:
        # Run standard scenarios for comparison
        standard_scenarios = ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']
        for scenario in standard_scenarios:
            if scenario not in model.results:
                model.run_scenario(scenario)
        
        model.compare_scenarios(standard_scenarios)


if __name__ == "__main__":
    main()