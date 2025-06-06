## 3. Module-Level Design - Python Application Layer

This section provides a detailed design for each primary module within the Python application layer of the PT-CLI. This layer is responsible for the command-line interface, workflow orchestration, configuration management, data input/output, validation, and interaction with the Rust calculation engine and the external Quarto reporting tool. The design emphasizes modularity and adherence to the requirements outlined in the SRS (FR-DI, FR-CM, FR-RP, FR-CLI, NFR-MA-001, NFR-MA-003).

### 3.1 `main.py`: CLI Entry Point and Workflow Orchestration

**Purpose:** This module serves as the main entry point for the application when invoked from the command line. It utilizes the `Typer` library to define the CLI structure, parse arguments and options, and orchestrate the overall execution flow based on the selected sub-command. It also handles top-level error catching and user feedback using the `rich` library.

**Key Responsibilities:**

*   **CLI Definition (FR-CLI-001, FR-CLI-005):** Define the main Typer application and register sub-commands (`calculate`, `validate-data`, `generate-report-only` as per FR-CLI-002).
*   **Argument/Option Parsing (FR-CLI-003, FR-CLI-004):** Define and parse command-line arguments and options for each sub-command, including input file path (FR-DI-001), config file path (FR-CM-001), output report path/format (FR-RP-004), calculation method override (FR-AV-006), `sigma_pt` (FR-PS-003), etc. Use type hints for automatic validation and help message generation.
*   **Workflow Orchestration:** Based on the invoked sub-command, orchestrate the sequence of operations by calling functions from other modules (`config.py`, `data_io.py`, `reporting.py`) and the Rust engine interface.
    *   For `calculate`: Load config -> Load data -> Validate data -> Call Rust engine for calculations -> Prepare report data -> Invoke Quarto reporting -> Provide console summary.
    *   For `validate-data`: Load config -> Load data -> Validate data -> Report validation results.
    *   For `generate-report-only`: Load config -> Load pre-calculated results (requires defining how these are stored/passed) -> Prepare report data -> Invoke Quarto reporting.
*   **User Feedback (FR-RP-010, FR-CLI-006):** Utilize the `rich` library to display progress messages, informative status updates, summaries of results, and formatted error messages to the console.
*   **Top-Level Error Handling (NFR-RL-002):** Implement try-except blocks to catch exceptions raised from other modules (e.g., file not found, validation errors, Rust calculation errors, Quarto errors) and present user-friendly error messages via `rich`.

**Primary Classes/Functions:**

*   `app = typer.Typer()`: The main Typer application instance.
*   `@app.command()` decorated functions (e.g., `calculate`, `validate_data`, `generate_report_only`): Implement the logic for each sub-command.
*   Helper functions for orchestrating the steps within each command.

**Interactions:**

*   Calls `config.load_config()` to get configuration settings.
*   Calls `data_io.load_and_validate_data()` to get validated input data.
*   Calls functions exposed by the Rust engine via PyO3 (e.g., `pt_cli_rust.calculate_algorithm_a()`).
*   Calls `reporting.generate_report()` to handle plot generation and Quarto invocation.
*   Uses `rich` for console output.

### 3.2 `config.py`: Configuration Management

**Purpose:** This module handles loading, validating, and providing access to application configuration settings. It supports configuration files in YAML or TOML format and provides default values.

**Key Responsibilities:**

*   **Loading Configuration (FR-CM-001, FR-CM-002):** Implement functions to load configuration settings from a specified file path (YAML or TOML). Detect file type based on extension. Load default settings if no file is provided or if the specified file doesn't exist (or handle as an error, TBD based on desired behavior).
*   **Validation (FR-CM-004):** Define Pydantic models representing the expected structure and types of the configuration settings (e.g., calculation parameters FR-CM-003, report format, custom template path, input data column mappings DR-IN-001, `sigma_pt` FR-PS-003, outlier handling options FR-CM-003). Use Pydantic to parse and validate the loaded configuration data against these models.
*   **Providing Access:** Offer a clear way (e.g., a function returning a validated config object/dictionary) for other modules (`main.py`, `data_io.py`, `reporting.py`) to access configuration values.
*   **Default Settings:** Define and manage the default configuration values.

**Primary Classes/Functions:**

*   Pydantic Models (e.g., `CalculationConfig`, `ReportingConfig`, `InputDataConfig`, `MainConfig`): Define the structure and validation rules for configuration sections.
*   `load_config(config_path: Optional[Path]) -> MainConfig`: The main function called by `main.py`. Takes an optional path, loads defaults, loads user file if provided, merges, validates using Pydantic, and returns the validated configuration object.
*   Helper functions for loading YAML (`PyYAML`) and TOML (`toml`) files.

**Interactions:**

*   Called by `main.py` to get the application configuration.
*   Uses `Pydantic` for validation.
*   Uses `PyYAML` or `toml` library for file parsing.
*   Reads configuration files from the filesystem.

### 3.3 `data_io.py`: Data Input/Output and Validation

