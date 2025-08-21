#!/usr/bin/env python3
"""
Test script to verify interactive mode fixes.
Tests the core functionality without requiring terminal interaction.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.interactive.scenario_builder import ScenarioBuilder
from src.model.baseline import BaselineMetrics

def test_scenario_builder():
    """Test that scenario builder creates valid BaselineMetrics parameters."""
    builder = ScenarioBuilder()
    
    print("Testing Quick Scenario Build...")
    scenario = builder.build_quick_scenario(
        team_size=50,
        junior_ratio=0.3,
        mid_ratio=0.5,
        senior_ratio=0.2,
        adoption_strategy="organic",
        impact_level="moderate",
        timeframe_months=24
    )
    
    # Verify baseline parameters are correct
    baseline_params = scenario['baseline']
    print(f"✓ Team size: {baseline_params['team_size']}")
    print(f"✓ Junior FLC: ${baseline_params['junior_flc']:,.0f}")
    print(f"✓ Mid FLC: ${baseline_params['mid_flc']:,.0f}")
    print(f"✓ Senior FLC: ${baseline_params['senior_flc']:,.0f}")
    
    # Test creating BaselineMetrics with the parameters
    try:
        baseline = BaselineMetrics(**baseline_params)
        print("✓ Successfully created BaselineMetrics instance")
        print(f"  - Weighted average FLC: ${baseline.weighted_avg_flc:,.0f}")
        total_cost = baseline.weighted_avg_flc * baseline.team_size
        print(f"  - Total annual cost: ${total_cost:,.0f}")
    except Exception as e:
        print(f"✗ Failed to create BaselineMetrics: {e}")
        return False
    
    print("\nTesting Template Scenarios...")
    for template_key in ['startup', 'enterprise', 'fintech', 'ecommerce']:
        template = builder.build_from_template(template_key)
        try:
            baseline = BaselineMetrics(**template['baseline'])
            print(f"✓ {template['name']} template works")
        except Exception as e:
            print(f"✗ {template['name']} template failed: {e}")
            return False
    
    return True

def test_questionary_import():
    """Test that questionary is properly installed and importable."""
    try:
        import questionary
        print("✓ Questionary library is installed and importable")
        return True
    except ImportError as e:
        print(f"✗ Failed to import questionary: {e}")
        return False

def main():
    print("=" * 50)
    print("Testing Interactive Mode Fixes")
    print("=" * 50)
    print()
    
    # Test questionary import
    if not test_questionary_import():
        print("\nPlease install questionary: pip install questionary")
        sys.exit(1)
    
    print()
    
    # Test scenario builder
    if test_scenario_builder():
        print("\n" + "=" * 50)
        print("✓ All tests passed! Interactive mode should now work.")
        print("=" * 50)
        print("\nTo use interactive mode:")
        print("  python interactive.py")
        print("\nNote: Interactive mode requires a terminal environment.")
        print("If running through SSH or a script, use: python -u interactive.py")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()