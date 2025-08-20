#!/usr/bin/env python3
"""
AI Impact Analysis Runner
Simple command-line tool for running scenarios and saving results to text files.

Usage:
    python run_analysis.py moderate_enterprise
    python run_analysis.py startup enterprise scaleup
    python run_analysis.py --compare all
    python run_analysis.py --output my_analysis.txt moderate_enterprise
"""

import os
import sys
import argparse
import yaml
from datetime import datetime
from typing import List, Dict, Optional
from io import StringIO
import contextlib

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import AIImpactModel


class AnalysisRunner:
    """Streamlined analysis runner with automatic output saving"""
    
    def __init__(self, output_dir: str = "outputs/reports"):
        self.output_dir = output_dir
        self.model = AIImpactModel()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def get_available_scenarios(self) -> List[str]:
        """Get list of available scenarios"""
        return list(self.model.scenarios.keys())
    
    def generate_filename(self, custom_name: Optional[str] = None) -> str:
        """Generate timestamped filename"""
        if custom_name:
            if not custom_name.endswith('.txt'):
                custom_name += '.txt'
            return os.path.join(self.output_dir, custom_name)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"analysis_{timestamp}.txt")
    
    def capture_scenario_output(self, scenario_name: str) -> tuple[Dict, str]:
        """Run scenario and capture both results and formatted output"""
        
        # Capture printed output
        output_buffer = StringIO()
        with contextlib.redirect_stdout(output_buffer):
            results = self.model.run_scenario(scenario_name)
            self.model.print_summary(results)
        
        captured_output = output_buffer.getvalue()
        return results, captured_output
    
    def run_single_scenario(self, scenario_name: str) -> tuple[Dict, str]:
        """Run a single scenario and return results"""
        
        print(f"🔄 Running scenario: {scenario_name}")
        
        if scenario_name not in self.get_available_scenarios():
            available = ", ".join(self.get_available_scenarios())
            raise ValueError(f"Scenario '{scenario_name}' not found. Available: {available}")
        
        results, output = self.capture_scenario_output(scenario_name)
        print("✅ Scenario completed")
        
        return results, output
    
    def run_multiple_scenarios(self, scenario_names: List[str]) -> tuple[List[Dict], str]:
        """Run multiple scenarios and return combined results"""
        
        all_results = []
        combined_output = []
        
        print(f"🔄 Running {len(scenario_names)} scenarios...")
        
        for i, scenario_name in enumerate(scenario_names, 1):
            print(f"  [{i}/{len(scenario_names)}] {scenario_name}")
            
            if scenario_name not in self.get_available_scenarios():
                print(f"  ⚠️  Skipping unknown scenario: {scenario_name}")
                continue
            
            results, output = self.capture_scenario_output(scenario_name)
            all_results.append(results)
            combined_output.append(output)
            print(f"  ✅ Completed: {scenario_name}")
        
        return all_results, "\n\n" + "="*80 + "\n\n".join(combined_output)
    
    def run_comparison(self, scenario_names: List[str] = None) -> str:
        """Run scenario comparison and return formatted output"""
        
        if scenario_names is None or scenario_names == ['all']:
            scenario_names = ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']
            print(f"🔄 Running comparison of standard scenarios...")
        else:
            print(f"🔄 Running comparison of: {', '.join(scenario_names)}")
        
        # Run all scenarios first
        for scenario_name in scenario_names:
            if scenario_name not in self.model.results:
                print(f"  Running {scenario_name}...")
                self.model.run_scenario(scenario_name)
        
        # Capture comparison output
        output_buffer = StringIO()
        with contextlib.redirect_stdout(output_buffer):
            self.model.compare_scenarios(scenario_names)
        
        print("✅ Comparison completed")
        return output_buffer.getvalue()
    
    def format_final_output(self, content: str, scenario_names: List[str], analysis_type: str) -> str:
        """Format the final output with header and footer"""
        
        header = f"""
{'='*80}
AI DEVELOPMENT IMPACT ANALYSIS REPORT
{'='*80}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Analysis Type: {analysis_type}
Scenarios: {', '.join(scenario_names)}
{'='*80}
"""
        
        footer = f"""
{'='*80}
END OF REPORT
Generated by AI Impact Analysis Tool
Report saved: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'='*80}
"""
        
        return header + content + footer
    
    def save_and_display_results(self, content: str, filename: str):
        """Save results to file and display summary"""
        
        with open(filename, 'w') as f:
            f.write(content)
        
        # Get relative path for display
        rel_path = os.path.relpath(filename)
        file_size = os.path.getsize(filename)
        
        print(f"\n📊 Analysis Complete!")
        print(f"📁 Results saved to: {rel_path}")
        print(f"📄 File size: {file_size:,} bytes")
        
        # Show first few lines as preview
        lines = content.split('\n')
        if len(lines) > 10:
            print(f"\n📋 Preview (first 10 lines):")
            print('-' * 40)
            for line in lines[:10]:
                print(line)
            print(f"... ({len(lines) - 10} more lines)")
        
        return rel_path


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Run AI impact analysis scenarios and save results to text files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_analysis.py moderate_enterprise
    python run_analysis.py startup enterprise scaleup
    python run_analysis.py --compare all
    python run_analysis.py --output my_analysis.txt moderate_enterprise
        """
    )
    
    parser.add_argument('scenarios', nargs='*', 
                       help='Scenario name(s) to run')
    parser.add_argument('--compare', '-c', action='store_true',
                       help='Run comparison mode')
    parser.add_argument('--output', '-o', type=str,
                       help='Custom output filename')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List available scenarios')
    
    args = parser.parse_args()
    
    runner = AnalysisRunner()
    
    # Handle list scenarios
    if args.list:
        scenarios = runner.get_available_scenarios()
        print("Available scenarios:")
        for scenario in scenarios:
            print(f"  • {scenario}")
        return
    
    # Validate arguments
    if not args.scenarios and not args.compare:
        print("❌ Error: Must specify scenarios or use --compare")
        print("Use --list to see available scenarios")
        parser.print_help()
        return
    
    try:
        # Determine analysis type and run
        if args.compare:
            analysis_type = "Scenario Comparison"
            scenario_names = args.scenarios if args.scenarios else ['all']
            content = runner.run_comparison(scenario_names)
            if scenario_names == ['all']:
                scenario_names = ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']
        
        elif len(args.scenarios) == 1:
            analysis_type = "Single Scenario"
            scenario_names = args.scenarios
            results, content = runner.run_single_scenario(args.scenarios[0])
        
        else:
            analysis_type = "Multiple Scenarios"
            scenario_names = args.scenarios
            results_list, content = runner.run_multiple_scenarios(args.scenarios)
        
        # Format and save output
        formatted_content = runner.format_final_output(content, scenario_names, analysis_type)
        filename = runner.generate_filename(args.output)
        runner.save_and_display_results(formatted_content, filename)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)