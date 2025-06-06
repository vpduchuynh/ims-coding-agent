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
params:
  data_file: ""
---

```{{python}}
#| echo: false
import json
from pathlib import Path

# Load report data
with open(params.data_file, 'r') as f:
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

- **Assigned value (x_pt)**: `{{python}} f"{data['results']['x_pt']:.6f}" if 'results' in data and 'x_pt' in data['results'] else "Not calculated"`
- **Uncertainty (u(x_pt))**: `{{python}} f"{data['results']['u_x_pt']:.6f}" if 'results' in data and 'u_x_pt' in data['results'] else "Not calculated"`

```{{python}}
#| echo: false
# Additional results if available
if 'results' in data:
    results = data['results']
    
    # Show robust standard deviation if available
    if 'calculation_details' in results and 's_star' in results['calculation_details']:
        s_star = results['calculation_details']['s_star']
        print(f"- **Robust standard deviation (s*)**: {s_star:.6f}")
    
    # Show participants used if available  
    if 'calculation_details' in results and 'participants_used' in results['calculation_details']:
        participants_used = results['calculation_details']['participants_used']
        print(f"- **Number of participants in calculation**: {participants_used}")
    
    # Show method details
    if 'method_used' in results:
        print(f"- **Calculation method**: {results['method_used']}")
    
    if 'sigma_pt_used' in results:
        print(f"- **σ_pt used for assessment**: {results['sigma_pt_used']}")
```

## Methodology

```{{python}}
#| echo: false
if 'results' in data and 'method_used' in data['results']:
    method = data['results']['method_used']
    print(f"The assigned value (x_pt) was determined using the **{method}** method.")
    
    if method == "AlgorithmA":
        print("This method implements Algorithm A from ISO 13528:2022, Annex C, which uses robust statistics to determine the assigned value and its uncertainty.")
    elif method == "CRM":
        print("This method uses a Certified Reference Material (CRM) as the basis for the assigned value.")
    elif method == "Formulation":
        print("This method uses theoretical formulation values as the basis for the assigned value.")
    elif method == "Expert":
        print("This method uses expert consensus values as the basis for the assigned value.")
    
    print(f"\\nThe standard deviation for proficiency assessment (σ_pt) was set to {data['config']['calculation']['sigma_pt']}.")
    print("\\nParticipant performance is evaluated using z-scores calculated as z = (x - x_pt) / σ_pt, where x is the participant result.")
```

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

### Additional Plots

```{{python}}
#| echo: false
if 'plot_paths' in data:
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    
    if 'histogram' in data['plot_paths']:
        plt.figure(figsize=(10, 6))
        img = mpimg.imread(data['plot_paths']['histogram'])
        plt.imshow(img)
        plt.axis('off')
        plt.title('Histogram of Results')
        plt.show()
    
    if 'density' in data['plot_paths']:
        plt.figure(figsize=(10, 6))
        img = mpimg.imread(data['plot_paths']['density'])
        plt.imshow(img)
        plt.axis('off')
        plt.title('Density Plot')
        plt.show()
```

## Participant Performance

```{{python}}
#| echo: false
if 'results' in data and 'participant_scores' in data['results']:
    import numpy as np
    
    participant_ids = data['participant_ids']
    z_scores = data['results']['participant_scores']
    z_prime_scores = data['results'].get('participant_z_prime_scores', [])
    
    has_z_prime = len(z_prime_scores) == len(z_scores)
    
    print("### Performance Table")
    print("")
    
    if has_z_prime:
        print("| Participant ID | Result | Z-Score | Z'-Score | Z Performance | Z' Performance |")
        print("|----------------|--------|---------|----------|---------------|----------------|")
    else:
        print("| Participant ID | Result | Z-Score | Performance |")
        print("|----------------|--------|---------|-------------|")
    
    for i, (pid, z_score) in enumerate(zip(participant_ids, z_scores)):
        result = data['participant_results'][i]
        
        # Determine z-score performance category
        if abs(z_score) <= 2.0:
            z_performance = "Satisfactory"
        elif abs(z_score) <= 3.0:
            z_performance = "Questionable"
        else:
            z_performance = "Unsatisfactory"
        
        if has_z_prime:
            z_prime = z_prime_scores[i]
            
            # Determine z'-score performance category  
            if abs(z_prime) <= 2.0:
                z_prime_performance = "Satisfactory"
            elif abs(z_prime) <= 3.0:
                z_prime_performance = "Questionable"
            else:
                z_prime_performance = "Unsatisfactory"
            
            print(f"| {pid} | {result:.4f} | {z_score:.3f} | {z_prime:.3f} | {z_performance} | {z_prime_performance} |")
        else:
            print(f"| {pid} | {result:.4f} | {z_score:.3f} | {z_performance} |")
    
    # Summary statistics for z-scores
    z_satisfactory = sum(1 for z in z_scores if abs(z) <= 2.0)
    z_questionable = sum(1 for z in z_scores if 2.0 < abs(z) <= 3.0)
    z_unsatisfactory = sum(1 for z in z_scores if abs(z) > 3.0)
    
    print("")
    print("### Z-Score Performance Summary")
    print("")
    print(f"- **Satisfactory** (|z| ≤ 2.0): {z_satisfactory} participants")
    print(f"- **Questionable** (2.0 < |z| ≤ 3.0): {z_questionable} participants")  
    print(f"- **Unsatisfactory** (|z| > 3.0): {z_unsatisfactory} participants")
    
    # Summary statistics for z'-scores if available
    if has_z_prime:
        z_prime_satisfactory = sum(1 for z in z_prime_scores if abs(z) <= 2.0)
        z_prime_questionable = sum(1 for z in z_prime_scores if 2.0 < abs(z) <= 3.0)
        z_prime_unsatisfactory = sum(1 for z in z_prime_scores if abs(z) > 3.0)
        
        print("")
        print("### Z'-Score Performance Summary")
        print("")
        print(f"- **Satisfactory** (|z'| ≤ 2.0): {z_prime_satisfactory} participants")
        print(f"- **Questionable** (2.0 < |z'| ≤ 3.0): {z_prime_questionable} participants")  
        print(f"- **Unsatisfactory** (|z'| > 3.0): {z_prime_unsatisfactory} participants")
        
        print("")
        print("**Note:** Z'-scores (zeta-scores) account for participant measurement uncertainties and the uncertainty of the assigned value.")
```

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

## Configuration Details

```{{python}}
#| echo: false
if 'config' in data:
    config = data['config']
    
    print("### Calculation Configuration")
    print("")
    print("| Parameter | Value |")
    print("|-----------|-------|")
    print(f"| Method | {config['calculation']['method']} |")
    print(f"| σ_pt | {config['calculation']['sigma_pt']} |")
    
    print("")
    print("### Input Data Configuration")
    print("")
    print("| Parameter | Value |")
    print("|-----------|-------|")
    print(f"| Participant ID Column | {config['input_data']['participant_id_col']} |")
    print(f"| Result Column | {config['input_data']['result_col']} |")
    if config['input_data']['uncertainty_col']:
        print(f"| Uncertainty Column | {config['input_data']['uncertainty_col']} |")

if 'results' in data and 'calculation_details' in data['results']:
    details = data['results']['calculation_details']
    
    print("")
    print("### Calculation Details")
    print("")
    
    if 'tolerance' in details:
        print(f"- **Convergence tolerance**: {details['tolerance']}")
    if 'max_iterations' in details:
        print(f"- **Maximum iterations**: {details['max_iterations']}")
    if 'iterations' in details:
        print(f"- **Actual iterations**: {details['iterations']}")
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
            '-P', f'data_file={data_file_path}'
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