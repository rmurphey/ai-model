#!/usr/bin/env python3
"""
AI Development Impact Model - Main Orchestration
Run scenarios and generate reports for AI tool adoption impact.
"""

import yaml
import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Any
import argparse
from tabulate import tabulate
import sys
import os

from src.utils.colors import *
from src.utils.exceptions import ConfigurationError, ScenarioError, CalculationError
from src.utils.math_helpers import safe_divide
from src.config.constants import DEFAULT_DISCOUNT_RATE_ANNUAL, MONTHS_PER_YEAR

from src.model.baseline import BaselineMetrics, create_industry_baseline, calculate_opportunity_cost
from src.model.impact_model import ImpactFactors, BusinessImpact, create_impact_scenario
from src.model.adoption_dynamics import AdoptionParameters, AdoptionModel, create_adoption_scenario
from src.model.cost_structure import AIToolCosts, CostModel, create_cost_scenario, calculate_breakeven
from src.model.monte_carlo import MonteCarloEngine, MonteCarloResults, create_parameter_distributions_from_scenario
from src.model.distributions import ParameterDistributions


class AIImpactModel:
    """Main orchestration class for the AI impact model"""
    
    def __init__(self, scenario_file: str = "src/scenarios/scenarios.yaml"):
        """Initialize with scenario configurations"""
        # Try to use new modular loader if available
        try:
            from src.scenarios.scenario_loader import ScenarioLoader
            # Determine if path is to directory or file
            if scenario_file.endswith('.yaml'):
                # Legacy mode - single file
                loader = ScenarioLoader(scenario_file)
            else:
                # Modular mode - directory structure
                loader = ScenarioLoader(scenario_file.replace('/scenarios.yaml', ''))
            self.scenarios = loader.load_all_scenarios()
            self.loader = loader
        except (ImportError, PermissionError) as e:
            if isinstance(e, PermissionError):
                raise ConfigurationError(
                    f"Permission denied accessing scenario file: {scenario_file}",
                    config_file=scenario_file,
                    resolution_steps=[
                        f"Check file permissions: ls -la {scenario_file}",
                        f"Fix permissions: chmod 644 {scenario_file}",
                        "Ensure you have read access to the file"
                    ]
                )
            # Fall back to legacy loading
            try:
                with open(scenario_file, 'r') as f:
                    self.scenarios = yaml.safe_load(f)
                self.loader = None
            except PermissionError:
                raise ConfigurationError(
                    f"Permission denied accessing scenario file: {scenario_file}",
                    config_file=scenario_file,
                    resolution_steps=[
                        f"Check file permissions: ls -la {scenario_file}",
                        f"Fix permissions: chmod 644 {scenario_file}",
                        "Ensure you have read access to the file"
                    ]
                )
            except FileNotFoundError:
                raise ConfigurationError(
                    f"Scenario configuration file not found: {scenario_file}",
                    config_file=scenario_file,
                    resolution_steps=[
                        "Check if the file path is correct",
                        "Ensure you're running from the project root directory",
                        "Verify the file exists: ls -la src/scenarios/scenarios.yaml",
                        "If missing, restore from version control or documentation"
                    ]
                )
            except yaml.YAMLError as e:
                line_info = ""
                if hasattr(e, 'problem_mark') and e.problem_mark:
                    line_info = f" (line {e.problem_mark.line + 1}, column {e.problem_mark.column + 1})"
                
                raise ConfigurationError(
                    f"Invalid YAML format in scenario file{line_info}: {e}",
                    config_file=scenario_file,
                    resolution_steps=[
                        "Check YAML syntax using an online YAML validator",
                        f"Focus on line {e.problem_mark.line + 1} if specified" if hasattr(e, 'problem_mark') else "Review file structure",
                        "Ensure proper indentation (use spaces, not tabs)",
                        "Verify all string values are properly quoted",
                    "Compare with working examples in the repository"
                ]
            )
        except PermissionError:
            raise ConfigurationError(
                f"Permission denied accessing scenario file: {scenario_file}",
                config_file=scenario_file,
                resolution_steps=[
                    f"Check file permissions: ls -la {scenario_file}",
                    "Ensure you have read access to the file",
                    "Verify the file is not locked by another process"
                ]
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load scenario file: {e}",
                config_file=scenario_file,
                resolution_steps=[
                    "Check file permissions and content",
                    "Verify file encoding (should be UTF-8)",
                    "Ensure file is not corrupted",
                    "Try opening file manually to check readability"
                ]
            )
        
        if not self.scenarios:
            raise ConfigurationError(
                "Scenario file is empty or contains no valid scenarios",
                config_file=scenario_file,
                resolution_steps=[
                    "Check if the YAML file loaded correctly",
                    "Verify the file contains scenario definitions",
                    "Ensure proper YAML structure with scenario names as keys",
                    "Add at least one scenario configuration",
                    "Compare with example scenarios from documentation"
                ]
            )
        
        self.results = {}
    
    def get_available_scenarios(self) -> List[str]:
        """Get list of available scenario names"""
        if hasattr(self, 'loader') and self.loader:
            return self.loader.list_available_scenarios()
        return list(self.scenarios.keys())
    
    def load_scenario(self, scenario_name: str) -> Dict:
        """Load a specific scenario configuration"""
        if scenario_name not in self.scenarios:
            raise ScenarioError(
                scenario_name=scenario_name,
                issue="not found in configuration",
                available_scenarios=list(self.scenarios.keys()),
                config_file="src/scenarios/scenarios.yaml"
            )
        
        scenario = self.scenarios[scenario_name]
        
        # Validate scenario has required fields
        required_fields = ['baseline', 'adoption', 'impact', 'costs', 'timeframe_months']
        missing_fields = [field for field in required_fields if field not in scenario]
        
        if missing_fields:
            raise ConfigurationError(
                f"Scenario '{scenario_name}' is missing required fields: {', '.join(missing_fields)}",
                config_file="src/scenarios/scenarios.yaml",
                resolution_steps=[
                    f"Add missing fields to scenario '{scenario_name}': {', '.join(missing_fields)}",
                    "Check scenario structure against working examples",
                    "Ensure all required fields are properly defined",
                    "Validate field values are in correct format"
                ]
            )
        
        return scenario
    
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
        
        # Calculate NPV using default discount rate
        discount_rate = DEFAULT_DISCOUNT_RATE_ANNUAL / MONTHS_PER_YEAR  # Monthly discount rate
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
            'roi_percent': safe_divide(
                (cumulative_value[-1] - cumulative_costs[-1]) * 100,
                cumulative_costs[-1],
                default=0.0,
                context="ROI calculation"
            ),
            'peak_adoption': max(adoption_curve),
            'total_cost_3y': sum(costs['total'][:min(36, months)]),
            'total_value_3y': sum(monthly_value[:min(36, months)]),
            'annual_cost_per_dev': safe_divide(
                sum(costs['total'][:12]),
                baseline.team_size * np.mean(adoption_curve[:12]),
                default=0.0,
                context="annual cost per developer calculation"
            ),
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
    
    def run_monte_carlo(self, scenario_name: str, iterations: int = 1000, 
                       confidence: float = 0.95, target_roi: float = 100.0,
                       random_seed: Optional[int] = None) -> MonteCarloResults:
        """
        Run Monte Carlo simulation for a scenario.
        
        Args:
            scenario_name: Name of scenario to run
            iterations: Number of simulation iterations
            confidence: Confidence level for intervals (e.g., 0.95)
            target_roi: Target ROI for probability calculations
            random_seed: Random seed for reproducibility
            
        Returns:
            MonteCarloResults with distributions and statistics
        """
        print(section_divider(f"Monte Carlo Simulation: {scenario_name}"))
        print(f"Running {iterations} iterations...")
        
        # Load scenario configuration
        config = self.load_scenario(scenario_name)
        
        # Create parameter distributions from scenario
        distributions = create_parameter_distributions_from_scenario(config)
        
        # Create model runner function that Monte Carlo engine will call
        def model_runner(sampled_config):
            """Run the model with sampled parameters"""
            # This reuses the existing run_scenario logic but with sampled parameters
            return self._run_scenario_deterministic(sampled_config)
        
        # Initialize Monte Carlo engine
        mc_engine = MonteCarloEngine(
            model_runner=model_runner,
            parameter_distributions=distributions,
            iterations=iterations,
            confidence_level=confidence,
            target_roi=target_roi,
            random_seed=random_seed,
            n_jobs=1  # Start with sequential execution
        )
        
        # Run simulation
        results = mc_engine.run(config)
        
        # Store results
        self.results[f"{scenario_name}_monte_carlo"] = results
        
        return results
    
    def _run_scenario_deterministic(self, config: Dict) -> Dict:
        """Extract the deterministic scenario logic for reuse in Monte Carlo"""
        # This is the core logic from run_scenario without the print statements
        
        # 1. Create baseline
        baseline_params = config.get('baseline', {})
        baseline = create_industry_baseline(baseline_params)
        
        # 2. Create impact factors
        impact_params = config.get('impact', {})
        impact_factors = create_impact_scenario(impact_params)
        
        # 3. Create adoption model
        adoption_params = config.get('adoption', {})
        adoption_parameters = create_adoption_scenario(adoption_params)
        adoption_model = AdoptionModel(adoption_parameters)
        
        # 4. Create cost model
        cost_params = config.get('costs', {})
        ai_costs = create_cost_scenario(cost_params)
        cost_model = CostModel(ai_costs, baseline)
        
        # 5. Run simulation
        months = config.get('timeframe_months', 24)
        
        adoption_curve = adoption_model.calculate_adoption_curve(months)
        efficiency_curve = adoption_model.calculate_efficiency_curve(months)
        effective_adoption = adoption_curve * efficiency_curve
        
        costs = cost_model.calculate_total_costs(months, adoption_curve)
        cost_per_dev = cost_model.calculate_cost_per_developer(months, adoption_curve)
        
        monthly_value = np.zeros(months)
        for month in range(months):
            monthly_impact = BusinessImpact(baseline, impact_factors, effective_adoption[month])
            monthly_impact_breakdown = monthly_impact.calculate_total_impact()
            monthly_value[month] = monthly_impact_breakdown['total_annual_value'] / 12
        
        cumulative_value = np.cumsum(monthly_value)
        cumulative_costs = costs['cumulative']
        
        breakeven = calculate_breakeven(costs, {'total': monthly_value})
        
        # Calculate NPV
        discount_rate = config.get('economic', {}).get('discount_rate_annual', DEFAULT_DISCOUNT_RATE_ANNUAL) / MONTHS_PER_YEAR
        discount_factors = [(1 + discount_rate) ** -i for i in range(months)]
        npv = sum((monthly_value[i] - costs['total'][i]) * discount_factors[i] for i in range(months))
        
        # Calculate final impact
        final_impact = BusinessImpact(baseline, impact_factors, effective_adoption[-1])
        final_impact_breakdown = final_impact.calculate_total_impact()
        
        # Calculate key metrics
        total_cost_3y = sum(costs['total'][:min(36, months)])
        total_value_3y = sum(monthly_value[:min(36, months)])
        roi_percent = safe_divide((total_value_3y - total_cost_3y), total_cost_3y) * 100
        annual_cost_per_dev = safe_divide(total_cost_3y / min(3, months/12), baseline.team_size * max(adoption_curve))
        annual_value_per_dev = safe_divide(total_value_3y / min(3, months/12), baseline.team_size * max(effective_adoption))
        
        return {
            'npv': npv,
            'roi_percent': roi_percent,
            'breakeven_month': breakeven,
            'total_cost_3y': total_cost_3y,
            'total_value_3y': total_value_3y,
            'peak_adoption': max(adoption_curve),
            'annual_cost_per_dev': annual_cost_per_dev,
            'annual_value_per_dev': annual_value_per_dev,
            'impact_breakdown': final_impact_breakdown,
            'baseline': baseline
        }
    
    def print_monte_carlo_summary(self, results: MonteCarloResults):
        """Print enhanced summary of Monte Carlo simulation results"""
        from src.model.monte_carlo_viz import (
            create_distribution_sparkline,
            create_confidence_interval_visualization,
            create_risk_gauge,
            create_outcome_probability_report,
            create_value_at_risk_report,
            create_sensitivity_tornado_chart
        )
        
        print()
        print(header("MONTE CARLO ANALYSIS"))
        print(f"Iterations: {results.iterations}")
        print(f"Convergence: {'✓ Achieved' if results.convergence_achieved else '✗ Not achieved'}")
        print(f"Runtime: {results.runtime_seconds:.1f} seconds")
        if results.random_seed:
            print(f"Random Seed: {results.random_seed}")
        print()
        
        # NPV Distribution with sparkline
        print(header("NPV DISTRIBUTION"))
        sparkline = create_distribution_sparkline(results.npv_distribution, width=50)
        print(f"Distribution: {sparkline}")
        print()
        print(f"{'Mean':<20} {format_currency(results.npv_stats['mean'])}")
        print(f"{'Median (P50)':<20} {format_currency(results.npv_stats['p50'])}")
        print(f"{'Std Deviation':<20} {format_currency(results.npv_stats['std'])}")
        print()
        
        # Confidence interval visualization
        ci_lower, ci_upper = results.get_confidence_interval('npv')
        print("95% Confidence Interval:")
        ci_viz = create_confidence_interval_visualization(
            ci_lower, ci_upper, results.npv_stats['mean'], 
            currency=True, width=40
        )
        print(ci_viz)
        print()
        
        # Percentiles
        print("Percentiles:")
        print(f"  {'P5':<5} {format_currency(results.npv_stats['p5'])}")
        print(f"  {'P10':<5} {format_currency(results.npv_stats['p10'])}")
        print(f"  {'P25':<5} {format_currency(results.npv_stats['p25'])}")
        print(f"  {'P50':<5} {format_currency(results.npv_stats['p50'])}")
        print(f"  {'P75':<5} {format_currency(results.npv_stats['p75'])}")
        print(f"  {'P90':<5} {format_currency(results.npv_stats['p90'])}")
        print(f"  {'P95':<5} {format_currency(results.npv_stats['p95'])}")
        print()
        
        # ROI Distribution with sparkline
        print(header("ROI DISTRIBUTION"))
        roi_sparkline = create_distribution_sparkline(results.roi_distribution, width=50)
        print(f"Distribution: {roi_sparkline}")
        print()
        print(f"{'Mean':<20} {results.roi_stats['mean']:.1f}%")
        print(f"{'Median (P50)':<20} {results.roi_stats['p50']:.1f}%")
        print(f"{'P10 - P90 Range':<20} {results.roi_stats['p10']:.1f}% - {results.roi_stats['p90']:.1f}%")
        print()
        
        # Breakeven Distribution
        print(header("BREAKEVEN DISTRIBUTION"))
        be_sparkline = create_distribution_sparkline(results.breakeven_distribution, width=50)
        print(f"Distribution: {be_sparkline}")
        print()
        print(f"{'Mean':<20} {results.breakeven_stats['mean']:.1f} months")
        print(f"{'Median (P50)':<20} {results.breakeven_stats['p50']:.1f} months")
        print(f"{'P10 - P90 Range':<20} {results.breakeven_stats['p10']:.1f} - {results.breakeven_stats['p90']:.1f} months")
        print()
        
        # Risk Metrics with gauges
        print(header("RISK ANALYSIS"))
        print(f"{'Positive NPV':<30} {create_risk_gauge(results.probability_positive_npv)}")
        print(f"{'Breakeven < 24 months':<30} {create_risk_gauge(results.probability_breakeven_within_24_months)}")
        print(f"{'ROI > 100%':<30} {create_risk_gauge(results.probability_roi_above_target)}")
        print()
        
        # Outcome probabilities
        print(create_outcome_probability_report(results))
        print()
        
        # Value at Risk
        print(create_value_at_risk_report(results))
        print()
        
        # Parameter Sensitivity with tornado chart
        print(header("SENSITIVITY ANALYSIS"))
        print("Impact on NPV (correlation strength):")
        print(create_sensitivity_tornado_chart(results.parameter_correlations, top_n=10))
        print()
        
        # Distribution histogram for NPV
        self._print_distribution_histogram(results.npv_distribution, "NPV Distribution Histogram", currency=True)
    
    def _print_distribution_histogram(self, data: np.ndarray, title: str, currency: bool = False, bins: int = 20):
        """Print a simple text-based histogram"""
        print(header(title))
        
        # Calculate histogram
        counts, edges = np.histogram(data, bins=bins)
        max_count = max(counts)
        
        # Print histogram
        for i in range(len(counts)):
            bar_length = int((counts[i] / max_count) * 40)
            bar = "█" * bar_length
            
            if currency:
                label = f"${edges[i]/1000:.0f}K - ${edges[i+1]/1000:.0f}K"
            else:
                label = f"{edges[i]:.1f} - {edges[i+1]:.1f}"
            
            percentage = (counts[i] / len(data)) * 100
            print(f"{label:<25} {bar:<40} {percentage:.1f}%")


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='AI Development Impact Model')
    parser.add_argument('--scenario', '-s', default='moderate_enterprise',
                       help='Scenario to run (or "all" for all scenarios)')
    parser.add_argument('--compare', '-c', action='store_true',
                       help='Compare all scenarios')
    parser.add_argument('--monte-carlo', '-mc', action='store_true',
                       help='Run Monte Carlo simulation')
    parser.add_argument('--iterations', '-i', type=int, default=1000,
                       help='Number of Monte Carlo iterations (default: 1000)')
    parser.add_argument('--confidence', type=float, default=0.95,
                       help='Confidence level for intervals (default: 0.95)')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed for reproducibility')
    parser.add_argument('--scenario-file', default='src/scenarios/scenarios.yaml',
                       help='Path to scenario configuration file')
    
    args = parser.parse_args()
    
    # Initialize model
    model = AIImpactModel(scenario_file=args.scenario_file)
    
    # Run Monte Carlo simulation if requested
    if args.monte_carlo:
        scenario_to_run = args.scenario
        model_mc = model
        
        # Check if using a Monte Carlo scenario file
        mc_scenario_file = args.scenario_file.replace('.yaml', '_monte_carlo.yaml')
        if os.path.exists(mc_scenario_file) and args.scenario_file == 'src/scenarios/scenarios.yaml':
            # Load Monte Carlo scenarios if available and using default file
            model_mc = AIImpactModel(scenario_file=mc_scenario_file)
            
            # Check if Monte Carlo version exists
            if f"{scenario_to_run}_monte_carlo" in model_mc.scenarios:
                scenario_to_run = f"{scenario_to_run}_monte_carlo"
            elif scenario_to_run not in model_mc.scenarios:
                print(f"Warning: Scenario '{scenario_to_run}' not found in Monte Carlo scenarios, using deterministic version")
                model_mc = model
        elif args.scenario_file != 'src/scenarios/scenarios.yaml':
            # User specified a custom scenario file
            model_mc = model
            if scenario_to_run not in model_mc.scenarios:
                print(f"Error: Scenario '{scenario_to_run}' not found in {args.scenario_file}")
                print(f"Available scenarios: {', '.join(model_mc.scenarios.keys())}")
                sys.exit(1)
        
        # First, run the deterministic scenario to show baseline report
        print(section_divider("DETERMINISTIC BASELINE ANALYSIS"))
        deterministic_results = model.run_scenario(args.scenario if args.scenario in model.scenarios else scenario_to_run.replace('_monte_carlo', ''))
        model.print_summary(deterministic_results)
        
        # Then run Monte Carlo simulation
        print()
        print(section_divider("PROBABILISTIC MONTE CARLO ANALYSIS"))
        mc_results = model_mc.run_monte_carlo(
            scenario_to_run,
            iterations=args.iterations,
            confidence=args.confidence,
            random_seed=args.seed
        )
        model_mc.print_monte_carlo_summary(mc_results)
    else:
        # Run deterministic scenarios
        if args.scenario == 'all':
            # Run all non-task-distribution scenarios
            for scenario_name in model.scenarios.keys():
                if scenario_name not in ['task_distributions', 'sensitivity', 'monte_carlo_template']:
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