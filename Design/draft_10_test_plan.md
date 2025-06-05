## 10. Detailed Test Plan

This section outlines the testing strategy for the PT-CLI application, ensuring its correctness, reliability (NFR-RL-001), and adherence to the specified requirements. The plan covers unit testing, integration testing, and end-to-end system testing, along with the definition of sample datasets and a strategy for verifying generated reports (NFR-MA-005).

### 10.1 Unit Testing Strategy

Unit tests will focus on verifying the functionality of individual components (functions, classes, modules) in isolation.

**Python Application Layer (`unittest` / `pytest`):

*   **Framework:** Python's built-in `unittest` library or the more feature-rich `pytest` framework will be used.
*   **Scope:**
    *   `config.py`: Test loading of valid YAML/TOML files, handling of missing files, correct application of defaults, validation logic using Pydantic (mocking file system reads).
    *   `data_io.py`: Test reading of sample CSV and Excel files, validation of correct and incorrect data structures (missing columns, wrong data types) using mock DataFrames and Pydantic models, error handling for invalid inputs.
    *   `reporting.py`: Test data aggregation logic, plot generation function calls (mocking Matplotlib/Seaborn if necessary or checking for output files), correct construction of Quarto commands, handling of `subprocess` errors (mocking `subprocess.run`).
    *   `main.py`: Test CLI argument parsing logic for each subcommand using `Typer`'s testing utilities or by mocking subprocess calls. Test workflow orchestration logic by mocking calls to other modules and the Rust engine.
*   **Mocking:** The `unittest.mock` library (or `pytest-mock`) will be used extensively to isolate units under test from dependencies like the file system, the Rust engine, and the Quarto CLI.

**Rust Calculation Engine (`cargo test`):

*   **Framework:** Rust's built-in testing framework (`cargo test`) will be used.
*   **Scope:**
    *   `estimators.rs`: Test each assigned value calculation method (`AlgorithmA`, `CRM`, `Formulation`, `Expert`) with known inputs and expected outputs. Test edge cases for Algorithm A (e.g., small datasets, datasets with many identical values, non-convergence scenarios).
    *   `uncertainty.rs`: Test uncertainty calculations corresponding to each estimation method using known inputs (`s*`, `p`, `crm_uncertainty`, etc.) and expected outputs.
    *   `scoring.rs`: Test z-score and z'-score calculations with various inputs, including edge cases like zero standard deviations or uncertainties (if applicable).
    *   `utils.rs`: Test any utility functions or error type implementations.
*   **Test Data:** Use hardcoded small arrays (`ndarray`) or vectors within the test functions representing specific scenarios.
*   **Assertions:** Use standard Rust assertions (`assert!`, `assert_eq!`, `assert_ne!`) and potentially floating-point comparison helpers (e.g., `approx` crate) for numerical results.

### 10.2 Integration Testing Strategy

Integration tests will verify the interactions between different components of the system.

**Python-Rust Integration (Pytest + Compiled Extension):

*   **Scope:** Test the interface defined by PyO3 in `lib.rs`. Verify that Python can correctly call Rust functions, pass data (NumPy arrays, basic types), and receive results or handle exceptions raised from Rust.
*   **Methodology:** Write Python test functions (using `pytest`) that import the compiled Rust extension (`pt_cli_rust`). Call the exposed Rust functions with sample NumPy arrays and parameters. Assert that the returned Python objects (tuples, floats, NumPy arrays, custom classes) have the expected values and types. Test error handling by providing inputs designed to cause specific `CalculationError` variants in Rust and assert that the corresponding Python exceptions are raised.

**Python-Quarto Integration (Pytest + Mocking/Actual Quarto):

*   **Scope:** Test the ability of `reporting.py` to correctly prepare data, generate plots, construct the Quarto command, invoke the Quarto CLI via `subprocess`, and handle potential errors from Quarto.
*   **Methodology:**
    *   *Mocked Approach:* Mock `subprocess.run`. Test that `reporting.py` generates the expected intermediate JSON data file, generates plot files (check existence/content if simple), and calls `subprocess.run` with the correctly formatted Quarto command arguments (template path, output path, format, data parameters).
    *   *Actual Quarto Call (requires Quarto installed in test environment):* Run tests that invoke the actual Quarto CLI on a minimal, known `.qmd` template and a sample intermediate data file. Verify that Quarto executes without errors (check return code) and produces an output file (e.g., HTML or PDF). This validates the basic interaction but not the full report content.

