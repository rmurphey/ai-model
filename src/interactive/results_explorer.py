"""
Interactive results explorer for navigating and analyzing model outputs.
Provides menu-driven exploration of results with refinement options.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
import os

from .prompts import (
    display_header,
    display_results_table,
    display_info,
    display_success,
    display_warning,
    display_comparison,
    display_sparkline,
    select_from_menu,
    get_text_input,
    get_numeric_input,
    confirm_action,
    pause
)

if TYPE_CHECKING:
    from .wizard import InteractiveWizard


class ResultsExplorer:
    """Interactive explorer for model results."""
    
    def explore(
        self, 
        scenario_name: str, 
        scenario: Dict[str, Any], 
        results: Dict[str, Any],
        wizard: Optional['InteractiveWizard'] = None
    ):
        """
        Main exploration interface for results.
        
        Args:
            scenario_name: Name of the scenario
            scenario: Scenario configuration
            results: Model results dictionary
            wizard: Reference to parent wizard for refinement
        """
        while True:
            self._display_summary(scenario_name, results)
            
            choice = self._results_menu()
            
            if choice == '1':
                self._view_detailed_breakdown(results)
            elif choice == '2':
                self._view_adoption_timeline(results)
            elif choice == '3':
                self._view_value_components(results)
            elif choice == '4':
                self._view_cost_breakdown(results)
            elif choice == '5':
                self._run_what_if_analysis(scenario_name, scenario, wizard)
            elif choice == '6':
                self._run_sensitivity_analysis(scenario_name, scenario)
            elif choice == '7':
                self._refine_parameters(scenario_name, scenario, results, wizard)
            elif choice == '8':
                self._compare_scenarios(scenario_name, results, wizard)
            elif choice == '9':
                self._export_results(scenario_name, scenario, results)
            elif choice == 'b':
                break
            else:
                display_warning("Invalid choice. Please try again.")
    
    def _display_summary(self, scenario_name: str, results: Dict[str, Any]):
        """Display results summary."""
        display_header(f"Results: {scenario_name}")
        
        # Key metrics table
        metrics = [
            ["Metric", "Value"],
            ["NPV (3 years)", f"${results.get('npv', 0):,.0f}"],
            ["ROI", f"{results.get('roi', 0):.1%}"],
            ["Breakeven Month", str(results.get('breakeven_month', 'N/A'))],
            ["Peak Adoption", f"{results.get('peak_adoption_rate', 0):.1%}"],
            ["Total Investment", f"${results.get('total_costs', 0):,.0f}"],
            ["Total Value Created", f"${results.get('total_value', 0):,.0f}"]
        ]
        
        display_results_table(metrics[1:], headers=metrics[0])
    
    def _results_menu(self) -> str:
        """Display results exploration menu."""
        print("\nExplore Results:")
        options = [
            ("1", "View detailed breakdown"),
            ("2", "View adoption timeline"),
            ("3", "View value components"),
            ("4", "View cost breakdown"),
            ("5", "Run what-if scenarios"),
            ("6", "Run sensitivity analysis"),
            ("7", "Refine parameters"),
            ("8", "Compare with other scenarios"),
            ("9", "Export results"),
            ("b", "Back to main menu")
        ]
        
        for key, desc in options:
            print(f"  {key}. {desc}")
        
        return get_text_input("\nSelection", default="1").lower()
    
    def _view_detailed_breakdown(self, results: Dict[str, Any]):
        """View detailed financial breakdown."""
        display_header("Detailed Financial Breakdown")
        
        # Annual breakdown
        print("\n=== Annual Breakdown ===")
        annual_data = []
        
        for year in range(1, 4):
            year_key = f"year_{year}"
            if year_key in results:
                year_data = results[year_key]
                annual_data.append([
                    f"Year {year}",
                    f"${year_data.get('costs', 0):,.0f}",
                    f"${year_data.get('value', 0):,.0f}",
                    f"${year_data.get('net', 0):,.0f}"
                ])
        
        if annual_data:
            display_results_table(
                annual_data,
                headers=["Period", "Costs", "Value", "Net"]
            )
        
        # Per-developer metrics
        print("\n=== Per-Developer Metrics ===")
        per_dev = results.get('per_developer_metrics', {})
        dev_data = [
            ["Annual Cost", f"${per_dev.get('annual_cost', 0):,.0f}"],
            ["Annual Value", f"${per_dev.get('annual_value', 0):,.0f}"],
            ["Net Benefit", f"${per_dev.get('net_benefit', 0):,.0f}"],
            ["Payback Period", f"{per_dev.get('payback_months', 0):.1f} months"]
        ]
        display_results_table(dev_data)
        
        pause()
    
    def _view_adoption_timeline(self, results: Dict[str, Any]):
        """View adoption progression over time."""
        display_header("Adoption Timeline")
        
        adoption = results.get('adoption_metrics', {})
        
        print("\n=== Adoption Phases ===")
        phases_data = [
            ["Early Adopters", f"{adoption.get('early_adopters', 0):.1%}"],
            ["Early Majority", f"{adoption.get('early_majority', 0):.1%}"],
            ["Late Majority", f"{adoption.get('late_majority', 0):.1%}"],
            ["Laggards", f"{adoption.get('laggards', 0):.1%}"],
            ["Peak Adoption", f"{adoption.get('peak', 0):.1%}"]
        ]
        display_results_table(phases_data)
        
        # Monthly progression sparkline
        if 'monthly_adoption' in results:
            print("\n=== Monthly Adoption Rate ===")
            monthly = results['monthly_adoption'][:24]  # First 2 years
            display_sparkline(monthly, width=40, label="Adoption %")
        
        # Efficiency curve
        if 'efficiency_curve' in results:
            print("\n=== Learning Curve (Efficiency) ===")
            efficiency = results['efficiency_curve'][:12]  # First year
            display_sparkline(efficiency, width=40, label="Efficiency")
        
        pause()
    
    def _view_value_components(self, results: Dict[str, Any]):
        """View breakdown of value creation."""
        display_header("Value Creation Components")
        
        value_breakdown = results.get('value_breakdown', {})
        
        # Value components table
        components = [
            ["Component", "Annual Value", "% of Total"],
            ["Time Savings", 
             f"${value_breakdown.get('time_value', 0):,.0f}",
             f"{value_breakdown.get('time_percent', 0):.1%}"],
            ["Quality Improvements", 
             f"${value_breakdown.get('quality_value', 0):,.0f}",
             f"{value_breakdown.get('quality_percent', 0):.1%}"],
            ["Capacity Gains", 
             f"${value_breakdown.get('capacity_value', 0):,.0f}",
             f"{value_breakdown.get('capacity_percent', 0):.1%}"],
            ["Strategic Value", 
             f"${value_breakdown.get('strategic_value', 0):,.0f}",
             f"{value_breakdown.get('strategic_percent', 0):.1%}"]
        ]
        
        display_results_table(components[1:], headers=components[0])
        
        # Specific improvements
        print("\n=== Specific Improvements ===")
        improvements = results.get('improvements', {})
        imp_data = [
            ["Feature Cycle Time", f"{improvements.get('feature_cycle', 0):.1%} reduction"],
            ["Bug Fix Time", f"{improvements.get('bug_fix', 0):.1%} reduction"],
            ["Defect Rate", f"{improvements.get('defects', 0):.1%} reduction"],
            ["Incident Rate", f"{improvements.get('incidents', 0):.1%} reduction"]
        ]
        display_results_table(imp_data)
        
        pause()
    
    def _view_cost_breakdown(self, results: Dict[str, Any]):
        """View detailed cost breakdown."""
        display_header("Cost Structure Breakdown")
        
        costs = results.get('cost_breakdown', {})
        
        # Cost components
        components = [
            ["Component", "Total Cost", "Monthly Average"],
            ["Licensing", 
             f"${costs.get('licensing_total', 0):,.0f}",
             f"${costs.get('licensing_monthly', 0):,.0f}"],
            ["Token Usage", 
             f"${costs.get('tokens_total', 0):,.0f}",
             f"${costs.get('tokens_monthly', 0):,.0f}"],
            ["Training", 
             f"${costs.get('training_total', 0):,.0f}",
             f"${costs.get('training_monthly', 0):,.0f}"],
            ["Hidden Costs", 
             f"${costs.get('hidden_total', 0):,.0f}",
             f"${costs.get('hidden_monthly', 0):,.0f}"]
        ]
        
        display_results_table(components[1:], headers=components[0])
        
        # Cost evolution
        print("\n=== Cost Evolution ===")
        evolution = costs.get('monthly_costs', [])[:12]
        if evolution:
            display_sparkline(evolution, width=40, label="Monthly Costs")
        
        pause()
    
    def _run_what_if_analysis(self, scenario_name: str, scenario: Dict[str, Any], wizard: Optional['InteractiveWizard']):
        """Run what-if scenarios."""
        display_header("What-If Analysis")
        
        variations = [
            ("conservative", "Conservative (-20% all improvements)", 0.8),
            ("optimistic", "Optimistic (+20% all improvements)", 1.2),
            ("slow", "Slow adoption (2x time to plateau)", "slow"),
            ("fast", "Fast adoption (0.5x time to plateau)", "fast"),
            ("high_cost", "Higher costs (+30% all costs)", "costs"),
            ("custom", "Custom adjustments", None)
        ]
        
        print("\nSelect variation:")
        for i, (key, desc, _) in enumerate(variations, 1):
            print(f"  {i}. {desc}")
        
        choice = get_text_input("\nSelection", default="1")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(variations):
                key, desc, modifier = variations[idx]
                
                # Create modified scenario
                modified_scenario = self._apply_what_if(scenario, key, modifier)
                modified_name = f"{scenario_name}_whatif_{key}"
                
                display_info(f"Running: {desc}")
                
                # Run the modified scenario
                if wizard:
                    wizard.session_data['scenarios'][modified_name] = modified_scenario
                    wizard._run_and_explore_scenario(modified_name, modified_scenario)
        except (ValueError, IndexError):
            display_warning("Invalid selection")
    
    def _apply_what_if(self, scenario: Dict[str, Any], variation: str, modifier: Any) -> Dict[str, Any]:
        """Apply what-if modifications to scenario."""
        import copy
        modified = copy.deepcopy(scenario)
        
        if variation == "conservative" and isinstance(modifier, float):
            # Reduce all impact factors
            for key in modified.get('impact', {}).keys():
                modified['impact'][key] *= modifier
        
        elif variation == "optimistic" and isinstance(modifier, float):
            # Increase all impact factors
            for key in modified.get('impact', {}).keys():
                modified['impact'][key] = min(modified['impact'][key] * modifier, 0.8)
        
        elif variation == "slow" and modifier == "slow":
            # Double time to plateau
            if 'time_to_plateau_months' in modified.get('adoption', {}):
                modified['adoption']['time_to_plateau_months'] *= 2
        
        elif variation == "fast" and modifier == "fast":
            # Halve time to plateau
            if 'time_to_plateau_months' in modified.get('adoption', {}):
                modified['adoption']['time_to_plateau_months'] = max(3, modified['adoption']['time_to_plateau_months'] // 2)
        
        elif variation == "high_cost" and modifier == "costs":
            # Increase all costs
            for key in modified.get('costs', {}).keys():
                if 'cost' in key or 'price' in key:
                    modified['costs'][key] *= 1.3
        
        elif variation == "custom":
            # Interactive custom adjustments
            display_info("Custom adjustments - enter percentage changes (e.g., -20 or +30)")
            
            # Adjust key parameters
            if 'impact' in modified:
                change = get_numeric_input("Feature cycle reduction change (%)", default=0, min_val=-50, max_val=50)
                if change != 0:
                    factor = 1 + (change / 100)
                    modified['impact']['feature_cycle_reduction'] *= factor
            
            if 'adoption' in modified:
                change = get_numeric_input("Adoption rate change (%)", default=0, min_val=-50, max_val=50)
                if change != 0:
                    factor = 1 + (change / 100)
                    for key in ['early_adopter_rate', 'early_majority_rate', 'late_majority_rate']:
                        if key in modified['adoption']:
                            modified['adoption'][key] *= factor
        
        return modified
    
    def _run_sensitivity_analysis(self, scenario_name: str, scenario: Dict[str, Any]):
        """Run sensitivity analysis on the scenario."""
        display_header("Sensitivity Analysis")
        
        display_info("Running sensitivity analysis... This may take a moment.")
        
        try:
            from ..analysis.sensitivity_analysis import perform_sensitivity_analysis
            
            # Run sensitivity analysis
            sensitivity_results = perform_sensitivity_analysis(
                scenario,
                num_samples=256,  # Fewer samples for interactive mode
                output_metric='npv'
            )
            
            # Display top sensitivity drivers
            print("\n=== Top Sensitivity Drivers ===")
            print("Parameters that most affect NPV:\n")
            
            top_params = sensitivity_results.get('ranked_parameters', [])[:10]
            for i, (param, score) in enumerate(top_params, 1):
                bar_width = int(score * 40)
                bar = "█" * bar_width + "░" * (40 - bar_width)
                print(f"{i:2}. {param:40} [{bar}] {score:.3f}")
            
            # Offer to refine based on sensitivity
            if confirm_action("\nWould you like to see detailed sensitivity metrics?"):
                self._display_detailed_sensitivity(sensitivity_results)
            
        except Exception as e:
            display_warning(f"Could not run sensitivity analysis: {e}")
        
        pause()
    
    def _display_detailed_sensitivity(self, sensitivity_results: Dict[str, Any]):
        """Display detailed sensitivity metrics."""
        print("\n=== Detailed Sensitivity Metrics ===")
        
        # First-order indices
        if 'first_order' in sensitivity_results:
            print("\nFirst-Order Effects (direct impact):")
            for param, value in list(sensitivity_results['first_order'].items())[:5]:
                print(f"  {param}: {value:.4f}")
        
        # Total effects
        if 'total_effects' in sensitivity_results:
            print("\nTotal Effects (including interactions):")
            for param, value in list(sensitivity_results['total_effects'].items())[:5]:
                print(f"  {param}: {value:.4f}")
    
    def _refine_parameters(
        self, 
        scenario_name: str, 
        scenario: Dict[str, Any], 
        results: Dict[str, Any],
        wizard: Optional['InteractiveWizard']
    ):
        """Refine scenario parameters based on analysis."""
        display_header("Parameter Refinement")
        
        # Identify parameters for refinement
        print("\nSuggested refinements based on analysis:")
        
        suggestions = []
        
        # Check if breakeven is too long
        if results.get('breakeven_month', float('inf')) > 24:
            suggestions.append(("adoption", "Increase adoption rate or efficiency"))
            suggestions.append(("costs", "Reduce per-seat or training costs"))
        
        # Check if ROI is low
        if results.get('roi', 0) < 1.0:
            suggestions.append(("impact", "Increase expected improvements"))
            suggestions.append(("timeframe", "Extend analysis timeframe"))
        
        # Check if adoption is low
        if results.get('peak_adoption_rate', 0) < 0.5:
            suggestions.append(("strategy", "Consider mandated adoption"))
            suggestions.append(("training", "Increase training investment"))
        
        if not suggestions:
            display_success("Scenario appears well-balanced!")
            pause()
            return
        
        for i, (category, suggestion) in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        if wizard and confirm_action("\nWould you like to refine parameters?"):
            # Get high-sensitivity parameters
            sensitivity_params = self._get_key_parameters(scenario, results)
            wizard.refine_scenario(scenario_name, scenario, sensitivity_params)
    
    def _get_key_parameters(self, scenario: Dict[str, Any], results: Dict[str, Any]) -> List[str]:
        """Identify key parameters for refinement."""
        # Return most impactful parameters
        return [
            "impact.feature_cycle_reduction",
            "adoption.plateau_efficiency",
            "costs.cost_per_seat_month",
            "adoption.dropout_rate_month",
            "impact.defect_reduction"
        ]
    
    def _compare_scenarios(self, scenario_name: str, results: Dict[str, Any], wizard: Optional['InteractiveWizard']):
        """Compare current scenario with others."""
        display_header("Scenario Comparison")
        
        if not wizard or len(wizard.session_data['results']) < 2:
            display_warning("Need at least 2 scenarios to compare.")
            pause()
            return
        
        # List available scenarios
        print("\nAvailable scenarios for comparison:")
        scenarios = list(wizard.session_data['results'].keys())
        other_scenarios = [s for s in scenarios if s != scenario_name]
        
        for i, name in enumerate(other_scenarios, 1):
            print(f"  {i}. {name}")
        
        choice = get_text_input("\nSelect scenario to compare with", default="1")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(other_scenarios):
                compare_name = other_scenarios[idx]
                compare_results = wizard.session_data['results'][compare_name]
                
                print("\n" + "="*50)
                display_comparison(
                    scenario_name, results.get('npv', 0),
                    compare_name, compare_results.get('npv', 0),
                    format_as="currency"
                )
                
                display_comparison(
                    scenario_name, results.get('roi', 0),
                    compare_name, compare_results.get('roi', 0),
                    format_as="percentage"
                )
                
                display_comparison(
                    scenario_name, results.get('breakeven_month', 'N/A'),
                    compare_name, compare_results.get('breakeven_month', 'N/A'),
                    format_as="number"
                )
        except (ValueError, IndexError):
            display_warning("Invalid selection")
        
        pause()
    
    def _export_results(self, scenario_name: str, scenario: Dict[str, Any], results: Dict[str, Any]):
        """Export results to file."""
        display_header("Export Results")
        
        formats = [
            ("txt", "Text report"),
            ("yaml", "YAML configuration"),
            ("both", "Both formats")
        ]
        
        format_choice = select_from_menu(
            "Select export format:",
            formats
        )
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{scenario_name}_{timestamp}"
        
        output_dir = "outputs/interactive"
        os.makedirs(output_dir, exist_ok=True)
        
        if format_choice in ["txt", "both"]:
            # Export text report
            txt_file = os.path.join(output_dir, f"{base_name}.txt")
            self._export_text_report(txt_file, scenario_name, scenario, results)
            display_success(f"Text report saved to: {txt_file}")
        
        if format_choice in ["yaml", "both"]:
            # Export YAML configuration
            yaml_file = os.path.join(output_dir, f"{base_name}.yaml")
            self._export_yaml_config(yaml_file, scenario)
            display_success(f"Scenario configuration saved to: {yaml_file}")
        
        pause()
    
    def _export_text_report(self, filepath: str, scenario_name: str, scenario: Dict[str, Any], results: Dict[str, Any]):
        """Export results as text report."""
        with open(filepath, 'w') as f:
            f.write(f"AI Impact Analysis Report\n")
            f.write(f"Scenario: {scenario_name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            f.write("KEY METRICS\n")
            f.write("-"*40 + "\n")
            f.write(f"NPV (3 years):       ${results.get('npv', 0):,.0f}\n")
            f.write(f"ROI:                 {results.get('roi', 0):.1%}\n")
            f.write(f"Breakeven Month:     {results.get('breakeven_month', 'N/A')}\n")
            f.write(f"Peak Adoption:       {results.get('peak_adoption_rate', 0):.1%}\n")
            f.write(f"Total Investment:    ${results.get('total_costs', 0):,.0f}\n")
            f.write(f"Total Value Created: ${results.get('total_value', 0):,.0f}\n")
            f.write("\n")
            
            f.write("SCENARIO CONFIGURATION\n")
            f.write("-"*40 + "\n")
            f.write(f"Team Size:           {scenario.get('baseline', {}).get('team_size', 'N/A')}\n")
            f.write(f"Timeframe:           {scenario.get('timeframe_months', 24)} months\n")
            f.write(f"Adoption Strategy:   {scenario.get('adoption', {}).get('scenario', 'N/A')}\n")
            f.write("\n")
            
            # Add more detailed sections as needed
    
    def _export_yaml_config(self, filepath: str, scenario: Dict[str, Any]):
        """Export scenario configuration as YAML."""
        import yaml
        
        with open(filepath, 'w') as f:
            yaml.dump(scenario, f, default_flow_style=False, sort_keys=False)