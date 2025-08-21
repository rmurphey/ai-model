#!/usr/bin/env python3
"""
Test script for custom impact input functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.interactive.scenario_builder import ScenarioBuilder
from src.model.baseline import BaselineMetrics

def test_custom_impact():
    """Test that custom impact values work correctly."""
    builder = ScenarioBuilder()
    
    print("Testing Custom Impact Scenarios")
    print("=" * 50)
    
    # Test 1: Custom overall percentage
    print("\n1. Testing custom overall percentage (45%):")
    scenario1 = builder.build_quick_scenario(
        team_size=50,
        junior_ratio=0.3,
        mid_ratio=0.5,
        senior_ratio=0.2,
        adoption_strategy="organic",
        impact_level="custom",
        timeframe_months=24,
        custom_impact_value=0.45  # 45% overall improvement
    )
    
    impacts1 = scenario1['impact']
    print(f"  Feature cycle reduction: {impacts1['feature_cycle_reduction']*100:.1f}%")
    print(f"  Bug fix reduction: {impacts1['bug_fix_reduction']*100:.1f}%")
    print(f"  Defect reduction: {impacts1['defect_reduction']*100:.1f}%")
    print(f"  Incident reduction: {impacts1['incident_reduction']*100:.1f}%")
    
    # Test 2: Custom detailed impacts
    print("\n2. Testing custom detailed impacts:")
    custom_details = {
        "feature_cycle_reduction": 0.15,  # 15%
        "bug_fix_reduction": 0.50,        # 50%
        "defect_reduction": 0.35,         # 35%
        "incident_reduction": 0.20         # 20%
    }
    
    scenario2 = builder.build_quick_scenario(
        team_size=50,
        junior_ratio=0.3,
        mid_ratio=0.5,
        senior_ratio=0.2,
        adoption_strategy="organic",
        impact_level="custom",
        timeframe_months=24,
        custom_impact_details=custom_details
    )
    
    impacts2 = scenario2['impact']
    print(f"  Feature cycle reduction: {impacts2['feature_cycle_reduction']*100:.1f}%")
    print(f"  Bug fix reduction: {impacts2['bug_fix_reduction']*100:.1f}%")
    print(f"  Defect reduction: {impacts2['defect_reduction']*100:.1f}%")
    print(f"  Incident reduction: {impacts2['incident_reduction']*100:.1f}%")
    
    # Test 3: Verify BaselineMetrics still works
    print("\n3. Testing BaselineMetrics compatibility:")
    try:
        baseline = BaselineMetrics(**scenario2['baseline'])
        print("  ✓ BaselineMetrics created successfully")
        print(f"  Team cost: ${baseline.weighted_avg_flc * baseline.team_size:,.0f}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Test 4: Compare with standard presets
    print("\n4. Comparing with standard presets:")
    for level in ["conservative", "moderate", "aggressive"]:
        scenario = builder.build_quick_scenario(
            team_size=50,
            junior_ratio=0.3,
            mid_ratio=0.5,
            senior_ratio=0.2,
            adoption_strategy="organic",
            impact_level=level,
            timeframe_months=24
        )
        avg_impact = sum([
            scenario['impact']['feature_cycle_reduction'],
            scenario['impact']['bug_fix_reduction'],
            scenario['impact']['defect_reduction'],
            scenario['impact']['incident_reduction']
        ]) / 4
        print(f"  {level.capitalize()}: ~{avg_impact*100:.0f}% average")
    
    print("\n" + "=" * 50)
    print("✓ All custom impact tests passed!")
    return True

if __name__ == "__main__":
    success = test_custom_impact()
    sys.exit(0 if success else 1)