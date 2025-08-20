#!/usr/bin/env python3
"""
Terminal-based visualizations for AI impact model
No browser required - pure ASCII art and formatted tables
"""

import numpy as np
from typing import Dict, List, Tuple
from tabulate import tabulate
from main import AIImpactModel
import sys

# ANSI color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def create_ascii_bar_chart(values: List[float], labels: List[str], title: str, width: int = 50, show_values: bool = True):
    """Create an ASCII bar chart"""
    max_val = max(values) if values else 1
    
    print(f"\n{Colors.BOLD}{title}{Colors.ENDC}")
    print("=" * (width + 20))
    
    for label, value in zip(labels, values):
        bar_length = int((value / max_val) * width)
        bar = "█" * bar_length
        
        # Color based on value
        if value / max_val > 0.75:
            color = Colors.GREEN
        elif value / max_val > 0.5:
            color = Colors.YELLOW
        else:
            color = Colors.CYAN
        
        if show_values:
            if value > 1_000_000:
                value_str = f"${value/1_000_000:.1f}M"
            elif value > 1_000:
                value_str = f"${value/1_000:.0f}K"
            else:
                value_str = f"${value:.0f}"
        else:
            value_str = f"{value:.1f}%"
        
        print(f"{label:20} {color}{bar}{Colors.ENDC} {value_str}")
    
    print()

