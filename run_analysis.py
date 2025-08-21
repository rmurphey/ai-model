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
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from io import StringIO
import contextlib

from main import AIImpactModel
from src.utils.colors import *
from src.utils.exceptions import ConfigurationError, ScenarioError, CalculationError, ValidationError
from src.model.baseline import calculate_opportunity_cost
from src.analysis.terminal_visualizations import create_sparkline
from src.config.version import get_current_version_string
import numpy as np


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
            if not custom_name.endswith('.md'):
                custom_name += '.md'
            return os.path.join(self.output_dir, custom_name)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"analysis_{timestamp}.md")
    
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
    
    def format_final_output(self, results_data, scenario_names: List[str], analysis_type: str) -> str:
        """Generate markdown output directly from results data"""
        
        generation_time = datetime.now()
        report_id = hashlib.md5(f"{analysis_type}_{','.join(scenario_names)}_{generation_time.isoformat()}".encode()).hexdigest()[:8]
        
        header = f"""# AI Development Impact Analysis Report

**Generated:** {generation_time.strftime("%Y-%m-%d %H:%M:%S")}  
**Analysis Type:** {analysis_type}  
**Scenarios:** {', '.join(scenario_names)}  
**Report ID:** `{report_id}`  
**Python Version:** {sys.version.split()[0]}  
**Analysis Tool Version:** v{get_current_version_string()}

---

"""
        
        # Generate markdown content directly from results
        if analysis_type == "Single Scenario":
            markdown_content = self._generate_single_scenario_markdown(results_data, scenario_names[0])
        elif analysis_type == "Multiple Scenarios":
            markdown_content = self._generate_multiple_scenarios_markdown(results_data, scenario_names)
        elif analysis_type == "Scenario Comparison":
            markdown_content = self._generate_comparison_markdown(scenario_names)
        else:
            markdown_content = "Analysis completed successfully."
        
        # Calculate checksums for reproducibility
        scenario_config_text = self._format_scenario_configs(scenario_names)
        resolved_params_text = self._format_resolved_parameters(results_data, analysis_type)
        config_checksum = hashlib.md5(scenario_config_text.encode()).hexdigest()[:8]
        params_checksum = hashlib.md5(resolved_params_text.encode()).hexdigest()[:8]
        
        footer = f"""

---

## Report Information

- **Generated by:** AI Impact Analysis Tool v{get_current_version_string()}
- **Report saved:** {generation_time.strftime("%Y-%m-%d %H:%M:%S")}
- **Report ID:** `{report_id}`
- **Format:** Markdown
- **Environment:** Python {sys.version.split()[0]} on {sys.platform}

### Reproducibility

**Command used:**
```bash
python run_analysis.py {self._format_command(scenario_names, analysis_type)}
```

**Verification checksums:**
- Config checksum: `{config_checksum}`
- Parameters checksum: `{params_checksum}`
- Report ID: `{report_id}`

**Data sources:**
- Scenario configuration: `src/scenarios/scenarios.yaml` (at time of generation)
- Analysis engine: AI Impact Model v{get_current_version_string()}
- Date generated: {generation_time.strftime("%Y-%m-%d %H:%M:%S")}

**To reproduce these exact results:**

1. **Automatic reproduction:**
   ```bash
   python reproduce_results.py {os.path.join(self.output_dir, f"analysis_{generation_time.strftime('%Y%m%d_%H%M%S')}.md")}
   ```

2. **Manual reproduction:**
   ```bash
   python run_analysis.py {self._format_command(scenario_names, analysis_type)}
   ```

3. **Exact reproduction with embedded config:**
   Create a temporary scenario file with the configuration below and run:
   ```bash
   python main.py --scenario <scenario_name>
   ```

**Complete scenario configuration used:**
{scenario_config_text}

**Resolved parameter values used in calculations:**
{resolved_params_text}

**Note:** This embedded data ensures exact reproducibility even if scenario definitions change. Use the `reproduce_results.py` tool to automatically validate and reproduce these results.
"""
        
        return header + markdown_content + footer
    
    def _generate_single_scenario_markdown(self, results: Dict, scenario_name: str) -> str:
        """Generate comprehensive markdown for a single scenario analysis"""
        
        # Extract time series data
        months = len(results['adoption'])
        month_labels = [f"M{i+1}" for i in range(min(months, 12))]  # Show first 12 months
        
        # Create sparklines for key metrics
        adoption_sparkline = create_sparkline([a * 100 for a in results['adoption']], width=24)
        efficiency_sparkline = create_sparkline([e * 100 for e in results['efficiency']], width=24)
        value_sparkline = create_sparkline(results['value'][:min(months, 24)], width=24)
        cumulative_value_sparkline = create_sparkline(results['cumulative_value'][:min(months, 24)], width=24)
        cost_sparkline = create_sparkline(results['costs']['total'][:min(months, 24)], width=24)
        
        markdown = f"""## Scenario Analysis: {scenario_name}

### Executive Summary

| Metric | Value | Trend |
|--------|-------|-------|
| **Team Size** | {results['baseline'].team_size} developers | |
| **Analysis Timeframe** | {results['config']['timeframe_months']} months | |
| **Peak Adoption Rate** | {results['peak_adoption']*100:.1f}% | `{adoption_sparkline}` |
| **Final Efficiency** | {results['efficiency'][-1]*100:.1f}% | `{efficiency_sparkline}` |

### Financial Performance

| Metric | Value | Monthly Trend |
|--------|-------|---------------|
| **Total Investment (3 years)** | ${results['total_cost_3y']:,.0f} | `{cost_sparkline}` |
| **Total Value Created (3 years)** | ${results['total_value_3y']:,.0f} | `{cumulative_value_sparkline}` |
| **Net Present Value (NPV)** | ${results['npv']:,.0f} | |
| **Return on Investment (ROI)** | {results['roi_percent']:.1f}% | |
| **Breakeven Point** | {"Month " + str(results['breakeven_month']) if results['breakeven_month'] else "Not reached within timeframe"} | |

### Monthly Value Creation

Monthly value generation over time:

```
{value_sparkline}
```

| Metric | Value |
|--------|-------|
| **Peak Monthly Value** | ${max(results['value']):,.0f} |
| **Average Monthly Value** | ${np.mean(results['value']):,.0f} |
| **Final Month Value** | ${results['value'][-1]:,.0f} |

### Adoption Dynamics

The adoption curve shows how developers embrace AI tools over time:

```
Adoption Rate: {adoption_sparkline}
Efficiency:    {efficiency_sparkline}
```

| Phase | Adoption Rate | Efficiency | Effective Impact |
|-------|---------------|------------|------------------|
| **Month 1** | {results['adoption'][0]*100:.1f}% | {results['efficiency'][0]*100:.1f}% | {results['effective_adoption'][0]*100:.1f}% |
| **Month 6** | {results['adoption'][5]*100:.1f}% | {results['efficiency'][5]*100:.1f}% | {results['effective_adoption'][5]*100:.1f}% |
| **Month 12** | {results['adoption'][11]*100:.1f}% | {results['efficiency'][11]*100:.1f}% | {results['effective_adoption'][11]*100:.1f}% |
| **Peak** | {results['peak_adoption']*100:.1f}% | {max(results['efficiency'])*100:.1f}% | {max(results['effective_adoption'])*100:.1f}% |

### Cost Structure Analysis

| Cost Component | Monthly Average | Total (3 years) | Per Developer |
|----------------|-----------------|-----------------|---------------|
| **License Costs** | ${np.mean(results['costs']['licensing']):,.0f} | ${sum(results['costs']['licensing'][:36]):,.0f} | ${results['annual_cost_per_dev']:,.0f}/year |
| **Training & Setup** | ${np.mean(results['costs']['training']):,.0f} | ${sum(results['costs']['training'][:36]):,.0f} | |
| **Total Costs** | ${np.mean(results['costs']['total']):,.0f} | ${results['total_cost_3y']:,.0f} | |

### Per Developer Metrics

| Metric | Value | Annual Comparison |
|--------|-------|-------------------|
| **Annual Cost per Developer** | ${results['annual_cost_per_dev']:,.0f} | vs ${results['baseline'].weighted_avg_flc:,.0f} FLC |
| **Annual Value per Developer** | ${results['annual_value_per_dev']:,.0f} | {(results['annual_value_per_dev']/results['baseline'].weighted_avg_flc)*100:.1f}% of FLC |
| **Net Value per Developer** | ${results['annual_value_per_dev'] - results['annual_cost_per_dev']:,.0f} | ROI: {((results['annual_value_per_dev']/results['annual_cost_per_dev'])-1)*100:.0f}% |

### Value Breakdown

The total annual value of ${results['impact_breakdown']['total_annual_value']:,.0f} comes from:

| Value Source | Annual Impact | % of Total | Per Developer |
|-------------|---------------|------------|---------------|
| **Time-to-Market Acceleration** | ${results['impact_breakdown']['time_value']:,.0f} | {(results['impact_breakdown']['time_value']/results['impact_breakdown']['total_annual_value'])*100:.1f}% | ${results['impact_breakdown']['time_value']/results['baseline'].team_size:,.0f} |
| **Quality Improvements** | ${results['impact_breakdown']['quality_value']:,.0f} | {(results['impact_breakdown']['quality_value']/results['impact_breakdown']['total_annual_value'])*100:.1f}% | ${results['impact_breakdown']['quality_value']/results['baseline'].team_size:,.0f} |
| **Capacity Reallocation** | ${results['impact_breakdown']['capacity_value']:,.0f} | {(results['impact_breakdown']['capacity_value']/results['impact_breakdown']['total_annual_value'])*100:.1f}% | ${results['impact_breakdown']['capacity_value']/results['baseline'].team_size:,.0f} |
| **Strategic Initiatives** | ${results['impact_breakdown']['strategic_value']:,.0f} | {(results['impact_breakdown']['strategic_value']/results['impact_breakdown']['total_annual_value'])*100:.1f}% | ${results['impact_breakdown']['strategic_value']/results['baseline'].team_size:,.0f} |

### Opportunity Cost Analysis

| Metric | Annual Value | Monthly Impact |
|--------|-------------|----------------|
| **Current Inefficiency Cost** | ${self._calculate_opportunity_cost(results['baseline']):,.0f} | ${self._calculate_opportunity_cost(results['baseline'])/12:,.0f} |
| **AI Tool Value Capture** | ${results['impact_breakdown']['total_annual_value']:,.0f} | ${results['impact_breakdown']['total_annual_value']/12:,.0f} |
| **Net Efficiency Gain** | ${results['impact_breakdown']['total_annual_value'] - results['total_cost_3y']/3:,.0f} | ${(results['impact_breakdown']['total_annual_value'] - results['total_cost_3y']/3)/12:,.0f} |
| **Efficiency Improvement** | {(results['impact_breakdown']['total_annual_value']/self._calculate_opportunity_cost(results['baseline']))*100:.1f}% | |

### Monthly Timeline

First 12 months progression:

| Month | Adoption | Efficiency | Monthly Value | Cumulative Value | Monthly Cost | Net Flow |
|-------|----------|------------|---------------|------------------|--------------|----------|
{self._generate_monthly_table(results, 12)}

### Key Insights & Recommendations

#### 📈 **Performance Summary**
- **Investment Recovery**: {"🟢 Strong positive ROI with breakeven in " + str(results['breakeven_month']) + " months" if results['breakeven_month'] and results['breakeven_month'] <= 12 else "🟡 Longer-term investment with " + ("breakeven in " + str(results['breakeven_month']) + " months" if results['breakeven_month'] else "🔴 breakeven beyond analysis period")}
- **Adoption Success**: {"🟢 High adoption rate" if results['peak_adoption'] > 0.7 else "🟡 Moderate adoption rate" if results['peak_adoption'] > 0.4 else "🔴 Low adoption rate"} of {results['peak_adoption']*100:.1f}% achieved
- **Value Creation**: ${results['annual_value_per_dev']:,.0f} annual value per developer
- **Cost Efficiency**: ${results['annual_cost_per_dev']:,.0f} annual cost per developer

#### 💡 **Strategic Recommendations**
- **Primary Value Driver**: {self._get_primary_value_driver(results['impact_breakdown'])} acceleration provides the highest value
- **ROI Timeframe**: {self._get_roi_timeframe_assessment(results['breakeven_month'])}
- **Adoption Focus**: {"🎯 Focus on maintaining high adoption rates" if results['peak_adoption'] > 0.7 else "📈 Invest in training and change management to improve adoption" if results['peak_adoption'] > 0.4 else "🚨 Significant adoption challenges require intervention"}
"""
        return markdown
    
    def _generate_multiple_scenarios_markdown(self, results_list: List[Dict], scenario_names: List[str]) -> str:
        """Generate markdown for multiple scenario analysis"""
        
        markdown = "## Multiple Scenario Analysis\n\n"
        
        for i, (results, scenario_name) in enumerate(zip(results_list, scenario_names)):
            markdown += f"### {i+1}. {scenario_name}\n\n"
            markdown += f"- **NPV**: ${results['npv']:,.0f}\n"
            markdown += f"- **ROI**: {results['roi_percent']:.1f}%\n"
            markdown += f"- **Breakeven**: {"Month " + str(results['breakeven_month']) if results['breakeven_month'] else "Not reached"}\n"
            markdown += f"- **Peak Adoption**: {results['peak_adoption']*100:.1f}%\n\n"
        
        return markdown
    
    def _generate_comparison_markdown(self, scenario_names: List[str]) -> str:
        """Generate markdown for scenario comparison"""
        
        # Get comparison data from the model
        comparison_data = []
        for name in scenario_names:
            if name in self.model.results:
                r = self.model.results[name]
                comparison_data.append({
                    'Scenario': name,
                    'NPV': f"${r['npv']:,.0f}",
                    'ROI': f"{r['roi_percent']:.1f}%",
                    'Breakeven': f"Month {r['breakeven_month']}" if r['breakeven_month'] else "N/A",
                    'Peak Adoption': f"{r['peak_adoption']*100:.1f}%",
                    'Cost/Dev/Year': f"${r['annual_cost_per_dev']:,.0f}",
                    'Value/Dev/Year': f"${r['annual_value_per_dev']:,.0f}"
                })
        
        markdown = "## Scenario Comparison\n\n"
        
        if comparison_data:
            markdown += "| Scenario | NPV | ROI | Breakeven | Peak Adoption | Cost/Dev/Year | Value/Dev/Year |\n"
            markdown += "|----------|-----|-----|-----------|---------------|---------------|----------------|\n"
            
            for row in comparison_data:
                markdown += f"| {row['Scenario']} | {row['NPV']} | {row['ROI']} | {row['Breakeven']} | {row['Peak Adoption']} | {row['Cost/Dev/Year']} | {row['Value/Dev/Year']} |\n"
        
        return markdown
    
    def _calculate_opportunity_cost(self, baseline) -> float:
        """Calculate opportunity cost from baseline"""
        opportunity = calculate_opportunity_cost(baseline)
        return opportunity['total_opportunity_cost']
    
    def _generate_monthly_table(self, results: Dict, num_months: int) -> str:
        """Generate monthly progression table"""
        table_rows = []
        for i in range(min(num_months, len(results['adoption']))):
            month = i + 1
            adoption = results['adoption'][i] * 100
            efficiency = results['efficiency'][i] * 100
            monthly_value = results['value'][i]
            cumulative_value = results['cumulative_value'][i]
            monthly_cost = results['costs']['total'][i]
            net_flow = monthly_value - monthly_cost
            
            table_rows.append(f"| M{month} | {adoption:.1f}% | {efficiency:.1f}% | ${monthly_value:,.0f} | ${cumulative_value:,.0f} | ${monthly_cost:,.0f} | ${net_flow:,.0f} |")
        
        return '\n'.join(table_rows)
    
    def _get_primary_value_driver(self, impact_breakdown: Dict) -> str:
        """Determine the primary value driver from impact breakdown"""
        values = {
            'Time-to-Market': impact_breakdown['time_value'],
            'Quality': impact_breakdown['quality_value'], 
            'Capacity': impact_breakdown['capacity_value'],
            'Strategic': impact_breakdown['strategic_value']
        }
        return max(values, key=values.get)
    
    def _get_roi_timeframe_assessment(self, breakeven_month) -> str:
        """Get ROI timeframe assessment text"""
        if breakeven_month and breakeven_month <= 6:
            return "✅ Quick payback makes this a low-risk investment"
        elif breakeven_month and breakeven_month <= 18:
            return "⚠️ Longer payback period requires sustained commitment"
        else:
            return "⚠️ Long-term investment requiring careful change management"
    
    def _format_command(self, scenario_names: List[str], analysis_type: str) -> str:
        """Format the command used to generate this report"""
        if analysis_type == "Scenario Comparison":
            if scenario_names == ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']:
                return "--compare"
            else:
                return f"--compare {' '.join(scenario_names)}"
        else:
            return ' '.join(scenario_names)
    
    def _format_scenario_configs(self, scenario_names: List[str]) -> str:
        """Format complete scenario configurations for reproducibility"""
        config_details = []
        
        for scenario_name in scenario_names:
            if scenario_name in self.model.scenarios:
                config = self.model.scenarios[scenario_name]
                
                # Convert config to YAML format for complete reproducibility
                import yaml
                yaml_config = yaml.dump(config, default_flow_style=False, indent=2)
                
                config_details.append(f"""
**{scenario_name}:**
```yaml
{yaml_config.strip()}
```""")
        
        return '\n'.join(config_details) if config_details else "Configuration details not available"
    
    def _format_resolved_parameters(self, results_data, analysis_type: str) -> str:
        """Format the actual resolved parameter values used in calculations"""
        if analysis_type == "Single Scenario" and results_data:
            return self._format_single_scenario_parameters(results_data)
        elif analysis_type == "Multiple Scenarios" and results_data:
            return self._format_multiple_scenario_parameters(results_data)
        elif analysis_type == "Scenario Comparison":
            return self._format_comparison_parameters()
        else:
            return "Parameter details not available"
    
    def _format_single_scenario_parameters(self, results: Dict) -> str:
        """Format resolved parameters for a single scenario"""
        baseline = results['baseline']
        config = results['config']
        
        # Helper to convert numpy values to native Python types
        def to_python_type(value):
            if hasattr(value, 'item'):  # numpy scalar
                return value.item()
            elif isinstance(value, dict):
                return {k: to_python_type(v) for k, v in value.items()}
            else:
                return value
        
        # Extract all the actual values used
        parameter_data = {
            'baseline_metrics': {
                'team_size': int(baseline.team_size),
                'junior_ratio': float(baseline.junior_ratio),
                'mid_ratio': float(baseline.mid_ratio), 
                'senior_ratio': float(baseline.senior_ratio),
                'junior_flc': int(baseline.junior_flc),
                'mid_flc': int(baseline.mid_flc),
                'senior_flc': int(baseline.senior_flc),
                'weighted_avg_flc': float(baseline.weighted_avg_flc),
                'avg_feature_cycle_days': int(baseline.avg_feature_cycle_days),
                'avg_bug_fix_hours': int(baseline.avg_bug_fix_hours),
                'defect_escape_rate': float(baseline.defect_escape_rate),
                'production_incidents_per_month': int(baseline.production_incidents_per_month),
                'avg_incident_cost': int(baseline.avg_incident_cost),
                'rework_percentage': float(baseline.rework_percentage),
                'new_feature_percentage': float(baseline.new_feature_percentage),
                'maintenance_percentage': float(baseline.maintenance_percentage),
                'tech_debt_percentage': float(baseline.tech_debt_percentage),
            },
            'analysis_parameters': {
                'timeframe_months': int(config['timeframe_months']),
                'discount_rate_annual': 0.12,  # From constants
            },
            'impact_breakdown': to_python_type(results['impact_breakdown']),
            'final_metrics': {
                'peak_adoption': to_python_type(results['peak_adoption']),
                'breakeven_month': results['breakeven_month'],
                'npv': to_python_type(results['npv']),
                'roi_percent': to_python_type(results['roi_percent']),
                'total_cost_3y': to_python_type(results['total_cost_3y']),
                'total_value_3y': to_python_type(results['total_value_3y']),
            }
        }
        
        import yaml
        yaml_params = yaml.dump(parameter_data, default_flow_style=False, indent=2)
        
        return f"""
```yaml
{yaml_params.strip()}
```"""
    
    def _format_multiple_scenario_parameters(self, results_list: List[Dict]) -> str:
        """Format resolved parameters for multiple scenarios"""
        all_params = {}
        for i, results in enumerate(results_list):
            scenario_name = results['scenario_name']
            single_params = self._extract_scenario_params(results)
            all_params[scenario_name] = single_params
        
        import yaml
        yaml_params = yaml.dump(all_params, default_flow_style=False, indent=2)
        
        return f"""
```yaml
{yaml_params.strip()}
```"""
    
    def _format_comparison_parameters(self) -> str:
        """Format resolved parameters for comparison scenarios"""
        all_params = {}
        comparison_scenarios = ['conservative_startup', 'moderate_enterprise', 'aggressive_scaleup']
        
        for scenario_name in comparison_scenarios:
            if scenario_name in self.model.results:
                results = self.model.results[scenario_name]
                all_params[scenario_name] = self._extract_scenario_params(results)
        
        import yaml
        yaml_params = yaml.dump(all_params, default_flow_style=False, indent=2)
        
        return f"""
```yaml
{yaml_params.strip()}
```"""
    
    def _extract_scenario_params(self, results: Dict) -> Dict:
        """Extract key parameters from scenario results"""
        baseline = results['baseline']
        
        # Helper to convert numpy values to native Python types
        def to_python_type(value):
            if hasattr(value, 'item'):  # numpy scalar
                return value.item()
            elif isinstance(value, dict):
                return {k: to_python_type(v) for k, v in value.items()}
            else:
                return value
        
        return {
            'team_size': int(baseline.team_size),
            'weighted_avg_flc': float(baseline.weighted_avg_flc),
            'timeframe_months': int(results['config']['timeframe_months']),
            'peak_adoption': to_python_type(results['peak_adoption']),
            'breakeven_month': results['breakeven_month'],
            'npv': to_python_type(results['npv']),
            'roi_percent': to_python_type(results['roi_percent']),
            'impact_breakdown': to_python_type(results['impact_breakdown'])
        }
    
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
            results_data = None  # Comparison uses model.results internally
        
        elif len(args.scenarios) == 1:
            analysis_type = "Single Scenario"
            scenario_names = args.scenarios
            results_data, content = runner.run_single_scenario(args.scenarios[0])
        
        else:
            analysis_type = "Multiple Scenarios"
            scenario_names = args.scenarios
            results_data, content = runner.run_multiple_scenarios(args.scenarios)
        
        # Format and save output
        formatted_content = runner.format_final_output(results_data, scenario_names, analysis_type)
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