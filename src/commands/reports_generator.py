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
        npv = float(self.results.get('npv', 0))
        roi = float(self.results.get('roi_percent', 0))
        payback = self.results.get('breakeven_month')
        if payback is not None:
            payback = float(payback)
        else:
            payback = 0
        
        report.append(f"- **NPV:** ${npv:,.2f}")
        report.append(f"- **ROI:** {roi:.1f}%")
        report.append(f"- **Payback Period:** {payback:.1f} months\n")
        
        # Time Efficiency
        report.append("## Efficiency Analysis\n")
        if 'efficiency' in self.results and self.results['efficiency'] is not None:
            final_efficiency = float(self.results['efficiency'][-1] * 100)
            peak_adoption = float(self.results.get('peak_adoption', 0) * 100)
            report.append(f"- **Final Efficiency:** {final_efficiency:.1f}%")
            report.append(f"- **Peak Adoption:** {peak_adoption:.1f}%\n")
        
        # Cost Analysis
        report.append("## Cost Analysis\n")
        total_cost = float(self.results.get('total_cost_3y', 0))
        annual_cost_per_dev = float(self.results.get('annual_cost_per_dev', 0))
        report.append(f"- **Total 3-Year Cost:** ${total_cost:,.2f}")
        report.append(f"- **Annual Cost per Developer:** ${annual_cost_per_dev:,.2f}\n")
        
        # Value Creation
        report.append("## Value Creation\n")
        total_value = float(self.results.get('total_value_3y', 0))
        annual_value_per_dev = float(self.results.get('annual_value_per_dev', 0))
        report.append(f"- **Total 3-Year Value:** ${total_value:,.2f}")
        report.append(f"- **Annual Value per Developer:** ${annual_value_per_dev:,.2f}\n")
        
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
        npv = float(self.results.get('npv', 0))
        roi = float(self.results.get('roi_percent', 0))
        payback = self.results.get('breakeven_month')
        if payback is not None:
            payback = float(payback)
        else:
            payback = 0
        
        lines.append(f"  NPV: ${npv:,.2f}")
        lines.append(f"  ROI: {roi:.1f}%")
        lines.append(f"  Payback Period: {payback:.1f} months")
        
        # Efficiency
        lines.append("\nEFFICIENCY:")
        if 'efficiency' in self.results and self.results['efficiency'] is not None:
            final_efficiency = float(self.results['efficiency'][-1] * 100)
            peak_adoption = float(self.results.get('peak_adoption', 0) * 100)
            lines.append(f"  Final Efficiency: {final_efficiency:.1f}%")
            lines.append(f"  Peak Adoption: {peak_adoption:.1f}%")
        
        # Costs
        lines.append("\nCOSTS:")
        total_cost = float(self.results.get('total_cost_3y', 0))
        annual_cost_per_dev = float(self.results.get('annual_cost_per_dev', 0))
        lines.append(f"  Total 3-Year Cost: ${total_cost:,.2f}")
        lines.append(f"  Annual Cost/Dev: ${annual_cost_per_dev:,.2f}")
        
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