**Purpose:** This module is responsible for reading input proficiency testing data from specified file formats (CSV, Excel) and performing validation based on configuration.

**Key Responsibilities:**

*   **Data Reading (FR-DI-001, FR-DI-002):** Implement functions to read data from CSV and Excel (.xlsx) files using the `polars` library into DataFrames.
*   **Structure Validation (FR-DI-003, DR-IN-001):** Check for the presence of required columns based on names specified in the configuration (e.g., participant ID, result value, participant uncertainty `u(x_i)` if needed for FR-PS-002/FR-PS-003).
*   **Data Type Validation (FR-DI-004):** Validate that relevant columns contain the expected data types (e.g., numerical results, numeric uncertainties).
*   **Pydantic Integration (FR-DI-005):** Leverage Pydantic models, potentially dynamically created or selected based on configuration, to validate the data row-by-row or the DataFrame structure as a whole. This provides robust validation beyond basic polars checks.
*   **Error Reporting (FR-DI-006):** Raise specific, informative exceptions if validation fails (e.g., `MissingColumnError`, `InvalidDataTypeError`), which can be caught by `main.py`.
*   **Data Preparation:** Prepare the validated data (e.g., extracting relevant columns as NumPy arrays) for passing to the Rust calculation engine.

**Primary Classes/Functions:**

*   Pydantic Models (e.g., `ParticipantDataRow`): Define the expected structure and types for a row of input data, potentially referencing configuration for column names.
*   `load_and_validate_data(file_path: Path, config: MainConfig) -> pl.DataFrame`: The main function called by `main.py`. Reads the file using polars, performs validation (structural, type, potentially Pydantic-based), and returns the validated DataFrame. Raises exceptions on failure.
*   Helper functions for reading specific file types (`_read_csv`, `_read_excel`).
*   Helper functions for performing validation checks.

**Interactions:**

*   Called by `main.py`.
*   Uses `polars` for reading files.
*   Uses `Pydantic` for validation.
*   Uses configuration object (from `config.py`) to determine expected columns, types, etc.
*   Reads input data files from the filesystem.

### 3.4 `reporting.py`: Reporting Orchestration

**Purpose:** This module orchestrates the generation of the final report using Quarto. It prepares the necessary data, generates plots, and invokes the Quarto CLI.

**Key Responsibilities:**

*   **Data Aggregation (FR-RP-002):** Collect all necessary data for the report, including input data summaries, configuration settings used, results from the Rust engine (`x_pt`, `u(x_pt)`, scores, etc.), and any other relevant metadata.
*   **Plot Generation (FR-RP-005):** Use `matplotlib` and/or `seaborn` to generate required plots (e.g., histograms, density plots of participant results). Save these plots to temporary image files (e.g., PNG) in a known location accessible by Quarto, or design the `.qmd` template to generate them dynamically using Python code chunks (requires careful setup).
*   **Quarto Data Passing (FR-RP-003):** Determine the mechanism for passing data to the `.qmd` template. Options include:
    *   Writing data to intermediate files (e.g., a JSON file containing all results and parameters) that the `.qmd` file reads.
    *   Passing parameters directly via the Quarto CLI render command (suitable for simpler data).
    The intermediate file approach is generally more robust for complex data.
*   **Quarto Invocation (FR-RP-006):** Construct the appropriate Quarto CLI command (e.g., `quarto render template.qmd -o output_report.pdf --metadata-file=results.json`) using the `subprocess` module. Ensure safe command construction (NFR-SE-002). Specify the correct template (default FR-RP-007 or custom FR-RP-008), output file path and format (FR-RP-004).
*   **Error Handling:** Capture potential errors during plot generation or from the `subprocess` call to Quarto (e.g., Quarto not found, rendering errors) and raise exceptions to be handled by `main.py`.

**Primary Classes/Functions:**

*   `generate_report(report_data: Dict, config: MainConfig, output_path: Path, output_format: str)`: The main function called by `main.py`. Takes calculation results/data, configuration, and output specs. Orchestrates plot generation, data preparation for Quarto, and Quarto invocation.
*   Helper functions for generating specific plots (`_generate_histogram`, etc.).
*   Helper function to prepare the intermediate data file (e.g., `_write_quarto_data_json`).
*   Helper function to build and execute the Quarto command (`_invoke_quarto`).

**Interactions:**

*   Called by `main.py`.
*   Uses `matplotlib`/`seaborn` for plotting.
*   Uses `subprocess` to call the external Quarto CLI.
*   Writes intermediate data/plot files to the filesystem.
*   Reads configuration for template paths, etc.

### 3.5 Other Python Utility Modules (If Necessary)

Depending on the complexity that arises during implementation, additional utility modules might be created. For example:

*   `utils.py`: Could contain common helper functions or constants used across multiple Python modules if they don't fit neatly into the modules above.
*   `exceptions.py`: Could define custom exception classes for more specific error handling throughout the Python layer.

This modular design ensures that each part of the Python application has a distinct responsibility, enhancing testability and maintainability (NFR-MA-001, NFR-MA-003).
