# PT-CLI Command Line Interface Documentation

The PT-CLI provides a comprehensive command-line interface for proficiency testing analysis using the Typer framework. This document provides detailed usage information and examples.

## Overview

The CLI is organized into three main sub-commands:

- **`calculate`**: Perform full proficiency testing analysis with report generation
- **`validate-data`**: Validate input data file structure and content
- **`generate-report-only`**: Generate report from pre-calculated results

## Features

- **Automatic Help Generation**: Use `--help` with any command for detailed usage information
- **Rich Console Output**: Color-coded progress indicators and error messages
- **Flexible Configuration**: YAML/TOML configuration files with CLI parameter overrides
- **Multiple Output Formats**: PDF, HTML, and Word document report generation
- **Error Handling**: Clear, user-friendly error messages with suggested solutions
- **Verbose Mode**: Detailed output for debugging and monitoring

## Installation

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Quick Start

1. **Validate your data first**:
   ```bash
   python -m src.main validate-data your_data.csv
   ```

2. **Run a complete analysis**:
   ```bash
   python -m src.main calculate your_data.csv --config your_config.yaml
   ```

3. **Generate additional reports**:
   ```bash
   python -m src.main generate-report-only results.json --output-format html
   ```

## Command Reference

### Global Options

- `--help`: Show help message and exit
- `--install-completion`: Install shell completion
- `--show-completion`: Show completion script

### calculate

Perform full proficiency testing analysis with report generation.

**Usage:**
```bash
python -m src.main calculate [OPTIONS] INPUT_FILE
```

**Arguments:**
- `INPUT_FILE`: Path to the input data file (CSV or XLSX) [required]

**Options:**
- `--config, -c PATH`: Path to configuration file (YAML or TOML)
- `--output-report, -o PATH`: Base path for output report [default: report]
- `--output-format, -f TEXT`: Output format (pdf, html, docx) [default: pdf]
- `--method TEXT`: Override calculation method (AlgorithmA, CRM, Formulation, Expert)
- `--sigma-pt FLOAT`: Override standard deviation for proficiency assessment
- `--results-json PATH`: Save intermediate results as JSON
- `--verbose, -v`: Enable verbose output

**Examples:**
```bash
# Basic analysis
python -m src.main calculate data.csv

# Full featured analysis
python -m src.main calculate data.csv \
  --config analysis_config.yaml \
  --output-report pt_round_1 \
  --output-format html \
  --method AlgorithmA \
  --sigma-pt 0.15 \
  --results-json backup_results.json \
  --verbose
```

### validate-data

Validate input data file structure and content.

**Usage:**
```bash
python -m src.main validate-data [OPTIONS] INPUT_FILE
```

**Arguments:**
- `INPUT_FILE`: Path to the input data file (CSV or XLSX) to validate [required]

**Options:**
- `--config, -c PATH`: Path to configuration file (YAML or TOML)
- `--verbose, -v`: Enable verbose output

**Examples:**
```bash
# Basic validation
python -m src.main validate-data participant_data.csv

# Validation with custom config
python -m src.main validate-data data.xlsx --config custom_config.yaml --verbose
```

### generate-report-only

Generate report from pre-calculated results.

**Usage:**
```bash
python -m src.main generate-report-only [OPTIONS] RESULTS_INPUT
```

**Arguments:**
- `RESULTS_INPUT`: Path to file containing pre-calculated results (JSON) [required]

**Options:**
- `--config, -c PATH`: Path to configuration file (YAML or TOML)
- `--output-report, -o PATH`: Base path for output report [default: report]
- `--output-format, -f TEXT`: Output format (pdf, html, docx) [default: pdf]
- `--verbose, -v`: Enable verbose output

**Examples:**
```bash
# Generate PDF report
python -m src.main generate-report-only results.json

# Generate custom format report
python -m src.main generate-report-only results.json \
  --output-report executive_summary \
  --output-format docx \
  --config presentation_template.yaml
```

## Configuration Files

The CLI supports YAML and TOML configuration files that define:

- Input data column mappings
- Calculation methods and parameters
- Report formatting options
- Output preferences

Example configuration (YAML):
```yaml
input_data:
  participant_id_col: "ParticipantID"
  result_col: "Value"
  uncertainty_col: "Uncertainty"

calculation:
  method: "AlgorithmA"
  sigma_pt: 0.15
  algorithm_a:
    tolerance: 1.0e-5
    max_iterations: 50

reporting:
  default_format: "pdf"
  plots:
    generate_histogram: true
    histogram_bins: 20
```

## Error Handling

The CLI provides clear error messages for common issues:

- **File not found**: Check file paths and permissions
- **Configuration errors**: Validate YAML/TOML syntax and required fields
- **Data validation failures**: Review column names and data types
- **Calculation errors**: Check method parameters and data quality

Use `--verbose` for detailed error information and debugging output.

## Workflow Examples

### Standard Analysis Workflow
```bash
# 1. Validate data structure
python -m src.main validate-data experiment_data.csv --config pt_config.yaml

# 2. Run full analysis
python -m src.main calculate experiment_data.csv \
  --config pt_config.yaml \
  --output-report round_15_analysis \
  --results-json round_15_results.json \
  --verbose

# 3. Generate additional report formats
python -m src.main generate-report-only round_15_results.json \
  --output-report round_15_summary \
  --output-format html
```

### Method Comparison Workflow
```bash
# Compare different calculation methods
python -m src.main calculate data.csv --method AlgorithmA --output-report algorithm_a_results
python -m src.main calculate data.csv --method CRM --output-report crm_results --config crm_config.yaml
python -m src.main calculate data.csv --method Expert --output-report expert_results --config expert_config.yaml
```

### Batch Processing Workflow
```bash
# Process multiple datasets
for dataset in dataset_*.csv; do
  echo "Processing $dataset..."
  python -m src.main validate-data "$dataset" --config batch_config.yaml
  python -m src.main calculate "$dataset" \
    --config batch_config.yaml \
    --output-report "${dataset%.csv}_analysis" \
    --results-json "${dataset%.csv}_results.json"
done
```

## Best Practices

1. **Always validate data first** before running full analysis
2. **Use configuration files** for consistent analysis parameters
3. **Save intermediate results** (`--results-json`) for backup and additional reporting
4. **Use verbose mode** (`--verbose`) when troubleshooting
5. **Specify meaningful output names** to organize results
6. **Test with small datasets** before processing large files

## Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
pip install -r requirements.txt
```

**"File does not exist" errors:**
- Check file paths (use absolute paths if needed)
- Verify file permissions

**"Configuration validation failed":**
- Validate YAML/TOML syntax
- Check required configuration fields
- Review example configurations

**"Calculation engine not available":**
- Ensure Rust calculation engine is properly installed
- Check that `pt_cli_rust` module is available

For additional support, use `--verbose` to get detailed error information and stack traces.