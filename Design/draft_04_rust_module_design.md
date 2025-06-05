## 4. Module-Level Design - Rust Calculation Engine

This section details the design of the Rust calculation engine, which is responsible for performing the computationally intensive statistical analyses required by the PT-CLI. Implemented as a Rust library callable from Python via PyO3, this engine ensures high performance (NFR-PE-001) and leverages Rust's memory safety features for reliability (NFR-RL-003). The design focuses on implementing the specific algorithms mandated by ISO 13528:2022 and the functional requirements (FR-AV, FR-UC, FR-PS) in a modular and maintainable manner (NFR-MA-002).

### 4.1 `lib.rs`: PyO3 Module Definition and Interface

**Purpose:** This file serves as the root of the Rust library crate and defines the Python module interface using PyO3. It declares the sub-modules (`estimators`, `uncertainty`, `scoring`, `utils`) and exposes the necessary public functions and potentially structs (wrapped as Python classes using `#[pyclass]`) to the Python layer.

**Key Responsibilities:**

*   **Module Declaration:** Declare the Rust sub-modules (`mod estimators;`, `mod uncertainty;`, etc.).
*   **PyO3 Setup:** Define the main `#[pymodule]` function (e.g., `pt_cli_rust`) that PyO3 uses to initialize the Python module.
*   **Function Exposure:** Within the `#[pymodule]` function, use `m.add_function(wrap_pyfunction!(...))` to expose the public Rust functions from the sub-modules that need to be called from Python (as shown conceptually in Section 2.3).
*   **Type Mapping:** Handle the necessary type conversions between Python objects (like NumPy arrays passed via `PyReadonlyArray`) and Rust's internal types (like `ndarray::ArrayView` or `Vec<f64>`). Define any custom `#[pyclass]` wrappers if complex Rust structs need to be returned to Python.
*   **Error Bridging:** Ensure that Rust errors (`Result<T, E>`) are correctly translated into Python exceptions (`PyResult<T>` -> `PyErr`) for handling in the Python layer.

**Primary Structures:**

*   `#[pymodule]` function.
*   `use` statements for PyO3 and sub-modules.
*   `wrap_pyfunction!` macros for each exposed function.

**Interactions:**

*   Acts as the bridge between Python and the Rust calculation logic.
*   Imports and re-exports functions/structs from `estimators`, `uncertainty`, `scoring`, and `utils` modules.
*   Uses `PyO3` library extensively.
*   Uses `numpy` crate (via PyO3) for array handling.

### 4.2 `estimators.rs`: Assigned Value (`x_pt`) Calculation

**Purpose:** This module implements the core logic for calculating the assigned value (`x_pt`) according to the methods specified in ISO 13528:2022 and required by the SRS (FR-AV-001 to FR-AV-007).

**Key Responsibilities:**

*   **Algorithm A Implementation (FR-AV-002):** Implement the iterative robust statistics algorithm (ISO 13528:2022, Annex C). This involves:
    *   Initial calculation of median and scaled MAD (Median Absolute Deviation) or NIQR (Normalized Interquartile Range).
    *   Iterative updating of `x*` (robust mean) and `s*` (robust standard deviation) based on Huber's robust M-estimation principles or similar robust techniques described in the standard.
    *   Applying Huber's Proposal 2 or equivalent weighting/winsorizing function (`psi` function) to down-weight or cap the influence of outliers.
    *   Checking for convergence based on changes in `x*` and `s*` against a tolerance (configurable via Python, FR-CM-003).
    *   Handling potential non-convergence within a maximum number of iterations (configurable).
    *   Returning the final robust mean (`x*` which becomes `x_pt`), robust standard deviation (`s*`), and the number of data points included in the final calculation.
