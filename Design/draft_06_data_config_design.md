## 6. Data Handling and Configuration Design

This section details the design for handling input data, configuration files, and the validation processes involved in the PT-CLI application. Robust data handling and flexible configuration are crucial for the tool's usability and reliability, directly addressing requirements FR-DI, FR-CM, DR-IN, DR-CFG, and NFR-US-004.

### 6.1 Configuration File Structure (YAML/TOML) and Parameters (DR-CFG-001, FR-CM-003)

The PT-CLI will support configuration via external files in either YAML or TOML format (FR-CM-001), allowing users to customize the application's behavior without modifying code. A default configuration will be embedded within the application or loaded from a default file if no user-specified file is provided (FR-CM-002). The configuration structure will be hierarchical, grouping related parameters logically.

**Supported Formats:** YAML (`.yaml` or `.yml`) and TOML (`.toml`). The `config.py` module will detect the format based on the file extension.

**Top-Level Structure (Conceptual):**

```yaml
# Example YAML Configuration Structure

input_data:
  participant_id_col: "ParticipantID"
  result_col: "Value"
  uncertainty_col: "Uncertainty" # Optional: Column name for u(xi) (FR-PS-003)
  # Add other potential column mappings if needed

calculation:
  method: "AlgorithmA" # Default method (FR-CM-003a), options: AlgorithmA, CRM, Formulation, Expert
  sigma_pt: 0.15 # Default Standard deviation for proficiency assessment (FR-PS-003)
  algorithm_a:
    tolerance: 1.0e-5 # Convergence tolerance (FR-CM-003b)
    max_iterations: 50 # Max iterations (FR-CM-003b)
  crm: # Parameters if method is CRM (DR-IN-003)
    certified_value: null
    uncertainty: null
  formulation: # Parameters if method is Formulation
    known_value: null
    uncertainty: null
  expert_consensus: # Parameters if method is Expert
    consensus_value: null
    uncertainty: null # Method for uncertainty TBD
  outlier_handling: # (FR-CM-003c)
    method: "RobustAlgorithmA" # Options: RobustAlgorithmA (implicit), Grubbs (if implemented), DixonsQ (if implemented), None
    # Parameters specific to outlier tests if implemented (e.g., alpha level)

reporting:
  default_format: "pdf" # Default report format (FR-CM-003d)
  custom_template: null # Path to custom .qmd template (FR-CM-003e, FR-RP-008)
  plots:
    generate_histogram: true
    histogram_bins: 30
    # Add other plot configuration options

# Add other sections as needed
```

**Key Parameters:**

*   **`input_data`**: Defines mappings from expected conceptual fields (like participant ID, result) to actual column names in the user's input file (DR-IN-001). Includes the optional column for participant uncertainty `u(x_i)` (FR-PS-003).
*   **`calculation`**: Specifies the core calculation parameters.
    *   `method`: Default method for `x_pt` calculation (FR-CM-003a).
    *   `sigma_pt`: Default value for the standard deviation for proficiency assessment (FR-PS-003).
    *   `algorithm_a`: Parameters specific to Algorithm A (tolerance, max iterations) (FR-CM-003b).
    *   `crm`, `formulation`, `expert_consensus`: Sections to provide necessary values if these methods are selected (DR-IN-003). These might be better provided via CLI arguments for single runs, but config provides a way to store them.
    *   `outlier_handling`: Configuration for outlier detection/handling methods (FR-CM-003c). Initially, this might just confirm the use of the inherent robustness of Algorithm A.
*   **`reporting`**: Controls report generation.
    *   `default_format`: Default output format if not specified via CLI (FR-CM-003d).
    *   `custom_template`: Path to a user-provided Quarto template file (FR-CM-003e, FR-RP-008).
    *   `plots`: Options to enable/disable or configure specific plots in the report.

### 6.2 Configuration Validation (Pydantic) (FR-CM-004)

Configuration data loaded from files (or defaults) will be rigorously validated using Pydantic models defined in `config.py`. This ensures that the configuration structure is correct, data types are appropriate, and values are within acceptable ranges or belong to predefined enumerations.

**Process:**

