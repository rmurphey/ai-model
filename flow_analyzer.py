#!/usr/bin/env python3
"""
Product development flow analyzer based on Reinertsen's principles.
Focuses on queue management, batch size optimization, and cost of delay.
"""

import argparse
import sys
import numpy as np
from tabulate import tabulate
from typing import Dict, List, Tuple, Any

# Colors
try:
    from src.utils.colors import *
except ImportError:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'

from src.model.delivery_pipeline import create_standard_pipeline
from src.model.queue_model import QueueMetrics, BatchSizeOptimizer, apply_littles_law, calculate_flow_efficiency


def analyze_flow_economics(team_size: int,
                          feature_value: float = 10000,
                          urgency_factor: float = 0.1,  # Cost of delay as % of feature value per day
                          current_lead_time: float = 30):  # days
    """
    Analyze flow economics using Reinertsen's principles.
    
    Key principles:
    1. Queues are the root cause of poor economics
    2. Cost of delay should drive prioritization  
    3. Batch size reduction is powerful
    4. WIP constraints improve flow
    5. Variability creates queues
    """
    
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}PRODUCT DEVELOPMENT FLOW ANALYSIS{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")
    
    print(f"{BOLD}Economic Parameters:{RESET}")
    cost_of_delay_per_day = feature_value * urgency_factor
    economic_data = [
        ["Feature Value", f"${feature_value:,}"],
        ["Cost of Delay", f"${cost_of_delay_per_day:,.0f} per feature per day"],
        ["Current Lead Time", f"{current_lead_time} days"],
        ["Current Delay Cost", f"${cost_of_delay_per_day * current_lead_time:,.0f} per feature"],
        ["Team Size", team_size]
    ]
    print(tabulate(economic_data, tablefmt='simple'))
    print()
    
    # Create pipeline for analysis
    pipeline = create_standard_pipeline(team_size=team_size, test_automation=0.5)
    
    # Analyze current state
    print(f"{BOLD}CURRENT STATE ANALYSIS{RESET}")
    
    # Calculate flow efficiency
    flow_efficiency = pipeline.calculate_flow_efficiency()
    lead_time_data = pipeline.calculate_lead_time(0.5)
    total_lead_time = lead_time_data['total_lead_time_days']
    
    # Estimate value-add time vs wait time
    value_add_time = total_lead_time * flow_efficiency
    wait_time = total_lead_time - value_add_time
    
    flow_data = [
        ["Total Lead Time", f"{total_lead_time:.1f} days"],
        ["Value-Add Time", f"{value_add_time:.1f} days ({flow_efficiency:.1%})"],
        ["Wait Time (Queues)", f"{wait_time:.1f} days ({1-flow_efficiency:.1%})"],
        ["Flow Efficiency", f"{flow_efficiency:.1%}" + (f" {RED}(Poor){RESET}" if flow_efficiency < 0.25 
                                                        else f" {YELLOW}(Typical){RESET}" if flow_efficiency < 0.5
                                                        else f" {GREEN}(Good){RESET}")],
    ]
    print(tabulate(flow_data, tablefmt='simple'))
    print()
    
    # Queue analysis
    print(f"{BOLD}QUEUE IMPACT ANALYSIS{RESET}")
    
    # Model queues between stages (simplified)
    throughput_data = pipeline.calculate_throughput(0.5)
    stage_throughputs = throughput_data['stage_throughputs']
    bottleneck_throughput = throughput_data['throughput_per_day']
    
    # Calculate queue lengths using Little's Law
    queue_analysis = []
    total_queue_cost = 0
    
    for stage_name, throughput in stage_throughputs.items():
        # Arrival rate = bottleneck throughput (system throughput)
        arrival_rate = bottleneck_throughput / 30  # per day
        service_rate = throughput / 30  # per day
        
        if service_rate > arrival_rate:
            utilization = arrival_rate / service_rate
            # M/M/1 queue length
            avg_queue_length = (utilization ** 2) / (1 - utilization) if utilization < 1 else float('inf')
            avg_wait_time = avg_queue_length / arrival_rate if arrival_rate > 0 else 0
        else:
            avg_queue_length = float('inf')
            avg_wait_time = float('inf')
            utilization = 1.0
        
        queue_cost_per_day = avg_queue_length * cost_of_delay_per_day if avg_queue_length != float('inf') else 999999
        total_queue_cost += queue_cost_per_day
        
        queue_analysis.append([
            stage_name.replace('_', ' ').title(),
            f"{utilization:.1%}",
            f"{avg_queue_length:.1f}" if avg_queue_length != float('inf') else "∞",
            f"{avg_wait_time:.1f}" if avg_wait_time != float('inf') else "∞",
            f"${queue_cost_per_day:,.0f}" if queue_cost_per_day != 999999 else "∞"
        ])
    
    print(tabulate(queue_analysis,
                   headers=["Stage", "Utilization", "Avg Queue", "Wait Time", "Daily Cost"],
                   tablefmt='simple'))
    
    print(f"\nTotal Daily Queue Cost: {RED}${total_queue_cost:,.0f}{RESET}")
    print(f"Monthly Queue Cost: {RED}${total_queue_cost * 30:,.0f}{RESET}")
    print()
    
    # Batch size analysis
    print(f"{BOLD}BATCH SIZE OPTIMIZATION{RESET}")
    
    current_batch_sizes = {
        'requirements': 5,
        'coding': 1,
        'code_review': 3,
        'testing': 2,
        'deployment': 10
    }
    
    batch_optimizer = BatchSizeOptimizer()
    batch_analysis = []
    
    for stage, current_batch in current_batch_sizes.items():
        # Estimate transaction and holding costs
        transaction_cost = team_size * 50  # Cost to start a batch
        holding_cost = cost_of_delay_per_day / current_batch  # Cost per item per day
        demand_rate = bottleneck_throughput / 30  # Items per day
        
        optimal_batch = batch_optimizer.calculate_optimal_batch_size(
            transaction_cost=transaction_cost,
            holding_cost_per_item=holding_cost,
            demand_rate=demand_rate,
            variability=1.2  # Software has high variability
        )
        
        # Calculate delay costs
        processing_time = 1.0  # Assume 1 day processing time
        current_delay_cost = batch_optimizer.calculate_batch_delay_cost(
            batch_size=current_batch,
            item_urgency=cost_of_delay_per_day,
            processing_time=processing_time
        )
        
        optimal_delay_cost = batch_optimizer.calculate_batch_delay_cost(
            batch_size=optimal_batch,
            item_urgency=cost_of_delay_per_day,
            processing_time=processing_time
        )
        
        savings = current_delay_cost - optimal_delay_cost
        
        batch_analysis.append([
            stage.replace('_', ' ').title(),
            current_batch,
            optimal_batch,
            f"${current_delay_cost:,.0f}",
            f"${optimal_delay_cost:,.0f}",
            f"${savings:,.0f}" if savings > 0 else f"-${abs(savings):,.0f}"
        ])
    
    print(tabulate(batch_analysis,
                   headers=["Stage", "Current", "Optimal", "Current Cost", "Optimal Cost", "Savings"],
                   tablefmt='simple'))
    print()
    
    # WIP constraint analysis
    print(f"{BOLD}WIP CONSTRAINT RECOMMENDATIONS{RESET}")
    
    # Calculate current WIP levels and recommendations
    wip_recommendations = []
    for stage_name in stage_throughputs.keys():
        current_wip = team_size  # Assume no WIP limits currently
        throughput = stage_throughputs[stage_name] / 30  # per day
        
        # Recommended WIP using Little's Law: WIP = Throughput × Lead Time
        target_lead_time = 2.0  # Target 2-day lead time per stage
        recommended_wip = max(1, int(throughput * target_lead_time))
        
        wip_impact = "Reduce queues" if recommended_wip < current_wip else "Current OK"
        
        wip_recommendations.append([
            stage_name.replace('_', ' ').title(),
            current_wip,
            recommended_wip,
            wip_impact
        ])
    
    print(tabulate(wip_recommendations,
                   headers=["Stage", "Current WIP", "Recommended", "Impact"],
                   tablefmt='simple'))
    print()
    
    # Variability impact analysis
    print(f"{BOLD}VARIABILITY IMPACT ANALYSIS{RESET}")
    
    # Model different variability scenarios
    variability_scenarios = [
        ("Low Variability (CV=0.5)", 0.5),
        ("Typical Software (CV=1.0)", 1.0),
        ("High Variability (CV=1.5)", 1.5),
        ("Chaotic (CV=2.0)", 2.0)
    ]
    
    variability_analysis = []
    
    for scenario_name, cv in variability_scenarios:
        # Higher variability increases queue lengths exponentially
        base_utilization = 0.8  # 80% utilization
        
        # Approximation: queue length increases with CV²
        queue_multiplier = 1 + cv ** 2
        estimated_queue_length = queue_multiplier * (base_utilization ** 2) / (1 - base_utilization)
        estimated_wait_time = estimated_queue_length / (bottleneck_throughput / 30)
        queue_cost = estimated_queue_length * cost_of_delay_per_day
        
        variability_analysis.append([
            scenario_name,
            f"{cv:.1f}",
            f"{estimated_queue_length:.1f}",
            f"{estimated_wait_time:.1f}",
            f"${queue_cost:,.0f}"
        ])
    
    print(tabulate(variability_analysis,
                   headers=["Scenario", "CV", "Queue Length", "Wait Time", "Daily Cost"],
                   tablefmt='simple'))
    print()
    
    # Recommendations based on Reinertsen's principles
    print(f"{BOLD}REINERTSEN'S FLOW PRINCIPLES - RECOMMENDATIONS{RESET}")
    
    recommendations = []
    
    # Principle 1: Make Economic Decisions
    if flow_efficiency < 0.25:
        recommendations.append([
            "Economic Focus",
            "Flow efficiency < 25% - focus on queue reduction over resource efficiency",
            "High Priority"
        ])
    
    # Principle 2: Manage Queues
    if total_queue_cost > feature_value:
        recommendations.append([
            "Queue Management", 
            f"Queue costs (${total_queue_cost:,.0f}/day) exceed feature value - implement WIP limits",
            "Critical"
        ])
    
    # Principle 3: Reduce Batch Sizes
    large_batches = [stage for stage, batch in current_batch_sizes.items() if batch > 5]
    if large_batches:
        recommendations.append([
            "Batch Size Reduction",
            f"Large batches in {', '.join(large_batches)} - reduce to improve flow",
            "High Priority"
        ])
    
    # Principle 4: Apply WIP Constraints
    if any(rec[2] == "Reduce queues" for rec in wip_recommendations):
        recommendations.append([
            "WIP Constraints",
            "Implement WIP limits to prevent queue buildup",
            "High Priority"
        ])
    
    # Principle 5: Accelerate Feedback
    if total_lead_time > 14:  # 2 weeks
        recommendations.append([
            "Feedback Acceleration",
            f"Lead time ({total_lead_time:.1f} days) too long - implement faster feedback loops",
            "Medium Priority"
        ])
    
    # Principle 6: Manage Flow under Variability
    recommendations.append([
        "Variability Management",
        "High software variability - use smaller batches and safety capacity",
        "Medium Priority"
    ])
    
    print(tabulate(recommendations,
                   headers=["Principle", "Recommendation", "Priority"],
                   tablefmt='simple'))
    print()
    
    # Economic impact summary
    print(f"{BOLD}ECONOMIC IMPACT SUMMARY{RESET}")
    
    # Calculate potential improvements
    improved_flow_efficiency = min(0.6, flow_efficiency * 1.5)  # 50% improvement, max 60%
    improved_lead_time = total_lead_time * (flow_efficiency / improved_flow_efficiency)
    delay_cost_savings = (total_lead_time - improved_lead_time) * cost_of_delay_per_day
    
    # Batch size savings
    total_batch_savings = sum(max(0, float(row[5].replace('$', '').replace(',', ''))) 
                             for row in batch_analysis if not row[5].startswith('-'))
    
    economic_summary = [
        ["Current Monthly Delay Cost", f"${total_lead_time * cost_of_delay_per_day * bottleneck_throughput:,.0f}"],
        ["Current Monthly Queue Cost", f"${total_queue_cost * 30:,.0f}"],
        ["", ""],
        ["Potential Improvements:", ""],
        ["Improved Lead Time", f"{improved_lead_time:.1f} days (vs {total_lead_time:.1f})"],
        ["Monthly Delay Savings", f"${delay_cost_savings * bottleneck_throughput:,.0f}"],
        ["Monthly Batch Savings", f"${total_batch_savings * 30:,.0f}"],
        ["Total Monthly Savings", f"${(delay_cost_savings * bottleneck_throughput) + (total_batch_savings * 30):,.0f}"],
        ["", ""],
        ["Implementation Cost", "Low - mostly process changes"],
        ["Payback Period", "< 1 month"]
    ]
    
    print(tabulate(economic_summary, tablefmt='simple'))
    print()
    
    print(f"{BOLD}KEY INSIGHTS:{RESET}")
    
    insights = [
        f"Flow efficiency of {flow_efficiency:.1%} indicates significant queue waste",
        f"Queue costs of ${total_queue_cost:,.0f}/day are often invisible to management",
        f"Batch size optimization could save ${total_batch_savings:,.0f}/day",
        f"Lead time reduction from {total_lead_time:.1f} to {improved_lead_time:.1f} days possible",
        "Focus on flow, not resource utilization - counterintuitive but economically sound"
    ]
    
    for insight in insights:
        print(f"  • {insight}")
    
    return {
        'flow_efficiency': flow_efficiency,
        'total_lead_time': total_lead_time,
        'queue_cost_per_day': total_queue_cost,
        'batch_savings_per_day': total_batch_savings,
        'delay_cost_savings': delay_cost_savings,
        'recommendations': recommendations
    }


def main():
    parser = argparse.ArgumentParser(
        description='Product development flow analysis using Reinertsen principles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Reinertsen's Product Development Flow Principles:

1. Make economic decisions based on cost of delay
2. Manage queues - they are the root cause of poor economics  
3. Reduce batch sizes to improve flow
4. Apply WIP constraints to limit queues
5. Accelerate feedback to enable smaller batches
6. Manage flow under variability with safety capacity
7. Use decentralized control for speed
8. Align architecture with organization for flow

This analysis reveals the hidden economic costs in your delivery pipeline,
focusing on queues, batches, and variability that most organizations ignore.

Examples:
  python flow_analyzer.py --team 50 --value 10000
  python flow_analyzer.py --team 20 --value 5000 --urgency 0.05
  python flow_analyzer.py --team 100 --lead-time 45 --urgency 0.15
        """
    )
    
    parser.add_argument('--team', type=int, required=True,
                       help='Team size')
    parser.add_argument('--value', type=float, default=10000,
                       help='Feature value in dollars')
    parser.add_argument('--urgency', type=float, default=0.1,
                       help='Cost of delay as fraction of feature value per day')
    parser.add_argument('--lead-time', type=float, default=30,
                       help='Current lead time in days')
    
    args = parser.parse_args()
    
    if args.urgency < 0 or args.urgency > 1:
        print(f"{RED}Error: Urgency factor must be between 0 and 1{RESET}")
        sys.exit(1)
    
    print(f"\n{BOLD}Product Development Flow Analysis{RESET}")
    print(f"Team: {args.team} | Feature Value: ${args.value:,} | Urgency: {args.urgency:.1%}/day")
    
    result = analyze_flow_economics(
        team_size=args.team,
        feature_value=args.value,
        urgency_factor=args.urgency,
        current_lead_time=args.lead_time
    )
    
    sys.exit(0)


if __name__ == "__main__":
    main()