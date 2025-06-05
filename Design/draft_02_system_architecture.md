## 2. System Architecture

This section outlines the high-level architecture of the Proficiency Testing Command Line Interface (PT-CLI). The architecture is designed to meet the requirements specified in the SRS, emphasizing modularity, performance for calculations, and clear separation of concerns between the user interface/workflow logic and the core statistical computations.

The PT-CLI adopts a hybrid architecture combining Python for the main application layer and Rust for a high-performance calculation engine. This approach leverages Python's strengths in rapid development, rich ecosystem for tasks like CLI creation (Typer), data handling (Pandas), and configuration management (Pydantic, PyYAML/TOML), while utilizing Rust's performance and memory safety for the computationally intensive statistical algorithms defined in ISO 13528:2022. Communication between these two layers is facilitated by PyO3, which provides seamless Python bindings for Rust code.

### 2.1 Component Diagram Description

The system is composed of several key components organized into two primary layers: the Python Application Layer and the Rust Calculation Engine. An external dependency, the Quarto CLI, is utilized for report generation.

**Python Application Layer:**

*   **`main.py` (CLI Entry Point):** Built using Typer, this module serves as the main entry point for the user. It parses command-line arguments, orchestrates the overall workflow (data loading, configuration, calculation, reporting), and provides user feedback via the `rich` library.
*   **`config.py` (Configuration Management):** Responsible for loading, validating (using Pydantic models), and providing access to configuration settings from YAML or TOML files. It handles default configurations and merges user-provided settings.
*   **`data_io.py` (Data Input/Output & Validation):** Handles reading input data from CSV/Excel files using Pandas. It performs initial data validation (structure, basic types) using Pydantic models defined based on configuration (e.g., expected column names) before passing data to the calculation engine. It may also handle writing intermediate data files if needed for Quarto.
*   **`reporting.py` (Reporting Orchestration):** Prepares data required for the final report (e.g., calculation results, summary statistics, configuration parameters). It generates necessary plots using Matplotlib/Seaborn, saving them as image files or preparing them for dynamic generation. Crucially, it invokes the external Quarto CLI via the `subprocess` module, passing the appropriate `.qmd` template, prepared data (potentially via intermediate files or command-line arguments), and output format/path parameters.
*   **`pt_cli_rust` (Rust Engine Interface - via PyO3):** This is not a distinct Python module file but represents the Python interface to the compiled Rust library. Python code (primarily in `main.py` or a dedicated orchestration module) interacts with this interface to call Rust functions for calculations.

**Rust Calculation Engine (Compiled Library):**

*   **`lib.rs` (PyO3 Module Definition):** Defines the main Rust library structure and the PyO3 module interface, exposing Rust functions and structs to Python. It handles the conversion between Python types (e.g., NumPy arrays via PyO3 features) and Rust's internal data structures (e.g., `ndarray` arrays).
*   **`estimators.rs` (Assigned Value Estimators):** Contains the core implementations of the statistical methods for calculating the assigned value (`x_pt`) as per ISO 13528:2022. This includes functions for Algorithm A, CRM-based calculation, formulation-based calculation, and expert consensus.
*   **`uncertainty.rs` (Uncertainty Calculation):** Implements the functions to calculate the standard uncertainty of the assigned value (`u(x_pt)`), corresponding to the methods used in `estimators.rs`.
*   **`scoring.rs` (Performance Scoring):** Implements the functions to calculate participant performance scores, specifically z-scores and z	'-scores.
*   **`utils.rs` (Utilities & Shared Types):** Contains shared data structures (structs), constants, and utility functions used across the Rust engine modules (e.g., robust statistical helpers, error types).

**External Components:**

*   **Quarto CLI:** An external command-line tool, installed separately by the user. The Python layer invokes Quarto to render `.qmd` markdown files into final report formats (PDF, HTML, Word).

### 2.2 Data Flow Diagram Description

The typical data flow for a `calculate` command execution is as follows:

1.  **User Input:** The user executes the PT-CLI via the command line, providing arguments such as the input data file path, configuration file path (optional), desired calculation method (optional), and output report specifications.
2.  **CLI Parsing (`main.py`):** Typer parses the CLI arguments.
3.  **Configuration Loading (`config.py`):** The configuration module loads the specified (or default) configuration file, validates it using Pydantic, and makes the settings available.
4.  **Data Loading (`data_io.py`):** The data I/O module reads the specified input data file (CSV/Excel) into a Pandas DataFrame.
5.  **Data Validation (`data_io.py`):** Pydantic models (informed by configuration) are used to validate the structure and data types of the input DataFrame. Errors are reported back to the user via `main.py` and `rich`.
6.  **Data Preparation (Python):** Relevant data columns (e.g., participant results, uncertainties if provided) are extracted, potentially converted to NumPy arrays suitable for passing to Rust.
7.  **Calculation Invocation (Python -> Rust):** The main workflow logic calls the appropriate functions within the Rust calculation engine via the PyO3 interface (`pt_cli_rust`), passing the prepared data arrays and relevant configuration parameters (e.g., calculation method choice, Algorithm A parameters).
8.  **Rust Calculation (`estimators.rs`, `uncertainty.rs`, `scoring.rs`):** The Rust engine performs the requested calculations (e.g., Algorithm A for `x_pt` and `s*`, `u(x_pt)` calculation, z-score calculation) using efficient, compiled code and libraries like `ndarray` and `statrs`.
9.  **Return Results (Rust -> Python):** The Rust functions return the calculated results (e.g., `x_pt`, `u(x_pt)`, `s*`, list/array of z-scores) back to the Python layer, potentially as tuples or custom Python objects mapped from Rust structs via PyO3.
10. **Result Handling (Python):** The Python layer receives the results from Rust.
11. **Report Data Preparation (`reporting.py`):** The reporting module gathers all necessary information for the report: input data summary, configuration used, calculation results, participant scores. It generates required plots (e.g., histograms) using Matplotlib/Seaborn and saves them to temporary files or prepares them for dynamic inclusion.
12. **Quarto Invocation (`reporting.py`):** The reporting module constructs the command to execute the external Quarto CLI, specifying the `.qmd` template (default or custom), the output file path and format, and potentially passing data parameters or pointing Quarto to intermediate data files (e.g., JSON/CSV containing results).
13. **Quarto Rendering (External):** Quarto reads the `.qmd` template, executes any embedded code chunks (if applicable), incorporates data and plots, and renders the final report file (PDF, HTML, Word).
14. **Console Feedback (`main.py`):** Throughout the process, `main.py` uses `rich` to provide informative status updates and displays key results (like calculated `x_pt`) directly to the console.
15. **Final Output:** The user receives the generated report file in the specified location and format, along with console output summarizing the execution.

