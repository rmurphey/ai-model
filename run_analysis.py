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
import re
from datetime import datetime
from typing import List, Dict, Optional
from io import StringIO
import contextlib

from main import AIImpactModel
from src.utils.colors import *
from src.utils.exceptions import ConfigurationError, ScenarioError, CalculationError, ValidationError


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
        
        print(info(f"🔄 Running scenario: {scenario_name}"))
        
        if scenario_name not in self.get_available_scenarios():
            raise ScenarioError(
                scenario_name=scenario_name,
                issue="not found in configuration",
                available_scenarios=self.get_available_scenarios(),
                config_file="src/scenarios/scenarios.yaml"
            )
        
        results, output = self.capture_scenario_output(scenario_name)
        print(success("✅ Scenario completed"))
        
        return results, output
    
    def run_multiple_scenarios(self, scenario_names: List[str]) -> tuple[List[Dict], str]:
        """Run multiple scenarios and return combined results"""
        
        all_results = []
        combined_output = []
        
        print(info(f"🔄 Running {len(scenario_names)} scenarios..."))
        
        for i, scenario_name in enumerate(scenario_names, 1):
            print(f"  {dim_text(f'[{i}/{len(scenario_names)}]')} {metric(scenario_name)}")
            
            if scenario_name not in self.get_available_scenarios():
                print(f"  {warning('⚠️  Skipping unknown scenario:')} {error(scenario_name)}")
                continue
            
            results, output = self.capture_scenario_output(scenario_name)
            all_results.append(results)
            combined_output.append(output)
            print(f"  {success('✅ Completed:')} {scenario_name}")
        
        return all_results, "\n\n" + "="*80 + "\n\n".join(combined_output)
    
    def run_comparison(self, scenario_names: List[str] = None) -> str:
        """Run scenario comparison and return formatted output"""
        
        if scenario_names is None or scenario_names == ['all']:
            scenario_names = ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']
            print(info("🔄 Running comparison of standard scenarios..."))
        else:
            print(info(f"🔄 Running comparison of: {', '.join(scenario_names)}"))
        
        # Run all scenarios first
        for scenario_name in scenario_names:
            if scenario_name not in self.model.results:
                print(f"  {dim_text('Running')} {metric(scenario_name)}...")
                self.model.run_scenario(scenario_name)
        
        # Capture comparison output
        output_buffer = StringIO()
        with contextlib.redirect_stdout(output_buffer):
            self.model.compare_scenarios(scenario_names)
        
        print(success("✅ Comparison completed"))
        return output_buffer.getvalue()
    
    def format_final_output(self, content: str, scenario_names: List[str], analysis_type: str) -> str:
        """Format the final output as markdown for file export"""
        
        header = f"""# AI Development Impact Analysis Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Analysis Type:** {analysis_type}  
**Scenarios:** {', '.join(scenario_names)}

---

"""
        
        # Convert plaintext content to markdown
        markdown_content = self._convert_to_markdown(content)
        
        footer = f"""

---

## Report Information

- **Generated by:** AI Impact Analysis Tool
- **Report saved:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Format:** Markdown
"""
        
        return header + markdown_content + footer
    
    def _convert_to_markdown(self, content: str) -> str:
        """Convert plaintext analysis output to markdown format"""
        # Strip ANSI color codes before processing
        content = re.sub(r'\x1b\[[0-9;]*m', '', content)
        
        lines = content.split('\n')
        markdown_lines = []
        
        for line in lines:
            # Convert headers
            if line.startswith('============================================================'):
                continue  # Skip separator lines
            elif line.startswith('Running Scenario:'):
                scenario = line.split(':', 1)[1].strip()
                markdown_lines.append(f"## Scenario: {scenario}")
            elif line.startswith('EXECUTIVE SUMMARY:'):
                summary = line.split(':', 1)[1].strip()
                markdown_lines.append(f"### Executive Summary: {summary}")
            elif line.startswith('------------------------------------------------------------'):
                continue  # Skip separator lines
            elif line.strip() in ['FINANCIAL METRICS', 'PER DEVELOPER METRICS', 'VALUE BREAKDOWN', 'OPPORTUNITY COST ANALYSIS']:
                markdown_lines.append(f"#### {line.strip()}")
            elif line.startswith('SCENARIO COMPARISON') or line.startswith('================'):
                if 'SCENARIO COMPARISON' in line:
                    markdown_lines.append("## Scenario Comparison")
                continue
            elif '|' in line and ('NPV' in line or 'ROI' in line or 'Scenario' in line):
                # Convert table rows to markdown table format
                if 'Scenario' in line:
                    # This is a table header
                    markdown_lines.append(line)
                    # Add markdown table separator
                    cols = line.count('|') + 1
                    markdown_lines.append('|' + '---|' * cols)
                else:
                    markdown_lines.append(line)
            else:
                # Regular content - check for key-value pairs
                if ':' in line and any(keyword in line for keyword in ['Team Size', 'NPV', 'ROI', 'Breakeven', 'Total', 'Annual', 'Value', 'Cost']):
                    # Format as markdown definition
                    if line.strip():
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            markdown_lines.append(f"- **{key}:** {value}")
                        else:
                            markdown_lines.append(line)
                    else:
                        markdown_lines.append("")
                else:
                    markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    def save_and_display_results(self, content: str, filename: str):
        """Save results to file and display summary"""
        
        with open(filename, 'w') as f:
            f.write(content)
        
        # Get relative path for display
        rel_path = os.path.relpath(filename)
        file_size = os.path.getsize(filename)
        
        print(f"\n{success('📊 Analysis Complete!')}")
        print(f"{info('📁 Results saved to:')} {header(rel_path)}")
        print(f"{metric('📄 File size:')} {info(f'{file_size:,} bytes')}")
        
        # Show first few lines as preview
        lines = content.split('\n')
        if len(lines) > 10:
            print(f"\n{header('📋 Preview (first 10 lines):')}")
            print(dim_text('-' * 40))
            for line in lines[:10]:
                print(dim_text(line))
            print(dim_text(f"... ({len(lines) - 10} more lines)"))
        
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
        print(header("Available scenarios:"))
        for scenario in scenarios:
            print(f"  {success('•')} {info(scenario)}")
        return
    
    # Validate arguments
    if not args.scenarios and not args.compare:
        print(error("❌ Error: Must specify scenarios or use --compare"))
        print(info("💡 Quick start:"))
        print(info("   • python run_analysis.py --list          (see available scenarios)"))
        print(info("   • python run_analysis.py moderate_enterprise  (run single scenario)"))
        print(info("   • python run_analysis.py --compare all   (compare all scenarios)"))
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
        
    except ConfigurationError as e:
        print(error(f"❌ {e}"))
        print(warning("\n🆘 Need help? Check the project documentation or create an issue."))
        return 1
    except ScenarioError as e:
        print(error(f"❌ {e}"))
        print(warning("\n🆘 Need help? Use 'python run_analysis.py --list' to see available scenarios."))
        return 1
    except (CalculationError, ValidationError) as e:
        print(error(f"❌ {e}"))
        print(warning("\n🆘 Need help? This may be a model configuration issue. Please check input parameters."))
        return 1
    except KeyboardInterrupt:
        print(warning("\n⏹️  Analysis interrupted by user"))
        return 130
    except FileNotFoundError as e:
        print(error(f"❌ File not found: {e}"))
        print(warning("🔧 Resolution Steps:"))
        print(warning("   1. Check if the file path is correct"))
        print(warning("   2. Ensure you're running from the project root directory"))
        print(warning("   3. Verify all required files are present"))
        return 2
    except PermissionError as e:
        print(error(f"❌ Permission denied: {e}"))
        print(warning("🔧 Resolution Steps:"))
        print(warning("   1. Check file permissions (ls -la)"))
        print(warning("   2. Ensure you have read/write access to the directory"))
        print(warning("   3. Try running with appropriate permissions"))
        return 13
    except Exception as e:
        print(error(f"❌ Unexpected error: {e}"))
        print(warning("🔧 Resolution Steps:"))
        print(warning("   1. Check Python version compatibility (>=3.8)"))
        print(warning("   2. Verify all dependencies are installed (pip install -r requirements.txt)"))
        print(warning("   3. Try running with --verbose flag if available"))
        print(warning("   4. Report this issue with full error details if problem persists"))
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)