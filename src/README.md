# PT-CLI Python Modules Implementation

This directory contains the complete implementation of the Python application layer for the Proficiency Testing CLI (PT-CLI), following the specifications in `Design/draft_03_python_module_design.md`.

## Module Overview

### 1. `config.py` - Configuration Management
- **Purpose**: Load, validate, and provide access to application configuration
- **Features**:
  - YAML and TOML format support with automatic detection
  - Comprehensive Pydantic validation models
  - Nested configuration structure (InputData, Calculation, Reporting)
  - Default values and custom validation rules
  - Detailed error messages for validation failures

### 2. `data_io.py` - Data Input/Output and Validation  
- **Purpose**: Read and validate input proficiency testing data
- **Features**:
  - CSV and Excel (.csv, .xlsx, .xls) file support
  - Multi-stage validation pipeline:
    - Column presence validation
    - Data type conversion and validation
    - Row-level Pydantic validation
  - Custom exception hierarchy for specific error types
  - Data preparation for calculation engines

### 3. `reporting.py` - Reporting Orchestration
- **Purpose**: Generate reports using Quarto with integrated plotting
- **Features**:
  - Plot generation using matplotlib and seaborn
  - Dynamic Quarto template creation with embedded Python
  - Data aggregation and JSON serialization for templates
  - Subprocess-based Quarto CLI invocation
  - Support for multiple output formats (PDF, HTML, Word)

### 4. `main.py` - CLI Entry Point and Workflow Orchestration
- **Purpose**: Main CLI application using Typer framework
- **Features**:
  - Three sub-commands:
    - `calculate`: Full analysis with report generation
    - `validate-data`: Data validation only
    - `generate-report-only`: Report from pre-calculated results
  - Rich console interface with progress indicators
  - Comprehensive argument and option handling
  - CLI parameter overrides for configuration values
  - Robust error handling with user-friendly messages

## CLI Usage Examples

### Getting Help
```bash
# Main CLI help
python -m src.main --help

# Help for specific commands
python -m src.main calculate --help
python -m src.main validate-data --help
python -m src.main generate-report-only --help
```

### Basic Data Validation
```bash
# Validate data file with default configuration
python -m src.main validate-data test_data.csv

# Validate with custom configuration
python -m src.main validate-data test_data.csv --config test_config.yaml

# Verbose validation with detailed output
python -m src.main validate-data test_data.csv --config test_config.yaml --verbose
```

### Full Analysis Run
```bash
# Basic analysis with defaults
python -m src.main calculate test_data.csv

# Complete analysis with all options
python -m src.main calculate test_data.csv \
  --config test_config.yaml \
  --output-report analysis_report \
  --output-format pdf \
  --method AlgorithmA \
  --sigma-pt 0.15 \
  --results-json intermediate_results.json \
  --verbose

# Generate HTML report with CRM method
python -m src.main calculate participant_data.xlsx \
  --config crm_config.yaml \
  --output-report crm_analysis \
  --output-format html \
  --method CRM

# Quick analysis with method override
python -m src.main calculate data.csv --method Expert --output-format docx
```

### Report Generation Only
```bash
# Generate PDF report from existing results
python -m src.main generate-report-only results.json

# Generate custom format report
python -m src.main generate-report-only results.json \
  --output-report final_report \
  --output-format html \
  --config custom_template_config.yaml

# Verbose report generation
python -m src.main generate-report-only results.json \
  --output-report detailed_report \
  --output-format pdf \
  --verbose
```

### Common CLI Patterns
```bash
# Save intermediate results for later report generation
python -m src.main calculate data.csv \
  --results-json results_backup.json \
  --output-report initial_report

# Later, generate additional reports from saved results
python -m src.main generate-report-only results_backup.json \
  --output-report management_summary \
  --output-format docx

# Validate data before running full analysis
python -m src.main validate-data data.csv --config analysis_config.yaml
python -m src.main calculate data.csv --config analysis_config.yaml
```

## Configuration Format Examples

### YAML Configuration
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
    histogram_bins: 30
```

### TOML Configuration
```toml
[input_data]
participant_id_col = "ParticipantID"
result_col = "Value"
uncertainty_col = "Uncertainty"

[calculation]
method = "AlgorithmA"
sigma_pt = 0.15

[calculation.algorithm_a]
tolerance = 1.0e-5
max_iterations = 50

[reporting]
default_format = "pdf"

[reporting.plots]
generate_histogram = true
histogram_bins = 30
```

## Data Format Requirements

Input data files (CSV or Excel) should contain:
- Participant ID column (configurable name)
- Result value column (configurable name) 
- Optional uncertainty column (configurable name)

Example CSV:
```csv
ParticipantID,Value,Uncertainty
P001,10.15,0.05
P002,9.87,0.08
P003,10.42,0.06
```

## Dependencies

The implementation requires the following Python packages:
- `pydantic`: Configuration and data validation
- `polars[excel]`: Data file reading and processing
- `matplotlib`, `seaborn`: Plot generation
- `typer`: CLI framework
- `rich`: Console formatting and progress indicators
- `PyYAML`: YAML configuration support
- `toml`: TOML configuration support

## Error Handling

The modules provide comprehensive error handling with:
- Custom exception hierarchies for different error types
- Detailed error messages with context
- Rich console formatting for user-friendly display
- Proper exit codes for CLI operations

## Design Compliance

This implementation fully complies with the module-level design specified in:
- `Design/draft_03_python_module_design.md`
- `Design/draft_05_cli_design.md` 
- `Design/draft_06_data_config_design.md`
- `Design/draft_07_reporting_system_design.md`
- `Design/draft_08_error_handling.md`

All modules include comprehensive type hints, docstrings, and follow modular design principles for maintainability and testability.