def create_ascii_line_chart(data: np.ndarray, title: str, height: int = 15, width: int = 60):
    """Create an ASCII line chart"""
    if len(data) == 0:
        return
    
    # Normalize data to fit in height
    min_val = np.min(data)
    max_val = np.max(data)
    range_val = max_val - min_val if max_val != min_val else 1
    
    # Create the chart
    chart = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Sample points if data is longer than width
    if len(data) > width:
        indices = np.linspace(0, len(data)-1, width).astype(int)
        sampled_data = data[indices]
    else:
        sampled_data = data
        indices = np.arange(len(data))
    
    # Plot the line
    for i, value in enumerate(sampled_data):
        y = height - 1 - int((value - min_val) / range_val * (height - 1))
        x = int(i * (width - 1) / (len(sampled_data) - 1)) if len(sampled_data) > 1 else 0
        if 0 <= x < width and 0 <= y < height:
            chart[y][x] = '●'
    
    # Add axes
    print(f"\n{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"  {max_val:.0f}% ┤" + "─" * width)
    
    for row in chart:
        print("       │" + ''.join(row))
    
    print(f"  {min_val:.0f}% └" + "─" * width)
    print(f"       0" + " " * (width//2 - 5) + f"Months" + " " * (width//2 - 5) + f"{len(data)}")
    print()

def create_heatmap(matrix: List[List[float]], row_labels: List[str], col_labels: List[str], title: str):
    """Create an ASCII heatmap using block characters"""
    blocks = [' ', '░', '▒', '▓', '█']
    
    print(f"\n{Colors.BOLD}{title}{Colors.ENDC}")
    print("=" * 60)
    
    # Normalize values
    flat = [val for row in matrix for val in row]
    min_val = min(flat)
    max_val = max(flat)
    range_val = max_val - min_val if max_val != min_val else 1
    
    # Print header
    print(f"{'':15}", end='')
    for label in col_labels:
        print(f"{label:15}", end='')
    print()
    print("-" * (15 + 15 * len(col_labels)))
    
    # Print rows
    for i, row_label in enumerate(row_labels):
        print(f"{row_label:15}", end='')
        for j, value in enumerate(matrix[i]):
            normalized = (value - min_val) / range_val
            block_idx = int(normalized * (len(blocks) - 1))
            block = blocks[block_idx]
            
            # Color based on value
            if normalized > 0.75:
                color = Colors.GREEN
            elif normalized > 0.5:
                color = Colors.YELLOW
            elif normalized > 0.25:
                color = Colors.CYAN
            else:
                color = Colors.RED
            
            # Format value based on context
            if title.upper().find('ROI') >= 0 or title.upper().find('RETURN') >= 0:
                # ROI values are percentages
                val_str = f"{value:.0f}%"
            elif title.upper().find('PAYBACK') >= 0:
                # Payback values are months
                if value >= 999:
                    val_str = "Never"
                else:
                    val_str = f"{value:.0f}mo"
            else:
                # NPV and other financial values
                if value > 1_000_000:
                    val_str = f"${value/1_000_000:.1f}M"
                elif value > 1_000:
                    val_str = f"${value/1_000:.0f}K"
                else:
                    val_str = f"${value:.0f}"
            
            print(f"{color}{block*3} {val_str:8}{Colors.ENDC}", end='  ')
        print()
    print()

def create_sparkline(data: List[float], width: int = 20) -> str:
    """Create a sparkline using Unicode block characters"""
    if not data:
        return ""
    
    blocks = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    min_val = min(data)
    max_val = max(data)
    range_val = max_val - min_val if max_val != min_val else 1
    
    # Sample if too long
    if len(data) > width:
        indices = np.linspace(0, len(data)-1, width).astype(int)
        sampled = [data[i] for i in indices]
    else:
        sampled = data
    
    sparkline = ""
    for value in sampled:
        normalized = (value - min_val) / range_val
        block_idx = int(normalized * (len(blocks) - 1))
        sparkline += blocks[block_idx]
    
    return sparkline

def display_scenario_matrix(results: Dict):
    """Display scenario matrix in terminal"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}SCENARIO MATRIX ANALYSIS - 3x3 Grid{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}")
    
    # Prepare matrix data
    companies = ['startup', 'enterprise', 'scaleup']
    approaches = ['conservative', 'moderate', 'aggressive']
    
    # NPV Matrix
    npv_matrix = []
    roi_matrix = []
    payback_matrix = []
    
    for company in companies:
        npv_row = []
        roi_row = []
        payback_row = []
        for approach in approaches:
            scenario = f"{approach}_{company}"
            if scenario in results:
                npv_row.append(results[scenario]['npv'])
                roi_row.append(results[scenario]['roi_percent'])
                payback_row.append(results[scenario]['breakeven_month'] or 999)
            else:
                npv_row.append(0)
                roi_row.append(0)
                payback_row.append(999)
        npv_matrix.append(npv_row)
        roi_matrix.append(roi_row)
        payback_matrix.append(payback_row)
    
    # Display heatmaps
    create_heatmap(npv_matrix, 
                  ['Startup', 'Enterprise', 'Scale-up'],
                  ['Conservative', 'Moderate', 'Aggressive'],
                  "NET PRESENT VALUE (NPV) HEATMAP")
    
    create_heatmap(roi_matrix,
                  ['Startup', 'Enterprise', 'Scale-up'],
                  ['Conservative', 'Moderate', 'Aggressive'],
                  "RETURN ON INVESTMENT (%) HEATMAP")

def display_adoption_curves(results: Dict):
    """Display adoption curves in terminal"""
    print(f"\n{Colors.BOLD}ADOPTION CURVES - Peak Values & Trends{Colors.ENDC}")
    print("=" * 80)
    
    # Group by company type
    for company in ['startup', 'enterprise', 'scaleup']:
        print(f"\n{Colors.CYAN}{company.upper()}{Colors.ENDC}")
        print("-" * 40)
        
        for approach in ['conservative', 'moderate', 'aggressive']:
            scenario = f"{approach}_{company}"
            if scenario in results:
                adoption = results[scenario]['adoption']
                peak = max(adoption) * 100
                final = adoption[-1] * 100
                
                # Create sparkline
                sparkline = create_sparkline([a * 100 for a in adoption])
                
                # Color code based on performance
                if peak > 85:
                    color = Colors.GREEN
                elif peak > 75:
                    color = Colors.YELLOW
                else:
                    color = Colors.CYAN
                
                print(f"  {approach:12} {sparkline} {color}Peak: {peak:5.1f}% Final: {final:5.1f}%{Colors.ENDC}")

def display_comprehensive_summary(results: Dict):
    """Display comprehensive summary table"""
    
    # Prepare data for tabulate
    headers = ['Scenario', 'Peak\nAdopt', 'NPV', 'ROI', 'Payback', 'Value/Dev\n/Year', 'Trend']
    rows = []
    
    for scenario in sorted(results.keys()):
        r = results[scenario]
        
        # Format values with proper units
        if r['npv'] > 1_000_000:
            npv_str = f"${r['npv']/1_000_000:.2f}M"
        else:
            npv_str = f"${r['npv']/1_000:.0f}K"
        
        # Create mini sparkline for adoption
        trend = create_sparkline([a * 100 for a in r['adoption']], width=10)
        
        row = [
            scenario.replace('_', ' ').title(),
            f"{max(r['adoption'])*100:.1f}%",  # Added % sign
            npv_str,
            f"{r['roi_percent']:.0f}%",  # Added % sign
            f"{r['breakeven_month']} mo" if r['breakeven_month'] else "Never",  # Added "mo"
            f"${r['annual_value_per_dev']/1_000:.0f}K",
            trend
        ]
        rows.append(row)
    
    print(f"\n{Colors.BOLD}{'='*100}{Colors.ENDC}")
    print(f"{Colors.BOLD}COMPREHENSIVE SCENARIO COMPARISON{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*100}{Colors.ENDC}\n")
    
    print(tabulate(rows, headers=headers, tablefmt='grid', numalign='right'))

def display_monte_carlo_summary():
    """Display Monte Carlo analysis summary in terminal"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}MONTE CARLO ANALYSIS - Risk & Uncertainty{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}")
    
    # Simulated data for demonstration
    scenarios = ['Conservative Startup', 'Moderate Enterprise', 'Aggressive Scaleup']
    
    # Risk-Return visualization using ASCII
    print("\n" + Colors.CYAN + "Risk-Return Profile (Size = Expected NPV)" + Colors.ENDC)
    print("High ┤")
    print("     │       ○ Aggressive")
    print("Return│    ◉ Moderate     ")
    print("     │ • Conservative")
    print("Low  └────────────────────")
    print("      Low    Risk    High")
    
    # Confidence intervals
    print(f"\n{Colors.CYAN}Confidence Intervals (P10 ━━━ P50 ━━━ P90){Colors.ENDC}")
    print("-" * 60)
    
    data = [
        ('Conservative Startup', 400, 480, 540),
        ('Moderate Enterprise', 7900, 9500, 10700),
        ('Aggressive Scaleup', 3400, 4200, 5000)
    ]
    
    for name, p10, p50, p90 in data:
        # Normalize to 40 char width
        max_val = 11000
        scale = 40 / max_val
        
        p10_pos = int(p10 * scale)
        p50_pos = int(p50 * scale)
        p90_pos = int(p90 * scale)
        
        line = [' '] * 40
        for i in range(p10_pos, p90_pos + 1):
            if i < len(line):
                line[i] = '━'
        if p50_pos < len(line):
            line[p50_pos] = '◆'
        
        print(f"{name:20} {''.join(line)} ${p50}K")

def display_top_insights(results: Dict):
    """Display key insights with visual indicators"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}KEY INSIGHTS & RECOMMENDATIONS{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    # Find best scenarios
    best_npv = max(results.items(), key=lambda x: x[1]['npv'])
    best_roi = max(results.items(), key=lambda x: x[1]['roi_percent'])
    best_payback = min((k, v['breakeven_month']) for k, v in results.items() if v['breakeven_month'])
    
    insights = [
        (f"🏆 Highest NPV", f"{best_npv[0]}", f"${best_npv[1]['npv']/1e6:.2f}M", Colors.GREEN),
        (f"📈 Best ROI", f"{best_roi[0]}", f"{best_roi[1]['roi_percent']:.0f}%", Colors.YELLOW),
        (f"⚡ Fastest Payback", f"{best_payback[0]}", f"{best_payback[1]} months", Colors.CYAN),
    ]
    
    for icon_label, scenario, value, color in insights:
        print(f"{icon_label:20} {color}{scenario:25} {value:>15}{Colors.ENDC}")
    
    # Risk-adjusted recommendations
    print(f"\n{Colors.BOLD}Risk-Adjusted Recommendations:{Colors.ENDC}")
    print("├─ Startups:     " + Colors.GREEN + "Moderate approach" + Colors.ENDC + " (best risk/return)")
    print("├─ Enterprises:  " + Colors.YELLOW + "Aggressive approach" + Colors.ENDC + " (high NPV, acceptable risk)")
    print("└─ Scale-ups:    " + Colors.CYAN + "Moderate approach" + Colors.ENDC + " (balanced growth)")

def main():
    """Main function to run all terminal visualizations"""
    
    # Run scenarios
    print(f"{Colors.BOLD}Running scenario analysis...{Colors.ENDC}")
    model = AIImpactModel()
    
    scenarios = []
    for company in ['startup', 'enterprise', 'scaleup']:
        for approach in ['conservative', 'moderate', 'aggressive']:
            scenarios.append(f"{approach}_{company}")
    
    results = {}
    for i, scenario in enumerate(scenarios):
        print(f"  [{i+1}/9] {scenario}...", end='\r')
        results[scenario] = model.run_scenario(scenario)
    print(f"  [9/9] Complete!          ")
    
    # Display all visualizations
    display_scenario_matrix(results)
    display_adoption_curves(results)
    display_comprehensive_summary(results)
    display_monte_carlo_summary()
    display_top_insights(results)
    
    # Simple bar charts for key metrics
    print(f"\n{Colors.BOLD}NPV BY COMPANY TYPE{Colors.ENDC}")
    for company in ['startup', 'enterprise', 'scaleup']:
        values = []
        labels = []
        for approach in ['conservative', 'moderate', 'aggressive']:
            scenario = f"{approach}_{company}"
            if scenario in results:
                values.append(results[scenario]['npv'])
                labels.append(approach.capitalize())
        
        if values:
            create_ascii_bar_chart(values, labels, company.upper(), width=40)

if __name__ == "__main__":
    # Check if terminal supports colors
    if not sys.stdout.isatty():
        # Disable colors if not in terminal
        for attr in dir(Colors):
            if not attr.startswith('__'):
                setattr(Colors, attr, '')
    
    main()