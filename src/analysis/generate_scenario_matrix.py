#!/usr/bin/env python3
"""
Generate all 9 scenario combinations (3 company types x 3 adoption approaches)
"""

import yaml

def generate_scenario_matrix():
    """Generate all 9 combinations of company type and adoption approach"""
    
    # Define the three dimensions
    company_types = {
        'startup': {
            'profile': 'startup',
            'cost_scenario': 'startup',
            'timeframe': 24,
            'description': '10-person startup'
        },
        'enterprise': {
            'profile': 'enterprise', 
            'cost_scenario': 'enterprise',
            'timeframe': 36,
            'description': '50-person enterprise'
        },
        'scaleup': {
            'profile': 'scale_up',
            'cost_scenario': 'aggressive',  # Scale-ups often spend more aggressively
            'timeframe': 24,
            'description': '25-person scale-up'
        }
    }
    
    adoption_approaches = {
        'conservative': {
            'adoption_scenario': 'organic',
            'impact_scenario': 'conservative',
            'description': 'cautious AI adoption'
        },
        'moderate': {
            'adoption_scenario': 'grassroots',  # Better adoption than organic
            'impact_scenario': 'moderate',
            'description': 'balanced adoption approach'
        },
        'aggressive': {
            'adoption_scenario': 'mandated',  # Top-down push for aggressive
            'impact_scenario': 'aggressive',
            'description': 'all-in on AI'
        }
    }
    
    scenarios = {}
    
    # Generate all 9 combinations
    for company_name, company_config in company_types.items():
        for adoption_name, adoption_config in adoption_approaches.items():
            scenario_key = f"{adoption_name}_{company_name}"
            
            scenarios[scenario_key] = {
                'name': f"{adoption_name.capitalize()} {company_name.capitalize()}",
                'description': f"{company_config['description']} with {adoption_config['description']}",
                'baseline': {
                    'profile': company_config['profile']
                },
                'adoption': {
                    'scenario': adoption_config['adoption_scenario']
                },
                'impact': {
                    'scenario': adoption_config['impact_scenario']
                },
                'costs': {
                    'scenario': company_config['cost_scenario']
                },
                'timeframe_months': company_config['timeframe']
            }
    
    # Add custom scenario at the end
    scenarios['custom'] = {
        'name': 'Custom Scenario',
        'description': 'User-defined parameters',
        'baseline': {
            'team_size': 30,
            'junior_ratio': 0.33,
            'mid_ratio': 0.50,
            'senior_ratio': 0.17,
            'junior_flc': 130000,
            'mid_flc': 170000,
            'senior_flc': 240000,
            'avg_feature_cycle_days': 20,
            'avg_bug_fix_hours': 10,
            'onboarding_days': 40,
            'defect_escape_rate': 4.0,
            'production_incidents_per_month': 3,
            'avg_incident_cost': 8000,
            'rework_percentage': 0.18,
            'new_feature_percentage': 0.45,
            'maintenance_percentage': 0.30,
            'tech_debt_percentage': 0.10,
            'meetings_percentage': 0.15,
            'avg_pr_review_hours': 2.5,
            'pr_rejection_rate': 0.20
        },
        'adoption': {
            'initial_adopters': 0.08,
            'early_adopters': 0.18,
            'early_majority': 0.34,
            'late_majority': 0.28,
            'laggards': 0.12,
            'training_effectiveness': 0.6,
            'peer_influence': 0.8,
            'management_mandate': 0.5,
            'initial_resistance': 0.35,
            'dropout_rate_month': 0.04,
            're_engagement_rate': 0.03,
            'initial_efficiency': 0.35,
            'learning_rate': 0.35,
            'plateau_efficiency': 0.88,
            'junior_adoption_multiplier': 1.4,
            'mid_adoption_multiplier': 1.1,
            'senior_adoption_multiplier': 0.75
        },
        'impact': {
            'feature_cycle_reduction': 0.28,
            'bug_fix_reduction': 0.38,
            'onboarding_reduction': 0.45,
            'pr_review_reduction': 0.55,
            'defect_reduction': 0.32,
            'incident_reduction': 0.28,
            'rework_reduction': 0.45,
            'feature_capacity_gain': 0.12,
            'tech_debt_capacity_gain': 0.06,
            'boilerplate_effectiveness': 0.88,
            'test_generation_effectiveness': 0.75,
            'documentation_effectiveness': 0.85,
            'code_review_effectiveness': 0.65,
            'debugging_effectiveness': 0.55,
            'junior_multiplier': 1.6,
            'mid_multiplier': 1.35,
            'senior_multiplier': 1.25
        },
        'costs': {
            'cost_per_seat_month': 40,
            'enterprise_discount': 0.15,
            'initial_tokens_per_dev_month': 350000,
            'token_price_per_million': 9,
            'token_price_decline_annual': 0.28,
            'token_growth_rate_monthly': 0.12,
            'token_plateau_month': 10,
            'initial_training_cost_per_dev': 1200,
            'ongoing_training_cost_annual': 300,
            'trainer_cost_per_day': 1800,
            'training_days_initial': 3,
            'training_days_ongoing_annual': 1.5,
            'infrastructure_setup': 15000,
            'infrastructure_monthly': 1500,
            'admin_overhead_percentage': 0.03,
            'context_switch_cost_month': 750,
            'bad_code_cleanup_percentage': 0.06,
            'security_review_overhead': 2,
            'pilot_budget': 25000,
            'ongoing_experimentation': 15000
        },
        'timeframe_months': 30
    }
    
    # Add task distributions
    scenarios['task_distributions'] = {
        'balanced': {
            'boilerplate': 0.15,
            'testing': 0.20,
            'documentation': 0.10,
            'code_review': 0.15,
            'debugging': 0.15,
            'feature_development': 0.20,
            'refactoring': 0.05
        },
        'feature_heavy': {
            'boilerplate': 0.10,
            'testing': 0.15,
            'documentation': 0.05,
            'code_review': 0.10,
            'debugging': 0.10,
            'feature_development': 0.40,
            'refactoring': 0.10
        },
        'maintenance_heavy': {
            'boilerplate': 0.05,
            'testing': 0.15,
            'documentation': 0.15,
            'code_review': 0.20,
            'debugging': 0.25,
            'feature_development': 0.10,
            'refactoring': 0.10
        }
    }
    
    # Add sensitivity analysis parameters
    scenarios['sensitivity'] = {
        'parameters': [
            'adoption_rate',
            'token_price',
            'feature_cycle_reduction',
            'defect_reduction',
            'cost_per_seat'
        ],
        'ranges': {
            'adoption_rate': [0.3, 0.9],
            'token_price': [5, 15],
            'feature_cycle_reduction': [0.1, 0.5],
            'defect_reduction': [0.1, 0.5],
            'cost_per_seat': [20, 100]
        }
    }
    
    return scenarios

if __name__ == "__main__":
    scenarios = generate_scenario_matrix()
    
    # Write to file
    with open('scenarios_matrix.yaml', 'w') as f:
        yaml.dump(scenarios, f, default_flow_style=False, sort_keys=False)
    
    print("Generated scenarios_matrix.yaml with all 9 combinations:")
    print("\nScenarios created:")
    for key in scenarios.keys():
        if key not in ['task_distributions', 'sensitivity', 'custom']:
            print(f"  - {key}: {scenarios[key]['description']}")
    
    print(f"\nTotal scenarios: {len([k for k in scenarios.keys() if k not in ['task_distributions', 'sensitivity']])}")