*   **CRM-Based Calculation (FR-AV-003):** Implement a simple function that takes the certified value and its uncertainty (passed from Python, originating from configuration or input DR-IN-003) and returns the certified value as `x_pt`.
*   **Formulation-Based Calculation (FR-AV-004):** Implement a function that takes the known value based on formulation (passed from Python) and returns it as `x_pt`.
*   **Expert Consensus Calculation (FR-AV-005):** Implement a function that takes the consensus value derived from expert laboratories (passed from Python, potentially requiring pre-processing in Python to identify expert results) and returns it as `x_pt`.
*   **Method Selection Logic:** While the primary selection (FR-AV-006) happens in Python (`main.py`), this module provides the distinct functions for each method to be called.
*   **Numerical Stability:** Ensure calculations are performed using appropriate data types (e.g., `f64`) and numerically stable algorithms.

**Primary Functions:**

*   `calculate_algorithm_a(results: ArrayView1<f64>, tolerance: f64, max_iterations: usize) -> Result<(f64, f64, usize), CalculationError>`
*   `calculate_from_crm(crm_value: f64) -> Result<f64, CalculationError>`
*   `calculate_from_formulation(formulation_value: f64) -> Result<f64, CalculationError>`
*   `calculate_from_expert_consensus(expert_value: f64) -> Result<f64, CalculationError>`
*   Internal helper functions for median, MAD/NIQR, psi function, iteration steps.

**Interactions:**

*   Called from `lib.rs` (ultimately from Python).
*   Uses `ndarray` for array operations.
*   May use `statrs` or similar crates for statistical distributions or basic functions if needed.
*   Uses utility functions from `utils.rs` (e.g., for custom error types).

### 4.3 `uncertainty.rs`: Uncertainty (`u(x_pt)`) Calculation

**Purpose:** This module implements the logic for calculating the standard uncertainty of the assigned value (`u(x_pt)`) corresponding to the method used for `x_pt` determination, as required by FR-UC-001 and FR-UC-002.

**Key Responsibilities:**

*   **Uncertainty for Consensus Values (FR-UC-002a):** Implement the calculation for `u(x_pt)` when `x_pt` is derived from participant consensus (e.g., Algorithm A). Typically `u(x_pt) = 1.25 * s* / sqrt(p)`, where `s*` is the robust standard deviation and `p` is the number of participants included in the robust calculation (both returned by `estimators::calculate_algorithm_a`).
*   **Uncertainty for CRM Values (FR-UC-002b):** Implement a function that takes the standard uncertainty stated on the CRM certificate (passed from Python) and returns it as `u(x_pt)`.
*   **Uncertainty for Formulation Values (FR-UC-002c):** Implement a function that takes the estimated uncertainty associated with the formulation process (passed from Python) and returns it as `u(x_pt)`.
*   **Uncertainty for Expert Consensus:** Define the method for calculating `u(x_pt)` when expert consensus is used (e.g., standard error of the mean of expert results, if applicable, requiring expert results and count to be passed).

**Primary Functions:**

*   `calculate_uncertainty_consensus(robust_std_dev: f64, num_participants: usize) -> Result<f64, CalculationError>`
*   `calculate_uncertainty_crm(crm_uncertainty: f64) -> Result<f64, CalculationError>`
*   `calculate_uncertainty_formulation(formulation_uncertainty: f64) -> Result<f64, CalculationError>`
*   `calculate_uncertainty_expert(...) -> Result<f64, CalculationError>` (parameters depend on chosen method)

**Interactions:**

*   Called from `lib.rs` (ultimately from Python).
*   Takes results from `estimators.rs` (like `s*`, `p`) or values passed from Python (like `crm_uncertainty`).
*   Uses utility functions/types from `utils.rs`.

### 4.4 `scoring.rs`: Performance Score Calculation

**Purpose:** This module implements the calculation of participant performance scores (z-scores and z		-scores) based on the calculated `x_pt`, `u(x_pt)`, and participant data, as required by FR-PS-001 and FR-PS-002.

**Key Responsibilities:**

