## 8. Comprehensive Error Handling Strategy

This section outlines the comprehensive strategy for detecting, handling, logging, and reporting errors throughout the PT-CLI application. A robust error handling mechanism is crucial for reliability (NFR-RL-002) and usability (NFR-US-003), ensuring that users receive clear feedback when issues arise and that the application behaves predictably even in unexpected situations.

### 8.1 Error Detection and Logging (Python & Rust)

Errors can originate from various sources: invalid user input, file system issues, configuration problems, data validation failures, calculation errors within the Rust engine, or external tool failures (Quarto). Detection will occur at the point where an invalid state or operation is identified.

**Python Layer Detection:**

*   **File I/O:** Use `try...except` blocks around file operations (reading config/data, writing reports/plots/intermediate files) to catch `FileNotFoundError`, `PermissionError`, `IOError`, etc.
*   **Configuration:** Pydantic validation in `config.py` automatically detects structural and type errors in configuration files, raising `ValidationError`.
*   **Data Validation:** Explicit checks in `data_io.py` (column presence, type coercion failures, `NaN` checks) and Pydantic row-level validation will detect issues in input data, raising custom exceptions (e.g., `DataValidationError`, `MissingColumnError`).
*   **CLI Parsing:** Typer handles basic argument type validation automatically. Custom validators can be added for more complex CLI argument checks.
*   **Subprocess Calls:** Check the return code and capture `stderr` from `subprocess.run` when calling Quarto (FR-RP-006) to detect external tool failures. Catch `FileNotFoundError` if Quarto is not installed/in PATH.
*   **Rust Interface:** Catch Python exceptions raised by the PyO3 layer when Rust functions return errors.

**Rust Engine Detection:**

*   **Input Validation:** Rust functions will validate the inputs received from Python (e.g., array dimensions, parameter values like `sigma_pt > 0`).
*   **Calculation Errors:** Detect numerical issues like division by zero, failure to converge in iterative algorithms (Algorithm A), or invalid mathematical operations (e.g., square root of negative number if not handled by complex numbers).
*   **Internal Logic Errors:** Use Rust's `Result<T, E>` and the `?` operator extensively to propagate errors from internal computations.

**Logging:**
A standard logging approach will be implemented using Python's built-in `logging` module.

*   **Configuration:** Logging level (e.g., DEBUG, INFO, WARNING, ERROR) can be controlled, potentially via a CLI flag (`--verbose` for DEBUG) or a configuration file setting.
*   **Log Format:** Logs should include timestamp, log level, module name, and the error message.
*   **Log Destination:** Log messages can be directed to the console (stderr) and/or a log file (e.g., `pt-cli.log`). Console logging for errors will be supplemented by user-friendly messages via `rich`.
*   **Content:** Log standard operations at INFO level, potential issues or recoverable errors at WARNING level, and unrecoverable errors or exceptions at ERROR/CRITICAL levels. Include stack traces for unexpected exceptions at the DEBUG level.
*   **Rust Logging:** While Rust has its own logging frameworks (`log` crate), for simplicity in this hybrid application, critical errors originating in Rust that are propagated to Python as exceptions will be logged by the Python `logging` framework when caught.

### 8.2 Error Propagation (Rust to Python)

As detailed in Section 4.6 (Rust Error Handling Strategy), errors detected within the Rust calculation engine need to be communicated back to the Python layer.

1.  **Rust `Result`:** Internal Rust functions return `Result<T, CalculationError>`.
2.  **Custom Error Type (`CalculationError`):** This enum/struct in `utils.rs` represents specific calculation failures (e.g., `NonConvergence`, `InvalidInput`, `DivisionByZero`).
3.  **PyO3 Conversion:** Implement `From<CalculationError> for PyErr` or manually map `CalculationError` variants to specific Python exception types (`ValueError`, `RuntimeError`, potentially custom Python exceptions like `CalculationFailedError`) within the `#[pyfunction]` wrappers in `lib.rs`. The error message associated with the Python exception should be informative, derived from the `CalculationError`.
4.  **Python `try...except`:** The Python code in `main.py` (or wherever Rust functions are called) wraps the calls in `try...except` blocks, catching the specific Python exceptions raised by the PyO3 layer.

This ensures that calculation failures are not silent but are transformed into standard Python exceptions that the main application logic can handle appropriately.

### 8.3 User-Facing Error Message Design (NFR-US-003, FR-DI-006, FR-CLI-006)

Clear and helpful error messages are critical for usability. The goal is to inform the user about what went wrong and, if possible, how to fix it.

**Principles:**

*   **Clarity:** Avoid technical jargon where possible. State the problem clearly.
*   **Context:** Indicate where the error occurred (e.g., "Error validating input file: data.csv", "Error in configuration file: config.yaml", "Calculation failed for Algorithm A").
*   **Specificity:** Provide specific details (e.g., "Missing required column: 'Participant_ID'", "Value 'abc' in column 'Result' (row 15) is not numeric", "Algorithm A did not converge after 50 iterations").
*   **Guidance (Where Possible):** Suggest corrective actions (e.g., "Please ensure the column exists and check spelling in the configuration file.", "Please check the data in the specified row.", "Consider increasing max_iterations or checking data for extreme outliers.").
*   **Consistency:** Use a consistent format for error messages.

**Implementation (`rich`):**
The `rich` library will be used in `main.py` to display formatted and user-friendly error messages to the console.

*   Use `rich.print` with styles (e.g., `"[bold red]Error:[/bold red]"`) to make errors stand out.
*   Format multi-line messages clearly.
*   When catching exceptions, extract the relevant information to construct the user-facing message. Avoid dumping raw stack traces to the user unless in verbose/debug mode.

**Example Error Messages:**

*   `[bold red]Error:[/bold red] Input file not found: '/path/to/nonexistent_data.csv'. Please check the file path.`
*   `[bold red]Error:[/bold red] Invalid configuration in 'config.yaml': Field 'calculation.method' has invalid value 'AlgoritmA'. Did you mean 'AlgorithmA'?` (Leveraging Pydantic's detailed errors)
*   `[bold red]Error:[/bold red] Data validation failed in 'input_data.xlsx': Required column 'ResultValue' not found. Check column names in the file and the 'input_data.result_col' setting in your configuration.`
*   `[bold red]Error:[/bold red] Calculation failed: Algorithm A did not converge after 100 iterations. Check input data for unusual values or adjust 'calculation.algorithm_a.max_iterations' in configuration.`
*   `[bold red]Error:[/bold red] Failed to generate report: Quarto rendering failed. Check 'pt-cli.log' or run with --verbose for detailed Quarto output.`

By combining specific detection points, structured logging, clear propagation from Rust to Python, and user-centric message design using `rich`, the PT-CLI will provide a robust and user-friendly experience even when errors occur.
