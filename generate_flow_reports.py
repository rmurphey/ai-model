#!/usr/bin/env python3
"""
Generate Reinertsen product development flow analysis reports.
Focuses on queue economics, batch sizes, and cost of delay.
"""

import sys
import json
from datetime import datetime
from pathlib import Path
import numpy as np

from src.model.delivery_pipeline import create_standard_pipeline
from src.model.queue_model import BatchSizeOptimizer, apply_littles_law


def analyze_flow_scenario(scenario_name, team_size, feature_value=10000, 
                         urgency_factor=0.1, test_automation=0.5,
                         deployment_freq="weekly"):
    """Analyze flow economics for a specific scenario."""
    
    # Create pipeline
    pipeline = create_standard_pipeline(
        team_size=team_size,
        test_automation=test_automation,
        deployment_frequency=deployment_freq
    )
    
    # Calculate flow metrics
    flow_efficiency = pipeline.calculate_flow_efficiency()
    lead_time_data = pipeline.calculate_lead_time(0.5)  # 50% AI adoption baseline
    total_lead_time = lead_time_data['total_lead_time_days']
    
    # Calculate throughput metrics
    throughput_data = pipeline.calculate_throughput(0.5)
    stage_throughputs = throughput_data['stage_throughputs']
    bottleneck_throughput = throughput_data['throughput_per_day']
    
    # Queue analysis using Little's Law
    queue_metrics = {}
    total_queue_cost = 0
    cost_of_delay_per_day = feature_value * urgency_factor
    
    for stage_name, throughput in stage_throughputs.items():
        arrival_rate = bottleneck_throughput / 30  # per day
        service_rate = throughput / 30  # per day
        
        if service_rate > arrival_rate and arrival_rate > 0:
            utilization = arrival_rate / service_rate
            # M/M/1 queue calculations
            avg_queue_length = (utilization ** 2) / (1 - utilization) if utilization < 1 else float('inf')
            avg_wait_time = avg_queue_length / arrival_rate if arrival_rate > 0 else 0
            queue_cost = avg_queue_length * cost_of_delay_per_day if avg_queue_length != float('inf') else 999999
        else:
            avg_queue_length = float('inf')
            avg_wait_time = float('inf')
            queue_cost = 999999
            utilization = 1.0
        
        queue_metrics[stage_name] = {
            'utilization': utilization,
            'avg_queue_length': avg_queue_length,
            'avg_wait_time': avg_wait_time,
            'daily_cost': queue_cost
        }
        
        if queue_cost != 999999:
            total_queue_cost += queue_cost
    
    # Batch size analysis
    batch_optimizer = BatchSizeOptimizer()
    batch_analysis = {}
    
    current_batch_sizes = {
        'requirements': 5,
        'coding': 1,
        'code_review': 3,
        'testing': 2,
        'deployment': 10 if deployment_freq == "weekly" else 5
    }
    
    for stage, current_batch in current_batch_sizes.items():
        transaction_cost = team_size * 50  # Cost to start a batch
        holding_cost = cost_of_delay_per_day / current_batch
        demand_rate = bottleneck_throughput / 30
        
        optimal_batch = batch_optimizer.calculate_optimal_batch_size(
            transaction_cost=transaction_cost,
            holding_cost_per_item=holding_cost,
            demand_rate=demand_rate,
            variability=1.2
        )
        
        current_delay_cost = batch_optimizer.calculate_batch_delay_cost(
            batch_size=current_batch,
            item_urgency=cost_of_delay_per_day,
            processing_time=1.0
        )
        
        optimal_delay_cost = batch_optimizer.calculate_batch_delay_cost(
            batch_size=optimal_batch,
            item_urgency=cost_of_delay_per_day,
            processing_time=1.0
        )
        
        batch_analysis[stage] = {
            'current_batch': current_batch,
            'optimal_batch': optimal_batch,
            'current_delay_cost': current_delay_cost,
            'optimal_delay_cost': optimal_delay_cost,
            'savings': current_delay_cost - optimal_delay_cost
        }
    
    # WIP analysis using Little's Law
    current_wip = team_size  # Assume no WIP limits
    optimal_wip = apply_littles_law(
        avg_wip=current_wip,
        throughput=bottleneck_throughput / 30
    )
    
    # Variability impact
    variability_scenarios = []
    for cv_name, cv_value in [("Low", 0.5), ("Typical", 1.0), ("High", 1.5), ("Chaotic", 2.0)]:
        base_utilization = 0.8
        queue_multiplier = 1 + cv_value ** 2
        est_queue_length = queue_multiplier * (base_utilization ** 2) / (1 - base_utilization)
        est_wait_time = est_queue_length / (bottleneck_throughput / 30) if bottleneck_throughput > 0 else 0
        
        variability_scenarios.append({
            'scenario': cv_name,
            'coefficient_of_variation': cv_value,
            'queue_length': est_queue_length,
            'wait_time': est_wait_time,
            'daily_cost': est_queue_length * cost_of_delay_per_day
        })
    
    # Build report
    report = {
        'scenario_name': scenario_name,
        'timestamp': datetime.now().isoformat(),
        'configuration': {
            'team_size': team_size,
            'feature_value': feature_value,
            'urgency_factor': urgency_factor,
            'cost_of_delay_per_day': cost_of_delay_per_day,
            'test_automation': test_automation,
            'deployment_frequency': deployment_freq
        },
        'flow_metrics': {
            'flow_efficiency': flow_efficiency,
            'total_lead_time': total_lead_time,
            'value_add_time': total_lead_time * flow_efficiency,
            'wait_time': total_lead_time * (1 - flow_efficiency),
            'throughput_per_month': bottleneck_throughput
        },
        'queue_analysis': {
            'stage_queues': queue_metrics,
            'total_daily_queue_cost': total_queue_cost,
            'monthly_queue_cost': total_queue_cost * 30,
            'queue_cost_per_feature': total_queue_cost / bottleneck_throughput if bottleneck_throughput > 0 else 0
        },
        'batch_size_optimization': batch_analysis,
        'wip_recommendations': {
            'current_wip': current_wip,
            'recommended_wip': optimal_wip,
            'lead_time_impact': f"{optimal_wip:.1f} days with optimal WIP"
        },
        'variability_impact': variability_scenarios,
        'economic_summary': {
            'monthly_delay_cost': total_lead_time * cost_of_delay_per_day * bottleneck_throughput,
            'monthly_queue_cost': total_queue_cost * 30,
            'potential_batch_savings': sum(b['savings'] for b in batch_analysis.values()) * 30,
            'flow_improvement_potential': (1 - flow_efficiency) * 100  # % improvement possible
        },
        'reinertsen_principles': generate_reinertsen_recommendations(
            flow_efficiency, total_queue_cost, feature_value, batch_analysis
        )
    }
    
    return report


