"""
Interactive wizard for AI Impact Model scenario creation and analysis.
Guides users through scenario definition, execution, and refinement.
"""

import os
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from .prompts import (
    get_text_input, 
    get_numeric_input, 
    select_from_menu,
    display_header,
    display_results_table,
    display_info,
    display_warning,
    display_success,
    confirm_action
)
from .scenario_builder import ScenarioBuilder
from .results_explorer import ResultsExplorer


class InteractiveWizard:
    """Main interactive wizard for scenario creation and analysis."""
    
    def __init__(self):
        """Initialize the interactive wizard."""
        self.builder = ScenarioBuilder()
        self.explorer = ResultsExplorer()
        self.session_data = {
            'scenarios': {},
            'results': {},
            'history': []
        }
        
    def run(self):
        """Main entry point for the interactive wizard."""
        display_header("AI Impact Model Interactive Mode")
        
        while True:
            choice = self._main_menu()
            
            if choice == '1':
                self._quick_setup()
            elif choice == '2':
                self._detailed_setup()
            elif choice == '3':
                self._load_existing_scenario()
            elif choice == '4':
                self._use_template()
            elif choice == '5':
                self._view_session_history()
            elif choice == 'q':
                if self._confirm_exit():
                    display_info("Thank you for using AI Impact Model!")
                    break
            else:
                display_warning("Invalid choice. Please try again.")
    
    def _main_menu(self) -> str:
        """Display main menu and get user choice."""
        print("\nChoose your path:")
        options = [
            ("1", "Quick Setup (5 questions)"),
            ("2", "Detailed Setup (15 questions)"),
            ("3", "Load existing scenario"),
            ("4", "Use template"),
            ("5", "View session history"),
            ("q", "Quit")
        ]
        
        for key, desc in options:
            print(f"  {key}. {desc}")
        
        return get_text_input("\nSelection", default="1").lower()
    
    def _quick_setup(self):
        """Quick setup with essential parameters only."""
        display_header("Quick Setup")
        
        # Collect essential parameters
        display_info("[Question 1/5] Company Profile")
        team_size = get_numeric_input("What is your current team size?", default=50, min_val=1, max_val=10000, integer_only=True)
        
        display_info("\n[Question 2/5] Team Composition")
        composition = select_from_menu(
            "Select your team composition:",
            [
                ("Balanced", "30% junior, 50% mid, 20% senior"),
                ("Junior-heavy", "50% junior, 35% mid, 15% senior"),
                ("Senior-heavy", "20% junior, 40% mid, 40% senior"),
                ("Custom", "Enter custom percentages")
            ]
        )
        
        if composition == "Custom":
            junior_ratio = get_numeric_input("Junior percentage", default=30, min_val=0, max_val=100) / 100
            mid_ratio = get_numeric_input("Mid-level percentage", default=50, min_val=0, max_val=100) / 100
            senior_ratio = get_numeric_input("Senior percentage", default=20, min_val=0, max_val=100) / 100
            
            # Normalize if they don't sum to 100%
            total = junior_ratio + mid_ratio + senior_ratio
            if abs(total - 1.0) > 0.01:
                display_warning(f"Ratios sum to {total*100:.1f}%. Normalizing to 100%.")
                junior_ratio /= total
                mid_ratio /= total
                senior_ratio /= total
        else:
            ratios = {
                "Balanced": (0.3, 0.5, 0.2),
                "Junior-heavy": (0.5, 0.35, 0.15),
                "Senior-heavy": (0.2, 0.4, 0.4)
            }
            junior_ratio, mid_ratio, senior_ratio = ratios[composition]
        
        display_info("\n[Question 3/5] Adoption Strategy")
        strategy = select_from_menu(
            "Select your adoption strategy:",
            [
                ("Organic", "Bottom-up, developer-driven adoption"),
                ("Mandated", "Top-down, management-driven rollout"),
                ("Hybrid", "Mixed approach with pilot groups")
            ]
        )
        
        display_info("\n[Question 4/5] Expected Impact")
        impact_level = select_from_menu(
            "What level of impact do you expect?",
            [
                ("Conservative", "10-20% improvements"),
                ("Moderate", "20-35% improvements"),
                ("Aggressive", "35-50% improvements"),
                ("Custom", "Enter custom improvement percentage")
            ]
        )
        
        # Handle custom impact level
        custom_impact_value = None
        custom_impact_details = None
        if impact_level == "Custom":
            display_info("\nCustom Impact Configuration")
            detail_choice = select_from_menu(
                "How would you like to specify improvements?",
                [
                    ("Overall", "Single overall improvement percentage"),
                    ("Detailed", "Specify individual areas (time, quality, etc.)")
                ]
            )
            
            if detail_choice == "Overall":
                custom_impact_value = get_numeric_input(
                    "Enter expected overall improvement percentage",
                    default=30,
                    min_val=5,
                    max_val=70
                ) / 100  # Convert percentage to decimal
            else:
                # Get specific improvements for different areas
                display_info("\nSpecify improvements for each area:")
                custom_impact_details = {
                    "feature_cycle_reduction": get_numeric_input(
                        "Feature delivery speed improvement (%)",
                        default=30,
                        min_val=0,
                        max_val=70
                    ) / 100,
                    "bug_fix_reduction": get_numeric_input(
                        "Bug fix speed improvement (%)",
                        default=40,
                        min_val=0,
                        max_val=80
                    ) / 100,
                    "defect_reduction": get_numeric_input(
                        "Defect rate reduction (%)",
                        default=25,
                        min_val=0,
                        max_val=60
                    ) / 100,
                    "incident_reduction": get_numeric_input(
                        "Production incident reduction (%)",
                        default=30,
                        min_val=0,
                        max_val=70
                    ) / 100
                }
        
        display_info("\n[Question 5/5] Timeframe")
        timeframe = get_numeric_input(
            "Analysis timeframe in months",
            default=24,
            min_val=6,
            max_val=60,
            integer_only=True
        )
        
        # Build scenario from inputs
        scenario_name = f"quick_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        scenario = self.builder.build_quick_scenario(
            team_size=team_size,
            junior_ratio=junior_ratio,
            mid_ratio=mid_ratio,
            senior_ratio=senior_ratio,
            adoption_strategy=strategy.lower(),
            impact_level=impact_level.lower(),
            timeframe_months=timeframe,
            custom_impact_value=custom_impact_value,
            custom_impact_details=custom_impact_details
        )
        
        # Store and run scenario
        self.session_data['scenarios'][scenario_name] = scenario
        self._run_and_explore_scenario(scenario_name, scenario)
    
    def _detailed_setup(self):
        """Detailed setup with all parameters."""
        display_header("Detailed Setup")
        
        # Company Profile Section
        display_info("=== Company Profile ===")
        team_size = get_numeric_input("Team size", default=50, min_val=1, max_val=10000, integer_only=True)
        
        junior_ratio = get_numeric_input("Junior developers (%)", default=30, min_val=0, max_val=100) / 100
        mid_ratio = get_numeric_input("Mid-level developers (%)", default=50, min_val=0, max_val=100) / 100
        senior_ratio = get_numeric_input("Senior developers (%)", default=20, min_val=0, max_val=100) / 100
        
        # Normalize ratios
        total = junior_ratio + mid_ratio + senior_ratio
        if abs(total - 1.0) > 0.01:
            display_warning(f"Ratios sum to {total*100:.1f}%. Normalizing to 100%.")
            junior_ratio /= total
            mid_ratio /= total
            senior_ratio /= total
        
        # Current Metrics Section
        display_info("\n=== Current Development Metrics ===")
        avg_feature_cycle = get_numeric_input(
            "Average feature cycle time (days)",
            default=30,
            min_val=1,
            max_val=365
        )
        
        avg_bug_fix = get_numeric_input(
            "Average bug fix time (hours)",
            default=8,
            min_val=0.5,
            max_val=168
        )
        
        monthly_incidents = get_numeric_input(
            "Monthly production incidents",
            default=5,
            min_val=0,
            max_val=100
        )
        
        defect_rate = get_numeric_input(
            "Defect rate per KLOC",
            default=15,
            min_val=0,
            max_val=100
        )
        
        # Adoption Parameters Section
        display_info("\n=== Adoption Parameters ===")
        adoption_strategy = select_from_menu(
            "Adoption strategy:",
            [
                ("organic", "Bottom-up, developer-driven"),
                ("mandated", "Top-down, management-driven"),
                ("grassroots", "Champion-led with viral spread"),
                ("pilot", "Pilot group then expansion")
            ]
        )
        
        plateau_adoption = get_numeric_input(
            "Expected plateau adoption rate (%)",
            default=70,
            min_val=10,
            max_val=100
        ) / 100
        
        time_to_plateau = get_numeric_input(
            "Months to reach adoption plateau",
            default=12,
            min_val=1,
            max_val=36
        )
        
        dropout_rate = get_numeric_input(
            "Monthly dropout rate (%)",
            default=2,
            min_val=0,
            max_val=10
        ) / 100
        
        # Impact Expectations Section
        display_info("\n=== Expected Improvements ===")
        feature_cycle_reduction = get_numeric_input(
            "Feature cycle time reduction (%)",
            default=30,
            min_val=0,
            max_val=70
        ) / 100
        
        bug_fix_reduction = get_numeric_input(
            "Bug fix time reduction (%)",
            default=40,
            min_val=0,
            max_val=80
        ) / 100
        
        defect_reduction = get_numeric_input(
            "Defect rate reduction (%)",
            default=25,
            min_val=0,
            max_val=60
        ) / 100
        
        incident_reduction = get_numeric_input(
            "Incident rate reduction (%)",
            default=30,
            min_val=0,
            max_val=70
        ) / 100
        
        # Cost Structure Section
        display_info("\n=== Cost Structure ===")
        cost_per_seat = get_numeric_input(
            "Cost per seat per month ($)",
            default=30,
            min_val=0,
            max_val=500
        )
        
        avg_tokens_per_user = get_numeric_input(
            "Average tokens per user per month (millions)",
            default=2,
            min_val=0,
            max_val=100
        )
        
        training_cost = get_numeric_input(
            "One-time training cost per user ($)",
            default=500,
            min_val=0,
            max_val=10000
        )
        
        # Analysis Parameters
        display_info("\n=== Analysis Parameters ===")
        timeframe = get_numeric_input(
            "Analysis timeframe (months)",
            default=24,
            min_val=6,
            max_val=60,
            integer_only=True
        )
        
        # Build detailed scenario
        scenario_name = f"detailed_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        scenario = self.builder.build_detailed_scenario(
            # Baseline parameters
            team_size=team_size,
            junior_ratio=junior_ratio,
            mid_ratio=mid_ratio,
            senior_ratio=senior_ratio,
            avg_feature_cycle_days=avg_feature_cycle,
            avg_bug_fix_hours=avg_bug_fix,
            monthly_incidents=monthly_incidents,
            defect_rate_per_kloc=defect_rate,
            
            # Adoption parameters
            adoption_strategy=adoption_strategy,
            plateau_adoption_rate=plateau_adoption,
            time_to_plateau_months=time_to_plateau,
            monthly_dropout_rate=dropout_rate,
            
            # Impact parameters
            feature_cycle_reduction=feature_cycle_reduction,
            bug_fix_reduction=bug_fix_reduction,
            defect_reduction=defect_reduction,
            incident_reduction=incident_reduction,
            
            # Cost parameters
            cost_per_seat_month=cost_per_seat,
            avg_tokens_million_per_user_month=avg_tokens_per_user,
            training_cost_per_user=training_cost,
            
            # Timeframe
            timeframe_months=timeframe
        )
        
        # Store and run scenario
        self.session_data['scenarios'][scenario_name] = scenario
        self._run_and_explore_scenario(scenario_name, scenario)
    
    def _load_existing_scenario(self):
        """Load an existing scenario from available options."""
        display_header("Load Existing Scenario")
        
        from ..scenarios.scenario_loader import ScenarioLoader
        loader = ScenarioLoader()
        available = loader.list_available_scenarios()
        
        if not available:
            display_warning("No scenarios available.")
            return
        
        # Build menu options
        options = []
        for i, name in enumerate(available, 1):
            info = loader.get_scenario_info(name)
            desc = f"{info['name']} (Team: {info['team_size']}, {info['timeframe_months']} months)"
            options.append((str(i), name, desc))
        
        print("\nAvailable scenarios:")
        for num, name, desc in options:
            print(f"  {num}. {desc}")
        
        choice = get_text_input("\nSelect scenario number (or 'b' to go back)", default="1")
        
        if choice.lower() == 'b':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available):
                scenario_name = available[idx]
                scenario = loader.load_scenario(scenario_name)
                self.session_data['scenarios'][scenario_name] = scenario
                self._run_and_explore_scenario(scenario_name, scenario)
            else:
                display_warning("Invalid selection.")
        except ValueError:
            display_warning("Invalid input.")
    
    def _use_template(self):
        """Use a predefined template scenario."""
        display_header("Use Template")
        
        templates = [
            ("startup", "Fast-moving Startup", "Small team, rapid adoption, high risk"),
            ("enterprise", "Enterprise Software", "Large team, careful rollout, moderate impact"),
            ("fintech", "Financial Services", "Medium team, compliance-aware, conservative"),
            ("ecommerce", "E-commerce/SaaS", "Growth-focused, balanced approach")
        ]
        
        print("\nAvailable templates:")
        for i, (key, name, desc) in enumerate(templates, 1):
            print(f"  {i}. {name}")
            print(f"     {desc}")
        
        choice = get_text_input("\nSelect template number", default="1")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(templates):
                template_key, template_name, _ = templates[idx]
                scenario = self.builder.build_from_template(template_key)
                scenario_name = f"template_{template_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.session_data['scenarios'][scenario_name] = scenario
                display_success(f"Using template: {template_name}")
                self._run_and_explore_scenario(scenario_name, scenario)
            else:
                display_warning("Invalid selection.")
        except ValueError:
            display_warning("Invalid input.")
    
    def _run_and_explore_scenario(self, name: str, scenario: Dict[str, Any]):
        """Run a scenario and enter exploration mode."""
        display_info(f"\nRunning analysis for: {name}")
        
        # Import and run the model
        from main import AIImpactModel
        
        # Try to initialize model with legacy scenario file first
        try:
            model = AIImpactModel(scenario_file="src/scenarios/scenarios.yaml")
        except:
            # Fall back to directory-based loading
            try:
                model = AIImpactModel(scenario_file="src/scenarios")
            except:
                # Create a minimal model without loading scenarios
                model = AIImpactModel.__new__(AIImpactModel)
                model.scenarios = {}
        
        # Temporarily inject our scenario
        model.scenarios[name] = scenario
        
        try:
            results = model.run_scenario(name)
            self.session_data['results'][name] = results
            self.session_data['history'].append({
                'timestamp': datetime.now(),
                'scenario': name,
                'type': 'run'
            })
            
            display_success("Analysis complete!")
            
            # Enter exploration mode
            self.explorer.explore(name, scenario, results, self)
            
        except Exception as e:
            display_warning(f"Error running scenario: {e}")
    
    def _view_session_history(self):
        """View the history of scenarios run in this session."""
        display_header("Session History")
        
        if not self.session_data['history']:
            display_info("No scenarios run yet in this session.")
            return
        
        print("\nScenarios run this session:")
        for i, entry in enumerate(self.session_data['history'], 1):
            timestamp = entry['timestamp'].strftime("%H:%M:%S")
            print(f"  {i}. [{timestamp}] {entry['scenario']} ({entry['type']})")
        
        if self.session_data['results']:
            print("\n" + "="*50)
            choice = get_text_input("\nEnter number to view details (or 'b' to go back)", default="b")
            
            if choice.lower() != 'b':
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(self.session_data['history']):
                        entry = self.session_data['history'][idx]
                        scenario_name = entry['scenario']
                        if scenario_name in self.session_data['results']:
                            results = self.session_data['results'][scenario_name]
                            scenario = self.session_data['scenarios'][scenario_name]
                            self.explorer.explore(scenario_name, scenario, results, self)
                except ValueError:
                    display_warning("Invalid input.")
    
    def _confirm_exit(self) -> bool:
        """Confirm before exiting."""
        if self.session_data['history']:
            return confirm_action("You have unsaved work. Are you sure you want to exit?")
        return True
    
    def refine_scenario(self, name: str, scenario: Dict[str, Any], sensitivity_params: List[str]):
        """Refine a scenario based on sensitivity analysis."""
        display_header("Scenario Refinement")
        
        display_info("High sensitivity parameters identified:")
        for i, param in enumerate(sensitivity_params[:5], 1):
            print(f"  {i}. {param}")
        
        if confirm_action("\nWould you like to adjust these parameters?"):
            # Create a copy for refinement
            refined_scenario = scenario.copy()
            refined_name = f"{name}_refined_{datetime.now().strftime('%H%M%S')}"
            
            for param in sensitivity_params[:3]:  # Refine top 3
                current = self._get_param_value(scenario, param)
                display_info(f"\nCurrent {param}: {current}")
                
                if isinstance(current, (int, float)):
                    new_value = get_numeric_input(
                        f"New value for {param}",
                        default=current,
                        min_val=current * 0.5,
                        max_val=current * 1.5
                    )
                    self._set_param_value(refined_scenario, param, new_value)
            
            # Store and run refined scenario
            self.session_data['scenarios'][refined_name] = refined_scenario
            self._run_and_explore_scenario(refined_name, refined_scenario)
    
    def _get_param_value(self, scenario: Dict[str, Any], param_path: str) -> Any:
        """Get a parameter value from nested dictionary."""
        parts = param_path.split('.')
        value = scenario
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
    
    def _set_param_value(self, scenario: Dict[str, Any], param_path: str, value: Any):
        """Set a parameter value in nested dictionary."""
        parts = param_path.split('.')
        target = scenario
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value