### 10.3 End-to-End Testing Strategy

End-to-end (E2E) tests will simulate user interaction by invoking the packaged CLI application from the command line and verifying the final outputs (console messages, generated reports).

*   **Framework:** Use shell scripting or a Python test runner (like `pytest`) that executes the `pt-cli` command as a subprocess.
*   **Scope:** Test the main user workflows defined by the CLI sub-commands (`calculate`, `validate-data`, `generate-report-only`).
*   **Methodology:**
    1.  Prepare sample input data files (CSV/Excel) and configuration files (YAML/TOML) representing various scenarios (see Section 10.4).
    2.  Execute `pt-cli` commands with different arguments and options targeting these sample files (e.g., `pt-cli calculate sample_data.csv --config sample_config.yaml -o test_report -f html`).
    3.  Capture and assert console output (using `rich`'s capabilities for capturing output might be useful if running via Python subprocess, or redirecting stdout/stderr in shell scripts).
    4.  Check for the existence and basic validity of generated output files (reports, intermediate JSON if requested).
    5.  Verify the content of generated reports (see Section 10.5).
    6.  Test error conditions by providing invalid inputs (non-existent files, malformed data, invalid config) and assert that the expected user-facing error messages are printed to the console and the application exits gracefully (e.g., with a non-zero exit code).

### 10.4 Sample Datasets Definition

A suite of sample datasets will be created to test various conditions:

*   **Normal Case (CSV/Excel):** A typical dataset with 20-50 participants, reasonably well-behaved data suitable for Algorithm A.
*   **Large Dataset:** A dataset meeting the performance requirement sizes (e.g., 1000+ results) to test NFR-PE-001.
*   **Small Dataset:** A dataset with very few participants (e.g., < 5) to test robustness of algorithms.
*   **Dataset with Outliers:** Data containing obvious outliers to verify the robustness of Algorithm A or specific outlier handling configurations (FR-CM-003c).
*   **Dataset with Identical Values:** Data where many participants report the exact same value.
*   **Dataset for CRM/Formulation:** Minimal data, primarily used to test workflows where `x_pt` comes from config/arguments, not participant consensus.
*   **Dataset with Missing/Invalid Data:** Files with missing columns, incorrect data types (e.g., text in result column), missing values (`NaN`) to test data validation (FR-DI-003, FR-DI-004, FR-DI-006).
*   **Dataset with Participant Uncertainties:** Data including a column for `u(x_i)` to test z'-score calculation (FR-PS-002).
*   **Malformed Files:** Empty files, files with incorrect delimiters (for CSV), corrupted Excel files (if possible to simulate).

These datasets will be stored within the test suite directory.

### 10.5 Report Verification Strategy

Verifying the content of generated reports (PDF, HTML, Word) is challenging to automate fully. A multi-pronged approach will be used:

1.  **Existence Check:** E2E tests will verify that report files are created in the expected format and location.
2.  **Smoke Test (Content Parsing):** For HTML reports, basic parsing (e.g., using `BeautifulSoup`) can check for the presence of key sections (identified by headers or specific IDs/classes) and expected keywords or values (e.g., check if the calculated `x_pt` value appears somewhere in the text). For PDF, text extraction tools (`pdftotext` from `poppler-utils`, or Python libraries like `PyPDF2`, `pdfminer.six`) can be used similarly, though layout makes exact matching harder. Word documents are more difficult to parse automatically.
3.  **Intermediate Data Verification:** Since the report content is derived from the data passed to Quarto (e.g., the intermediate JSON file), rigorously verifying the *correctness* of this intermediate data provides high confidence in the report content. Unit and integration tests should ensure the Rust engine produces correct numerical results, and Python correctly aggregates these into the structure passed to Quarto.
4.  **Visual Inspection (Manual):** Key reports generated during E2E testing using representative datasets (normal case, outlier case) will be manually inspected during development and before releases to ensure layout, plots, and content are rendered correctly and professionally across different formats (especially PDF and HTML).
5.  **Plot Verification:** Unit/Integration tests for `reporting.py` can verify that plot files are generated. For critical plots, image comparison libraries (like `pytest-mpl` or `Pillow`) could potentially be used to compare generated plots against baseline reference images, although this can be brittle.

This comprehensive test plan, combining automated unit, integration, and E2E tests with targeted manual verification of reports, aims to ensure the PT-CLI application is robust, reliable, and meets all specified requirements.