def generate_reinertsen_recommendations(flow_efficiency, queue_cost, feature_value, batch_analysis):
    """Generate recommendations based on Reinertsen's principles."""
    recommendations = []
    
    # Principle 1: Economic decisions
    if queue_cost > feature_value:
        recommendations.append({
            'principle': 'Economic Focus',
            'issue': f'Queue costs (${queue_cost:.0f}/day) exceed feature value',
            'recommendation': 'Implement cost of delay prioritization',
            'priority': 'Critical'
        })
    
    # Principle 2: Queue management
    if flow_efficiency < 0.25:
        recommendations.append({
            'principle': 'Queue Management',
            'issue': f'Flow efficiency only {flow_efficiency:.1%}',
            'recommendation': 'Focus on queue reduction over resource efficiency',
            'priority': 'High'
        })
    
    # Principle 3: Batch size
    large_batches = [stage for stage, data in batch_analysis.items() 
                    if data['current_batch'] > data['optimal_batch'] * 2]
    if large_batches:
        recommendations.append({
            'principle': 'Batch Size Reduction',
            'issue': f'Large batches in {", ".join(large_batches)}',
            'recommendation': 'Reduce batch sizes to improve flow',
            'priority': 'High'
        })
    
    # Principle 4: WIP constraints
    recommendations.append({
        'principle': 'WIP Constraints',
        'issue': 'No WIP limits currently applied',
        'recommendation': 'Implement WIP limits using Little\'s Law',
        'priority': 'Medium'
    })
    
    # Principle 5: Feedback
    recommendations.append({
        'principle': 'Accelerate Feedback',
        'issue': 'Long feedback loops increase risk',
        'recommendation': 'Implement faster feedback mechanisms',
        'priority': 'Medium'
    })
    
    # Principle 6: Variability
    recommendations.append({
        'principle': 'Manage Variability',
        'issue': 'High software development variability',
        'recommendation': 'Use smaller batches and safety capacity',
        'priority': 'Medium'
    })
    
    return recommendations


