from main import AIImpactModel

model = AIImpactModel()

print('Updated Adoption Curves and Results:')
print('='*60)

for scenario in ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']:
    result = model.run_scenario(scenario)
    print(f'{scenario}:')
    print(f'  Peak adoption: {max(result["adoption"])*100:.1f}%')
    print(f'  Month 12 adoption: {result["adoption"][11]*100:.1f}%')
    print(f'  NPV: ${result["npv"]:,.0f}')
    print(f'  ROI: {result["roi_percent"]:.1f}%')
    print()