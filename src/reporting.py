"""Reporting Orchestration Module

This module handles report generation using Quarto, including data aggregation,
plot generation with matplotlib/seaborn, and Quarto CLI invocation.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
import matplotlib.pyplot as plt
import seaborn as sns
import polars as pl
import numpy as np

from .config import MainConfig


class ReportingError(Exception):
    """Raised when report generation fails."""
    pass


class QuartoNotFoundError(ReportingError):
    """Raised when Quarto CLI is not found."""
    pass


def _generate_histogram(data: np.ndarray, output_path: Path, config: MainConfig) -> None:
    """Generate histogram plot of participant results.
    
    Args:
        data: Array of participant results.
        output_path: Path to save the plot.
        config: Configuration object with plot settings.
    """
    try:
        plt.figure(figsize=(10, 6))
        
        # Get histogram configuration
        bins = config.reporting.plots.histogram_bins
        
        # Create histogram
        plt.hist(data, bins=bins, alpha=0.7, edgecolor='black', 
                density=True, label='Participant Results')
        
        # Add labels and title
        plt.xlabel('Result Value')
        plt.ylabel('Density')
        plt.title('Distribution of Participant Results')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Add summary statistics as text
        mean_val = np.mean(data)
        std_val = np.std(data, ddof=1)
        plt.axvline(mean_val, color='red', linestyle='--', alpha=0.8, label=f'Mean: {mean_val:.4f}')
        plt.text(0.02, 0.98, f'Mean: {mean_val:.4f}\\nStd: {std_val:.4f}\\nN: {len(data)}',
                transform=plt.gca().transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Save the plot
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        raise ReportingError(f"Failed to generate histogram: {e}")


def _generate_density_plot(data: np.ndarray, output_path: Path) -> None:
    """Generate density plot of participant results.
    
    Args:
        data: Array of participant results.
        output_path: Path to save the plot.
    """
    try:
        plt.figure(figsize=(10, 6))
        
        # Create density plot using seaborn
        sns.kdeplot(data, fill=True, alpha=0.7, label='Kernel Density Estimate')
        
        # Add histogram for comparison
        plt.hist(data, bins=30, alpha=0.3, density=True, color='gray', label='Histogram')
        
        # Add labels and title
        plt.xlabel('Result Value')
        plt.ylabel('Density')
        plt.title('Density Distribution of Participant Results')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Save the plot
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        raise ReportingError(f"Failed to generate density plot: {e}")


def _write_quarto_data_json(report_data: Dict[str, Any], output_path: Path) -> None:
    """Write report data to JSON file for Quarto template.
    
    Args:
        report_data: Dictionary containing all report data.
        output_path: Path to save the JSON file.
    """
    try:
        # Convert numpy arrays to lists for JSON serialization
        json_data = {}
        for key, value in report_data.items():
            if isinstance(value, np.ndarray):
                json_data[key] = value.tolist()
            elif isinstance(value, (np.integer, np.floating)):
                json_data[key] = float(value)
            else:
                json_data[key] = value
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        raise ReportingError(f"Failed to write report data JSON: {e}")


def _create_default_quarto_template(template_path: Path) -> None:
    """Create a default Quarto template if none exists.
    
    Args:
        template_path: Path where template should be created.
    """
    template_content = '''---
title: "Proficiency Testing Report"
format: 
  pdf:
    toc: true
    number-sections: true
  html:
    toc: true
    number-sections: true
date: now
---

```{{python}}
#| echo: false
import json
from pathlib import Path

# Load report data
with open('{{data_file}}', 'r') as f:
    data = json.load(f)
```

# Executive Summary

This report presents the results of proficiency testing analysis conducted using the PT-CLI tool.

## Input Data Summary

- **Number of participants**: `{{python}} len(data['participant_ids'])`
- **Calculation method**: `{{python}} data['config']['calculation']['method']`
- **Standard deviation (σ_pt)**: `{{python}} data['config']['calculation']['sigma_pt']`

## Results

### Assigned Value and Uncertainty

- **Assigned value (x_pt)**: `{{python}} f"{data['results']['x_pt']:.6f}" if 'x_pt' in data['results'] else "Not calculated"`
- **Uncertainty (u(x_pt))**: `{{python}} f"{data['results']['u_x_pt']:.6f}" if 'u_x_pt' in data['results'] else "Not calculated"`

### Participant Results Distribution

```{{python}}
#| echo: false
#| fig-cap: "Distribution of participant results"

import matplotlib.pyplot as plt
import numpy as np

if 'participant_results' in data:
    results = np.array(data['participant_results'])
    plt.figure(figsize=(10, 6))
    plt.hist(results, bins=30, alpha=0.7, edgecolor='black', density=True)
    plt.xlabel('Result Value')
    plt.ylabel('Density')
    plt.title('Distribution of Participant Results')
    plt.grid(True, alpha=0.3)
    
    # Add statistics
    mean_val = np.mean(results)
    std_val = np.std(results, ddof=1)
    plt.axvline(mean_val, color='red', linestyle='--', alpha=0.8)
    plt.text(0.02, 0.98, f'Mean: {mean_val:.4f}\\nStd: {std_val:.4f}\\nN: {len(results)}',
            transform=plt.gca().transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    plt.tight_layout()
    plt.show()
```

{{#if plot_paths}}
### Additional Plots

{{#if plot_paths.histogram}}
![Histogram of Results]({{plot_paths.histogram}})
{{/if}}

{{#if plot_paths.density}}
![Density Plot]({{plot_paths.density}})
{{/if}}
{{/if}}

## Statistical Summary

```{{python}}
#| echo: false

if 'participant_results' in data:
    import numpy as np
    results = np.array(data['participant_results'])
    
    summary_stats = {
        'Count': len(results),
        'Mean': np.mean(results),
        'Std Dev': np.std(results, ddof=1),
        'Min': np.min(results),
        'Max': np.max(results),
        'Median': np.median(results),
        'Q1': np.percentile(results, 25),
        'Q3': np.percentile(results, 75)
    }
    
    # Simple table formatting without pandas
    print("| Statistic | Value |")
    print("|-----------|-------|")
    for stat, value in summary_stats.items():
        print(f"| {stat} | {value:.6f} |")
```

---

*Report generated using PT-CLI*
'''
    
    try:
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    except Exception as e:
        raise ReportingError(f"Failed to create default template: {e}")


def _invoke_quarto(template_path: Path, output_path: Path, output_format: str, 
                  data_file_path: Path) -> None:
    """Invoke Quarto CLI to generate the report.
    
    Args:
        template_path: Path to Quarto template file.
        output_path: Path for output report.
        output_format: Output format (pdf, html, docx).
        data_file_path: Path to JSON data file.
    """
    try:
        # Check if Quarto is available
        subprocess.run(['quarto', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise QuartoNotFoundError(
            "Quarto CLI not found. Please install Quarto from https://quarto.org"
        )
    
    try:
        # Build Quarto command
        cmd = [
            'quarto', 'render', str(template_path),
            '--to', output_format,
            '--output', str(output_path),
            '--metadata', f'data_file={data_file_path}'
        ]
        
        # Execute Quarto command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
    except subprocess.CalledProcessError as e:
        raise ReportingError(
            f"Quarto rendering failed with exit code {e.returncode}. "
            f"Error output: {e.stderr}"
        )
    except Exception as e:
        raise ReportingError(f"Failed to invoke Quarto: {e}")


def generate_report(report_data: Dict[str, Any], config: MainConfig, 
                   output_path: Path, output_format: str) -> None:
    """Generate report using Quarto.
    
    Args:
        report_data: Dictionary containing all data for the report.
        config: Configuration object with reporting settings.
        output_path: Path for output report (without extension).
        output_format: Output format (pdf, html, docx).
        
    Raises:
        ReportingError: If report generation fails.
        QuartoNotFoundError: If Quarto CLI is not found.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Generate plots if enabled
        plot_paths = {}
        if config.reporting.plots.generate_histogram and 'participant_results' in report_data:
            histogram_path = temp_dir_path / 'histogram.png'
            _generate_histogram(
                np.array(report_data['participant_results']), 
                histogram_path, 
                config
            )
            plot_paths['histogram'] = str(histogram_path)
            
            # Also generate density plot
            density_path = temp_dir_path / 'density.png'
            _generate_density_plot(
                np.array(report_data['participant_results']), 
                density_path
            )
            plot_paths['density'] = str(density_path)
        
        # Add plot paths to report data
        if plot_paths:
            report_data['plot_paths'] = plot_paths
        
        # Write report data to JSON
        data_file_path = temp_dir_path / 'report_data.json'
        _write_quarto_data_json(report_data, data_file_path)
        
        # Determine template path
        if config.reporting.custom_template:
            template_path = config.reporting.custom_template
            if not template_path.exists():
                raise ReportingError(f"Custom template not found: {template_path}")
        else:
            # Create default template
            template_path = temp_dir_path / 'default_template.qmd'
            _create_default_quarto_template(template_path)
        
        # Ensure output path has correct extension
        output_extensions = {'pdf': '.pdf', 'html': '.html', 'docx': '.docx'}
        final_output_path = output_path.with_suffix(output_extensions[output_format])
        
        # Invoke Quarto
        _invoke_quarto(template_path, final_output_path, output_format, data_file_path)