Error conditions at any stage (e.g., file not found, invalid data, calculation errors in Rust, Quarto rendering failure) are propagated back through the layers and reported clearly to the user via the console.

### 2.3 Internal API Definition (Python-Rust via PyO3)

The interface between the Python Application Layer and the Rust Calculation Engine will be defined using PyO3. Python will primarily interact with Rust by calling functions exposed from the compiled Rust library. Data exchange will heavily rely on NumPy arrays for numerical data, leveraging PyO3's support for efficient, zero-copy (where possible) transfer.

**Key Principles:**

*   **Data Input to Rust:** Participant results and uncertainties will typically be passed as NumPy arrays (`ndarray::PyArray`). Configuration parameters relevant to calculations (e.g., convergence criteria, method choice flags) will be passed as basic Python types (int, float, bool, str) which PyO3 maps to corresponding Rust types.
*   **Data Output from Rust:** Calculation results (`x_pt`, `u(x_pt)`, `s*`, scores) will be returned as basic types (float) or potentially grouped within simple Python tuples or dictionaries. For more complex return structures, custom Rust structs can be exposed as Python classes using `#[pyclass]`.
*   **Error Handling:** Rust functions will return `PyResult<T>` (or equivalent using custom error types mapped via PyO3). Errors originating in Rust (e.g., calculation failure, invalid input dimensions) will be converted into Python exceptions (e.g., `ValueError`, `RuntimeError`, or custom exception types defined in Python) allowing the Python layer to handle them gracefully.

**Example Function Signatures (Conceptual Rust `lib.rs`):**

```rust
use pyo3::prelude::*;
use numpy::{PyReadonlyArray1, PyArray1};
use pyo3::wrap_pyfunction;

// Placeholder for custom error type
#[derive(Debug)]
struct CalculationError { msg: String }

// --- Estimators --- 

#[pyfunction]
fn calculate_algorithm_a(results: PyReadonlyArray1<f64>, tolerance: f64, max_iterations: usize) -> PyResult<(f64, f64, usize)> { 
    // ... implementation using results.as_array() ... 
    // Returns Ok((robust_mean, robust_std_dev, num_participants_included))
    // Returns Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Error message")) on failure
    unimplemented!() 
}

#[pyfunction]
fn calculate_from_crm(crm_value: f64, crm_uncertainty: f64) -> PyResult<f64> {
    // ... simple calculation ...
    Ok(crm_value) // x_pt is just the CRM value
}

// ... other estimator functions (formulation, expert) ...

// --- Uncertainty --- 

#[pyfunction]
fn calculate_uncertainty_consensus(robust_std_dev: f64, num_participants: usize) -> PyResult<f64> {
    // ... implementation: 1.25 * robust_std_dev / (num_participants as f64).sqrt() ...
    unimplemented!()
}

#[pyfunction]
fn calculate_uncertainty_crm(crm_uncertainty: f64) -> PyResult<f64> {
    // ... simple calculation ...
    Ok(crm_uncertainty)
}

// ... other uncertainty functions ...

// --- Scoring --- 

#[pyfunction]
fn calculate_z_scores(results: PyReadonlyArray1<f64>, x_pt: f64, sigma_pt: f64) -> PyResult<Py<PyArray1<f64>>> {
    // ... implementation: (results - x_pt) / sigma_pt ...
    // Returns PyResult containing a new PyArray1<f64>
    unimplemented!()
}

#[pyfunction]
fn calculate_z_prime_scores(results: PyReadonlyArray1<f64>, u_results: PyReadonlyArray1<f64>, x_pt: f64, u_x_pt: f64) -> PyResult<Py<PyArray1<f64>>> {
    // ... implementation: (results - x_pt) / sqrt(u_results^2 + u_x_pt^2) ...
    // Returns PyResult containing a new PyArray1<f64>
    unimplemented!()
}

// --- PyO3 Module Definition --- 

#[pymodule]
fn pt_cli_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_algorithm_a, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_from_crm, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_uncertainty_consensus, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_uncertainty_crm, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_z_scores, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_z_prime_scores, m)?)?;
    // ... add other functions ...
    Ok(())
}
```

This API definition provides a clear separation, allowing the Python layer to treat the Rust engine as a high-performance library for specific statistical tasks, passing data in efficient formats and receiving results or well-defined errors.