def generate_all_flow_reports():
    """Generate flow reports for key scenarios."""
    
    scenarios = [
        # Different team sizes
        {'name': 'small_team_flow', 'team_size': 10, 'urgency': 0.05, 'automation': 0.3},
        {'name': 'medium_team_flow', 'team_size': 50, 'urgency': 0.1, 'automation': 0.5},
        {'name': 'large_team_flow', 'team_size': 200, 'urgency': 0.15, 'automation': 0.7},
        
        # Different urgency levels
        {'name': 'low_urgency', 'team_size': 50, 'urgency': 0.02, 'automation': 0.5},
        {'name': 'high_urgency', 'team_size': 50, 'urgency': 0.2, 'automation': 0.5},
        
        # Different automation levels
        {'name': 'low_automation', 'team_size': 50, 'urgency': 0.1, 'automation': 0.2},
        {'name': 'high_automation', 'team_size': 50, 'urgency': 0.1, 'automation': 0.9},
        
        # Different deployment frequencies
        {'name': 'daily_deployment', 'team_size': 50, 'urgency': 0.1, 'automation': 0.6, 'deploy': 'daily'},
        {'name': 'monthly_deployment', 'team_size': 50, 'urgency': 0.1, 'automation': 0.6, 'deploy': 'monthly'},
        
        # Edge case
        {'name': 'critical_project', 'team_size': 30, 'urgency': 0.25, 'automation': 0.8, 'value': 50000}
    ]
    
    # Create output directory
    output_dir = Path('reports/flow_analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_reports = []
    summary_data = []
    
    print(f"Generating flow analysis reports for {len(scenarios)} scenarios...")
    
    for scenario in scenarios:
        print(f"  Analyzing {scenario['name']}...")
        
        report = analyze_flow_scenario(
            scenario['name'],
            scenario['team_size'],
            feature_value=scenario.get('value', 10000),
            urgency_factor=scenario['urgency'],
            test_automation=scenario['automation'],
            deployment_freq=scenario.get('deploy', 'weekly')
        )
        
        if report:
            # Save individual report
            report_file = output_dir / f"{scenario['name']}_flow_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            all_reports.append(report)
            
            # Extract summary
            summary_data.append({
                'scenario': scenario['name'],
                'team_size': scenario['team_size'],
                'flow_efficiency': report['flow_metrics']['flow_efficiency'],
                'lead_time': report['flow_metrics']['total_lead_time'],
                'monthly_queue_cost': report['queue_analysis']['monthly_queue_cost'],
                'batch_savings': report['economic_summary']['potential_batch_savings'],
                'improvement_potential': report['economic_summary']['flow_improvement_potential']
            })
    
    # Generate summary
    generate_flow_summary(summary_data, all_reports, output_dir)
    
    print(f"\nFlow reports generated in {output_dir}/")
    print(f"  - {len(all_reports)} individual flow reports")
    print(f"  - 1 flow economics summary")
    
    return all_reports


def generate_flow_summary(summary_data, all_reports, output_dir):
    """Generate summary of flow analysis."""
    
    md_content = """# Product Development Flow Analysis - Summary

## Reinertsen's Principles Applied

This analysis applies Donald Reinertsen's product development flow principles to reveal hidden economic costs in software delivery pipelines.

## Key Economic Findings

### Queue Costs (Usually Invisible)

| Scenario | Team Size | Flow Efficiency | Lead Time | Monthly Queue Cost | Potential Savings |
|----------|-----------|-----------------|-----------|-------------------|-------------------|
"""
    
    # Sort by queue cost
    sorted_data = sorted(summary_data, key=lambda x: x['monthly_queue_cost'], reverse=True)
    
    for item in sorted_data:
        md_content += f"| {item['scenario']} | {item['team_size']} | {item['flow_efficiency']:.1%} | {item['lead_time']:.1f} days | ${item['monthly_queue_cost']:,.0f} | ${item['batch_savings']:,.0f} |\n"
    
    # Calculate averages
    avg_flow_efficiency = np.mean([d['flow_efficiency'] for d in summary_data])
    avg_queue_cost = np.mean([d['monthly_queue_cost'] for d in summary_data])
    total_batch_savings = sum(d['batch_savings'] for d in summary_data)
    
    md_content += f"""
### Economic Impact Summary

- **Average Flow Efficiency**: {avg_flow_efficiency:.1%} (industry typical: 15-25%)
- **Average Monthly Queue Cost**: ${avg_queue_cost:,.0f} (often invisible to management)
- **Total Batch Size Savings Potential**: ${total_batch_savings:,.0f}/month
- **Average Improvement Potential**: {np.mean([d['improvement_potential'] for d in summary_data]):.1f}%

## Reinertsen's Eight Principles - Key Insights

### 1. Economic Decisions
Queue costs often exceed feature value, yet remain invisible in traditional accounting.

### 2. Queue Management  
Queues are the root cause of poor product development economics. Average queue cost: ${avg_queue_cost:,.0f}/month.

### 3. Batch Size Reduction
One of the cheapest, most powerful improvements. Reduces variability, accelerates feedback, reduces risk.

### 4. WIP Constraints
Apply Little's Law: Lead Time = WIP / Throughput. Limiting WIP reduces lead time.

### 5. Accelerate Feedback
Faster feedback enables smaller batches, reducing risk and improving quality.

### 6. Manage Variability
Software has high variability. Use smaller batches and safety capacity to manage it.

### 7. Fast Control Loops
Decentralized control with fast local feedback loops improves responsiveness.

### 8. Architecture & Organization
Align system architecture with team organization for optimal flow.

## Critical Recommendations

1. **Make Queue Costs Visible** - Hidden costs often exceed visible costs by 10x
2. **Reduce Batch Sizes** - Immediate impact with minimal investment
3. **Implement WIP Limits** - Use Little's Law to set optimal limits
4. **Measure Flow Efficiency** - Track value-add time vs wait time
5. **Prioritize by Cost of Delay** - Economic decision-making framework

---
*Analysis based on Reinertsen's "The Principles of Product Development Flow"*
"""
    
    # Save summary
    summary_file = output_dir / 'flow_economics_summary.md'
    with open(summary_file, 'w') as f:
        f.write(md_content)


if __name__ == "__main__":
    reports = generate_all_flow_reports()
    print(f"\n✅ Successfully generated {len(reports)} flow analysis reports")