def aggregate_report_data(input_data: pl.DataFrame, config: MainConfig, 
                         calculation_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Aggregate all data needed for the report.
    
    Args:
        input_data: Validated input DataFrame.
        config: Configuration object.
        calculation_results: Results from calculation engine (if available).
        
    Returns:
        Dictionary containing all report data.
    """
    # Extract participant results
    result_col = config.input_data.result_col
    participant_results = input_data.get_column(result_col).to_numpy()
    
    report_data = {
        'participant_ids': input_data.get_column(config.input_data.participant_id_col).to_list(),
        'participant_results': participant_results.tolist(),
        'config': {
            'calculation': {
                'method': config.calculation.method,
                'sigma_pt': config.calculation.sigma_pt
            },
            'input_data': {
                'participant_id_col': config.input_data.participant_id_col,
                'result_col': config.input_data.result_col,
                'uncertainty_col': config.input_data.uncertainty_col
            }
        },
        'summary_statistics': {
            'count': len(participant_results),
            'mean': float(np.mean(participant_results)),
            'std': float(np.std(participant_results, ddof=1)),
            'min': float(np.min(participant_results)),
            'max': float(np.max(participant_results)),
            'median': float(np.median(participant_results))
        }
    }
    
    # Add calculation results if available
    if calculation_results:
        report_data['results'] = calculation_results
    
    # Add uncertainty data if available
    uncertainty_col = config.input_data.uncertainty_col
    if uncertainty_col and uncertainty_col in input_data.columns:
        uncertainties = input_data.get_column(uncertainty_col).to_numpy()
        report_data['participant_uncertainties'] = uncertainties.tolist()
    
    return report_data