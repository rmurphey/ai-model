#!/usr/bin/env python3
"""
Report generation command for AI Impact Analysis Model.
Generates comprehensive reports in multiple formats.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from main import AIImpactModel
from src.scenarios.scenario_loader import ScenarioLoader
from src.config.version import get_current_version_string
from src.utils.exceptions import ConfigurationError
from src.model.monte_carlo import create_parameter_distributions_from_scenario


class ReportGenerator:
    """Generate reports from analysis results."""
    
    def __init__(self, results: Dict[str, Any], scenario_name: str):
        """
        Initialize report generator.
        
        Args:
            results: Analysis results dictionary
            scenario_name: Name of the scenario analyzed
        """
        self.results = results
        self.scenario_name = scenario_name
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_markdown(self) -> str:
        """Generate a markdown report."""
        report = []
        
        # Header
        report.append(f"# AI Impact Analysis Report")
        report.append(f"\n**Scenario:** {self.scenario_name}")
        report.append(f"**Generated:** {self.timestamp}")
        report.append(f"**Model Version:** {get_current_version_string()}\n")
        
        # Executive Summary
        report.append("## Executive Summary\n")
        npv = self.results.get('financial_metrics', {}).get('npv', 0)
        roi = self.results.get('financial_metrics', {}).get('roi', 0)
        payback = self.results.get('financial_metrics', {}).get('payback_period_months', 0)
        
        report.append(f"- **NPV:** ${npv:,.2f}")
        report.append(f"- **ROI:** {roi:.1f}%")
        report.append(f"- **Payback Period:** {payback:.1f} months\n")
        
        # Time Efficiency
        report.append("## Time Efficiency Analysis\n")
        time_metrics = self.results.get('time_efficiency', {})
        report.append(f"- **Time Saved per Month:** {time_metrics.get('time_saved_per_month', 0):.1f} hours")
        report.append(f"- **Efficiency Gain:** {time_metrics.get('efficiency_gain', 0):.1f}%")
        report.append(f"- **Total Time Saved:** {time_metrics.get('total_time_saved', 0):.1f} hours\n")
        
        # Cost Analysis
        report.append("## Cost Analysis\n")
        costs = self.results.get('costs', {})
        report.append(f"- **Development Costs:** ${costs.get('development', 0):,.2f}")
        report.append(f"- **Infrastructure Costs:** ${costs.get('infrastructure', 0):,.2f}")
        report.append(f"- **Training Costs:** ${costs.get('training', 0):,.2f}")
        report.append(f"- **Total Implementation Costs:** ${costs.get('total_implementation', 0):,.2f}\n")
        
        # Productivity Metrics
        report.append("## Productivity Metrics\n")
        productivity = self.results.get('productivity_metrics', {})
        report.append(f"- **Output Increase:** {productivity.get('output_increase', 0):.1f}%")
        report.append(f"- **FTE Equivalent:** {productivity.get('fte_equivalent', 0):.2f}")
        report.append(f"- **Productivity Multiplier:** {productivity.get('productivity_multiplier', 0):.2f}x\n")
        
        # Monte Carlo Results (if present)
        if 'monte_carlo' in self.results:
            report.append("## Monte Carlo Simulation Results\n")
            mc = self.results['monte_carlo']
            
            if 'npv' in mc:
                npv_stats = mc['npv']
                report.append("### NPV Distribution")
                report.append(f"- **Mean:** ${npv_stats.get('mean', 0):,.2f}")
                report.append(f"- **Std Dev:** ${npv_stats.get('std', 0):,.2f}")
                report.append(f"- **95% CI:** ${npv_stats.get('percentile_5', 0):,.2f} to ${npv_stats.get('percentile_95', 0):,.2f}")
                report.append(f"- **P(NPV > 0):** {npv_stats.get('probability_positive', 0):.1%}\n")
            
            if 'sensitivity' in mc:
                report.append("### Sensitivity Analysis")
                report.append("Top factors affecting NPV variance:")
                for param, importance in sorted(mc['sensitivity'].items(), 
                                               key=lambda x: x[1], reverse=True)[:5]:
                    report.append(f"- {param}: {importance:.1%}")
                report.append("")
        
        return "\n".join(report)
    
    def generate_json(self) -> str:
        """Generate a JSON report."""
        report_data = {
            "metadata": {
                "scenario": self.scenario_name,
                "timestamp": self.timestamp,
                "model_version": get_current_version_string()
            },
            "results": self.results
        }
        return json.dumps(report_data, indent=2, default=str)
    
    def generate_text(self) -> str:
        """Generate a plain text report."""
        lines = []
        lines.append("=" * 60)
        lines.append("AI IMPACT ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"Scenario: {self.scenario_name}")
        lines.append(f"Generated: {self.timestamp}")
        lines.append(f"Model Version: {get_current_version_string()}")
        lines.append("-" * 60)
        
        # Financial metrics
        lines.append("\nFINANCIAL METRICS:")
        npv = self.results.get('financial_metrics', {}).get('npv', 0)
        roi = self.results.get('financial_metrics', {}).get('roi', 0)
        payback = self.results.get('financial_metrics', {}).get('payback_period_months', 0)
        
        lines.append(f"  NPV: ${npv:,.2f}")
        lines.append(f"  ROI: {roi:.1f}%")
        lines.append(f"  Payback Period: {payback:.1f} months")
        
        # Time efficiency
        lines.append("\nTIME EFFICIENCY:")
        time_metrics = self.results.get('time_efficiency', {})
        lines.append(f"  Time Saved/Month: {time_metrics.get('time_saved_per_month', 0):.1f} hours")
        lines.append(f"  Efficiency Gain: {time_metrics.get('efficiency_gain', 0):.1f}%")
        
        # Costs
        lines.append("\nCOSTS:")
        costs = self.results.get('costs', {})
        lines.append(f"  Development: ${costs.get('development', 0):,.2f}")
        lines.append(f"  Infrastructure: ${costs.get('infrastructure', 0):,.2f}")
        lines.append(f"  Training: ${costs.get('training', 0):,.2f}")
        lines.append(f"  Total: ${costs.get('total_implementation', 0):,.2f}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def save(self, output_path: Path, format: str = "markdown"):
        """
        Save report to file.
        
        Args:
            output_path: Path to save the report
            format: Report format (markdown, json, text)
        """
        if format == "markdown":
            content = self.generate_markdown()
        elif format == "json":
            content = self.generate_json()
        elif format == "text":
            content = self.generate_text()
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(content)


def main():
    """Main entry point for report generation."""
    parser = argparse.ArgumentParser(
        description="Generate reports from AI impact analysis results"
    )
    
    parser.add_argument(
        "scenario",
        help="Name of the scenario to analyze"
    )
    
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "text", "all"],
        default="markdown",
        help="Output format for the report (default: markdown)"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (default: reports/<scenario>_<timestamp>.<ext>)"
    )
    
    parser.add_argument(
        "--monte-carlo",
        "-m",
        action="store_true",
        help="Include Monte Carlo simulation in analysis"
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=10000,
        help="Number of Monte Carlo iterations (default: 10000)"
    )
    
    parser.add_argument(
        "--scenarios-path",
        default="src/scenarios",
        help="Path to scenarios directory (default: src/scenarios)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize model
        model = AIImpactModel()
        
        # Run analysis
        if args.monte_carlo:
            results = model.run_monte_carlo_analysis(args.scenario, iterations=args.iterations)
        else:
            results = model.run_scenario(args.scenario)
        
        # Generate report
        generator = ReportGenerator(results, args.scenario)
        
        # Determine output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if args.format == "all":
            formats = ["markdown", "json", "text"]
        else:
            formats = [args.format]
        
        for fmt in formats:
            if args.output and len(formats) == 1:
                output_path = Path(args.output)
            else:
                ext = {"markdown": "md", "json": "json", "text": "txt"}[fmt]
                filename = f"{args.scenario}_{timestamp}.{ext}"
                output_path = Path("reports") / filename
            
            generator.save(output_path, fmt)
            print(f"Report saved to: {output_path}")
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        if e.resolution_steps:
            print("\nSuggested resolution steps:")
            for step in e.resolution_steps:
                print(f"  - {step}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()