*   **Z-Score Calculation (FR-PS-001):** Implement the formula `z = (x_i - x_pt) / σ_pt`. Takes an array of participant results (`x_i`), the assigned value (`x_pt`), and the standard deviation for proficiency assessment (`σ_pt`, passed from Python, originating from config/CLI FR-PS-003). Returns an array of z-scores.
*   **Z		-Score (Zeta Score) Calculation (FR-PS-002):** Implement the formula `z' = (x_i - x_pt) / sqrt(u(x_i)^2 + u(x_pt)^2)`. Takes an array of participant results (`x_i`), an array of corresponding participant uncertainties (`u(x_i)`, passed from Python, originating from input data FR-PS-003), the assigned value (`x_pt`), and its uncertainty (`u(x_pt)`). Returns an array of z		-scores. Handle cases where `u(x_i)` might be missing or zero if applicable.

**Primary Functions:**

*   `calculate_z_scores(results: ArrayView1<f64>, x_pt: f64, sigma_pt: f64) -> Result<Array1<f64>, CalculationError>`
*   `calculate_z_prime_scores(results: ArrayView1<f64>, u_results: ArrayView1<f64>, x_pt: f64, u_x_pt: f64) -> Result<Array1<f64>, CalculationError>`

**Interactions:**

*   Called from `lib.rs` (ultimately from Python).
*   Takes participant data arrays and calculation results (`x_pt`, `u(x_pt)`, `σ_pt`) as input.
*   Uses `ndarray` for efficient array operations.
*   Uses utility functions/types from `utils.rs`.

### 4.5 `utils.rs`: Common Utilities and Data Structures

**Purpose:** This module contains shared code used by other modules within the Rust engine, such as custom error types, mathematical constants, or helper functions for common statistical operations.

**Key Responsibilities:**

*   **Custom Error Type:** Define a custom error enum or struct (e.g., `CalculationError`) that can represent various failure modes within the engine (e.g., non-convergence, invalid input dimensions, division by zero). Implement `std::error::Error` and `std::fmt::Display` for it. Provide conversions from this error type to `PyErr` for PyO3.
*   **Mathematical Helpers:** Include any necessary mathematical constants or simple helper functions (e.g., robust scaling factors like 1.4826 for MAD) not readily available in dependencies.
*   **Shared Structs:** If complex data structures need to be passed between Rust modules (though less likely for this design), they could be defined here.

**Primary Structures:**

*   `enum CalculationError { ... }` or `struct CalculationError { ... }`
*   Associated `impl` blocks for error handling and conversion.
*   Potentially `const` definitions.

**Interactions:**

*   Used by `estimators.rs`, `uncertainty.rs`, `scoring.rs`, and `lib.rs`.

### 4.6 Rust Error Handling Strategy

The error handling strategy within the Rust engine focuses on robustness and clear communication back to the Python layer.

1.  **Internal Errors:** Functions within `estimators`, `uncertainty`, and `scoring` will return `Result<T, CalculationError>`, where `CalculationError` is the custom error type defined in `utils.rs`. This allows specific error conditions (e.g., Algorithm A non-convergence, division by zero in scoring) to be represented distinctly.
2.  **Error Propagation:** Errors are propagated upwards using the `?` operator within Rust.
3.  **PyO3 Boundary:** In `lib.rs`, the exposed functions wrapped with `#[pyfunction]` will have a return type of `PyResult<T>`. The conversion from `Result<T, CalculationError>` to `PyResult<T>` will be handled either by implementing `From<CalculationError> for PyErr` or by explicitly matching on the `Result` in the wrapper function and creating an appropriate `PyErr` (e.g., `PyValueError`, `PyRuntimeError`) with a descriptive message derived from the `CalculationError`.
4.  **Python Handling:** The Python code calling the Rust functions will use `try...except` blocks to catch these Python exceptions (e.g., `except ValueError as e:`), allowing it to report the error to the user via `rich` or log it appropriately (NFR-RL-002).

This strategy ensures that Rust's compile-time checks and explicit error handling are utilized, while providing meaningful error information to the Python layer and ultimately the user.