1.  **Define Pydantic Models:** Create Python classes inheriting from `pydantic.BaseModel` that mirror the structure outlined in 6.1. Use type hints (`str`, `int`, `float`, `bool`, `Optional`, `Path`, `Literal[...]`, `List[...]`, nested models) and Pydantic validators (`@validator`) for complex rules.
    ```python
    # Example Pydantic model snippet in config.py
    from pydantic import BaseModel, Field, validator
    from typing import Optional, Literal
    from pathlib import Path

    class AlgorithmAParams(BaseModel):
        tolerance: float = Field(1.0e-5, gt=0)
        max_iterations: int = Field(50, gt=0)

    class CalculationConfig(BaseModel):
        method: Literal['AlgorithmA', 'CRM', 'Formulation', 'Expert'] = 'AlgorithmA'
        sigma_pt: Optional[float] = Field(None, gt=0) # Allow override via CLI
        algorithm_a: AlgorithmAParams = AlgorithmAParams()
        # ... other sections (CRM, Formulation, etc.) ...
        # ... outlier_handling ...

    class InputDataConfig(BaseModel):
        participant_id_col: str = 'ParticipantID'
        result_col: str = 'Value'
        uncertainty_col: Optional[str] = None

    class ReportingConfig(BaseModel):
        default_format: Literal['pdf', 'html', 'docx'] = 'pdf'
        custom_template: Optional[Path] = None
        # ... plot configs ...

    class MainConfig(BaseModel):
        input_data: InputDataConfig = InputDataConfig()
        calculation: CalculationConfig = CalculationConfig()
        reporting: ReportingConfig = ReportingConfig()

    ```
2.  **Load Raw Data:** Load the YAML or TOML file into a Python dictionary.
3.  **Parse and Validate:** Instantiate the top-level Pydantic model (e.g., `MainConfig`) with the loaded dictionary. Pydantic will automatically parse, validate types, run validators, and populate default values.
4.  **Handle Errors:** If validation fails, Pydantic raises a `ValidationError`. The `config.py` module will catch this, format the error messages clearly (Pydantic provides detailed error locations), and raise a custom configuration error (e.g., `ConfigValidationError`) to be handled by `main.py`.
5.  **Return Validated Config:** If validation succeeds, return the populated and validated Pydantic model instance.

This approach ensures that the rest of the application receives a guaranteed-valid configuration object, simplifying downstream logic and improving robustness.

### 6.3 Input Data Validation Flow (Pydantic) (FR-DI-003, FR-DI-004, FR-DI-005)

Input participant data (CSV/Excel) requires validation to ensure it meets the structural and type requirements before being used in calculations. This validation will occur in the `data_io.py` module after loading the data into a Pandas DataFrame, leveraging both Pandas capabilities and Pydantic for enhanced checking.

**Process:**

1.  **Load Data:** Read the CSV or Excel file into a Pandas DataFrame using `pd.read_csv` or `pd.read_excel` (FR-DI-002).
2.  **Column Presence Check (FR-DI-003):** Verify that the columns specified in the configuration (`input_data.participant_id_col`, `input_data.result_col`, `input_data.uncertainty_col` if provided and needed) exist in the DataFrame. Raise an informative error (e.g., `MissingColumnError`) if any required column is missing.
3.  **Initial Type Conversion (Pandas):** Attempt to convert the essential columns (results, uncertainties) to numeric types using `pd.to_numeric(errors='coerce')`. This will turn non-numeric values into `NaN`.
4.  **Missing Value Check:** Check for `NaN` values in the critical numeric columns (results). Decide on a strategy: either raise an error immediately, report warnings, or allow the Rust engine to handle them (though filtering them out in Python is often cleaner).
5.  **(Optional but Recommended) Row-Level Pydantic Validation (FR-DI-005):** For more rigorous validation, especially if there are complex cross-field rules or specific format requirements for IDs:
    *   Define a Pydantic model representing a single row of data (e.g., `ParticipantDataRow`).
    *   Iterate through the DataFrame rows (`df.itertuples()` or similar efficient method).
    *   For each row, create a dictionary and attempt to parse it with the `ParticipantDataRow` model.
    *   Collect any `ValidationError` exceptions. This can pinpoint specific rows and fields causing issues.
    *   This step adds overhead but provides much more detailed validation feedback than DataFrame-level checks alone.
6.  **Final Type Check (FR-DI-004):** After coercion and potential Pydantic validation, double-check the `dtype` of the critical Pandas Series (e.g., ensure the result column is indeed float or int).
7.  **Error Reporting (FR-DI-006):** If any validation step fails, raise specific exceptions (e.g., `DataValidationError`, `InvalidTypeError`) containing clear messages about the nature and location (e.g., column name, row number if using row-level validation) of the error. These exceptions will be caught by `main.py` and reported to the user.
8.  **Return Validated Data:** If all checks pass, return the validated (and potentially cleaned) DataFrame or extracted NumPy arrays ready for the calculation engine.

This multi-stage validation process, combining Pandas efficiency with Pydantic's rigorous schema definition, ensures data quality and prevents errors during the critical calculation phase.
