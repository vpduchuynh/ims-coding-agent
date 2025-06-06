## Software Requirements Specification: Proficiency Testing CLI

Version: 1.0

Date: June 5, 2025

### Table of Contents

1. Introduction
    
    1.1 Purpose
    
    1.2 Scope
    
    1.3 Definitions, Acronyms, and Abbreviations
    
    1.4 References
    
    1.5 Overview
    
2. Overall Description
    
    2.1 Product Perspective
    
    2.2 Product Functions
    
    2.3 User Characteristics
    
    2.4 Constraints
    
    2.5 Assumptions and Dependencies
    
3. Specific Requirements
    
    3.1 Functional Requirements
    
    3.1.1 Data Input and Validation
    
    3.1.2 Configuration Management
    
    3.1.3 Assigned Value Calculation
    
    3.1.4 Uncertainty Calculation
    
    3.1.5 Performance Score Calculation
    
    3.1.6 Reporting
    
    3.1.7 Command Line Interface (CLI)
    
    3.2 Non-Functional Requirements
    
    3.2.1 Performance
    
    3.2.2 Reliability
    
    3.2.3 Usability
    
    3.2.4 Maintainability
    
    3.2.5 Portability
    
    3.2.6 Security
    
    3.3 Interface Requirements
    
    3.3.1 User Interfaces
    
    3.3.2 Software Interfaces
    
    3.4 Data Requirements
    
    3.4.1 Input Data
    
    3.4.2 Output Data
    
    3.4.3 Configuration Data
    

### 1. Introduction

#### 1.1 Purpose

This Software Requirements Specification (SRS) document describes the functional and non-functional requirements for the Proficiency Testing Command Line Interface (PT-CLI) application. The PT-CLI is designed for proficiency testing providers to estimate assigned values for proficiency test items in alignment with the ISO 13528:2022 guidelines. It will utilize Python for the main application logic and user interface, and Rust for computationally intensive statistical calculations, with Quarto for report generation.

#### 1.2 Scope

The PT-CLI will provide functionalities for:

- Importing participant proficiency testing data.
    
- Calculating assigned values (`x_pt`) using methods specified in ISO 13528:2022, including robust statistical methods like Algorithm A.
    
- Calculating the standard uncertainty of the assigned value (`u(x_pt)`).
    
- Calculating participant performance scores (e.g., z-scores, z'-scores).
    
- Generating comprehensive reports in various formats (PDF, HTML, Word) using Quarto.
    
- Allowing user configuration for calculation parameters and reporting options.
    

The application is intended to be used as a command-line tool. It will not include a graphical user interface (GUI).

#### 1.3 Definitions, Acronyms, and Abbreviations

- **PT:** Proficiency Testing
    
- **CLI:** Command Line Interface
    
- **SRS:** Software Requirements Specification
    
- **ISO:** International Organization for Standardization
    
- **CRM:** Certified Reference Material
    
- `x_pt`: Assigned value for a proficiency test item
    
- `u(x_pt)`: Standard uncertainty of the assigned value
    
- `σ_pt`: Standard deviation for proficiency assessment
    
- **QMD:** Quarto Markdown Document
    
- **PyO3:** Python bindings for Rust
    

#### 1.4 References

- ISO 13528:2022: "Statistical methods for use in proficiency testing by interlaboratory comparison."
    
- Proposal: Proficiency Testing CLI with Python and Rust (Quarto Reporting) (ID: `proficiency_testing_cli_proposal`)
    
- Typer documentation: [https://typer.tiangolo.com/](https://typer.tiangolo.com/ "null")
    
- PyO3 documentation: [https://pyo3.rs/](https://pyo3.rs/ "null")
    
- Quarto documentation: [https://quarto.org/](https://quarto.org/ "null")
    
- Polars documentation: [https://polars.rs/](https://polars.rs/ "null")
    
- Pydantic documentation: [https://pydantic-docs.helpmanual.io/](https://pydantic-docs.helpmanual.io/ "null")
    

#### 1.5 Overview

This document is organized into three main sections:

- **Section 1 (Introduction):** Provides the purpose, scope, definitions, references, and overview of the SRS.
    
- **Section 2 (Overall Description):** Describes the product perspective, product functions, user characteristics, constraints, and assumptions.
    
- **Section 3 (Specific Requirements):** Details the functional, non-functional, interface, and data requirements for the PT-CLI.
    

### 2. Overall Description

#### 2.1 Product Perspective

The PT-CLI is a standalone desktop application intended to be run from a command line environment. It leverages a hybrid architecture, with a Python front-end for user interaction and workflow management, and a Rust back-end for performance-critical calculations. Quarto is used as an external tool for report generation. The PT-CLI will be installable as a Python package, which includes the compiled Rust extension.

#### 2.2 Product Functions

The primary functions of the PT-CLI are:

1. **Data Import:** Allow users to import proficiency testing data from standard file formats (CSV, Excel).
    
2. **Data Validation:** Perform validation on input data to ensure correctness and completeness.
    
3. **Configuration:** Allow users to configure calculation parameters and reporting options via configuration files.
    
4. **Statistical Calculation:** Perform robust statistical calculations as per ISO 13528:2022 to determine assigned values and their uncertainties. This includes:
    
    - Consensus value from participant results (e.g., Algorithm A).
        
    - Calculation based on CRM values.
        
    - Calculation based on formulation.
        
    - Calculation based on expert laboratory consensus.
        
5. **Performance Scoring:** Calculate participant performance scores (z-scores, z'-scores).
    
6. **Report Generation:** Generate comprehensive, publication-quality reports in multiple formats (PDF, HTML, Word) using Quarto.
    
7. **CLI Operation:** Provide a user-friendly command-line interface for all operations.
    

#### 2.3 User Characteristics

The primary users of the PT-CLI are expected to be:

- Proficiency testing providers.
    
- Statisticians or technical staff involved in PT scheme design and data analysis.
    
- Users comfortable with command-line interfaces.
    
- Users with a working knowledge of ISO 13528 concepts.
    

#### 2.4 Constraints

- **Operating System:** The system should be primarily developed and tested for common desktop operating systems (Windows, macOS, Linux).
    
- **Programming Languages:** The core application logic will be in Python. Performance-critical calculations will be implemented in Rust.
    
- **External Dependencies:**
    
    - Python 3.8+
        
    - Rust toolchain (for building the Rust extension)
        
    - Quarto CLI (must be installed separately by the user)
        
    - Python libraries: Typer, Polars, Pydantic, PyYAML/TOML, Rich, Matplotlib/Seaborn, subprocess.
        
    - Rust crates: PyO3, statrs, ndarray, ndarray-stats, serde.
        
- **No GUI:** The application will be CLI-only.
    
- **Performance:** Rust components are chosen for performance in calculations. Overall performance should be acceptable for typical PT data set sizes.
    

#### 2.5 Assumptions and Dependencies

- Users will have the Quarto CLI installed and accessible in their system's PATH.
    
- Input data files will adhere to expected formats and structures.
    
- Users understand the statistical methods and options provided by the tool.
    
- The Rust calculation engine will be correctly compiled and packaged with the Python application.
    

### 3. Specific Requirements

#### 3.1 Functional Requirements

##### 3.1.1 Data Input and Validation

- **FR-DI-001:** The system shall allow users to specify input data files in CSV or Excel (XLSX) format via a CLI argument.
    
- **FR-DI-002:** The system shall use `polars` for reading and handling tabular data.
    
- **FR-DI-003:** The system shall validate the structure of the input data (e.g., presence of required columns like 'participant_id', 'result').
    
- **FR-DI-004:** The system shall validate the data types of relevant columns (e.g., numerical results).
    
- **FR-DI-005:** The system shall use `Pydantic` for defining data models and performing data validation.
    
- **FR-DI-006:** The system shall provide clear error messages if input data validation fails.
    

##### 3.1.2 Configuration Management

- **FR-CM-001:** The system shall allow users to specify a configuration file (YAML or TOML format) via a CLI argument.
    
- **FR-CM-002:** The system shall load default configuration settings if no user-specified file is provided.
    
- **FR-CM-003:** The configuration shall allow users to specify:
    
    - Default method for assigned value calculation (e.g., "AlgorithmA", "CRM").
        
    - Parameters for robust statistics (e.g., convergence criteria, iteration limits for Algorithm A).
        
    - Configuration options for outlier handling/identification, such as selecting from a list of supported outlier tests (e.g., Grubbs', Dixon's Q if implemented) or adjusting parameters for the chosen robust statistical method's sensitivity to outliers (if applicable and configurable beyond the standard Algorithm A parameters).
        
    - Default report output format (e.g., "pdf", "html").
        
    - Path to a custom Quarto template file.
        
- **FR-CM-004:** The system shall validate the structure and values within the configuration file.
    

##### 3.1.3 Assigned Value Calculation

- **FR-AV-001:** The system's Rust calculation engine shall implement methods for determining the assigned value (`x_pt`) as per ISO 13528:2022.
    
- **FR-AV-002:** The system shall implement Algorithm A (Annex C, ISO 13528:2022) for calculating the robust mean and robust standard deviation from participant results.
    
- **FR-AV-003:** The system shall support calculation of `x_pt` based on the certified value of a Certified Reference Material (CRM).
    
- **FR-AV-004:** The system shall support calculation of `x_pt` based on formulation (known value scheme).
    
- **FR-AV-005:** The system shall support calculation of `x_pt` based on consensus value from designated expert laboratories.
    
- **FR-AV-006:** The system shall allow the user to select the method for `x_pt` calculation via CLI argument or configuration file.
    
- **FR-AV-007:** The Rust calculation engine shall handle numerical computations efficiently.
    

##### 3.1.4 Uncertainty Calculation

- **FR-UC-001:** The system's Rust calculation engine shall implement methods for determining the standard uncertainty of the assigned value (`u(x_pt)`) as per ISO 13528:2022.
    
- **FR-UC-002:** The calculation of `u(x_pt)` shall be appropriate for the method used to determine `x_pt`.
    
    - For consensus values (e.g., from Algorithm A), `u(x_pt)` shall be calculated typically as `1.25 * s* / sqrt(p)`, where `s*` is the robust standard deviation and `p` is the number of data points included.
        
    - For CRM-based values, `u(x_pt)` should be derived from the uncertainty stated on the CRM certificate.
        
    - For formulation-based values, `u(x_pt)` should be estimated based on the uncertainties of the formulation process.
        

##### 3.1.5 Performance Score Calculation

- **FR-PS-001:** The system's Rust calculation engine shall calculate z-scores for participants using the formula: `z = (x_i - x_pt) / σ_pt`.
    
    - `x_i`: participant's result.
        
    - `x_pt`: assigned value.
        
    - `σ_pt`: standard deviation for proficiency assessment (must be provided or determined according to ISO 13528 guidelines, e.g., fitness-for-purpose).
        
- **FR-PS-002:** The system's Rust calculation engine shall calculate z'-scores (zeta scores) for participants using the formula: `z' = (x_i - x_pt) / sqrt(u(x_i)^2 + u(x_pt)^2)`.
    
    - `u(x_i)`: standard uncertainty of the participant's result (if available).
        
    - `u(x_pt)`: standard uncertainty of the assigned value.
        
- **FR-PS-003:** The system shall allow input of `σ_pt` (standard deviation for proficiency assessment) via a configuration file parameter or a dedicated CLI argument. Individual participant uncertainties `u(x_i)`, if required for z'-scores, shall be readable from a specified column in the input data file (column name to be configurable).
    

##### 3.1.6 Reporting

- **FR-RP-001:** The system shall generate reports using Quarto.
    
- **FR-RP-002:** The Python layer shall prepare all necessary data (calculated results, participant data, configuration details, plots) for consumption by Quarto.
    
- **FR-RP-003:** Data for Quarto may be passed as parameters to the Quarto render command or written to intermediate files (e.g., JSON, CSV) that the Quarto document reads.
    
- **FR-RP-004:** The system shall allow users to specify the output report file name and format (e.g., PDF, HTML, Word) via CLI arguments.
    
- **FR-RP-005:** The system shall use `matplotlib` or `seaborn` to generate plots (e.g., histograms, kernel density plots of participant data). These plots can be saved as image files for static embedding in Quarto or generated dynamically by Python code chunks within the `.qmd` file.
    
- **FR-RP-006:** The Python layer shall invoke the Quarto CLI using the `subprocess` module to render the report from a `.qmd` template.
    
- **FR-RP-007:** The system shall include at least one default `.qmd` report template.
    
- **FR-RP-008:** The system shall allow users to specify a custom `.qmd` template via configuration.
    
- **FR-RP-009:** Reports shall include:
    
    - Summary of the PT round/data.
        
    - Method used for `x_pt` determination.
        
    - The calculated `x_pt` and its `u(x_pt)`.
        
    - Robust standard deviation (`s*`) if applicable.
        
    - Number of participants included in calculations.
        
    - Participant performance scores (z-scores, z'-scores).
        
    - Relevant plots (e.g., data distribution).
        
- **FR-RP-010:** The system shall provide informative console output using the `rich` library for immediate feedback, distinct from the formal Quarto report.
    

##### 3.1.7 Command Line Interface (CLI)

- **FR-CLI-001:** The system shall provide a CLI using the `Typer` library.
    
- **FR-CLI-002:** The CLI shall support sub-commands for different actions (e.g., `calculate`, `validate-data`, `generate-report-only`).
    
- **FR-CLI-003:** CLI arguments and options shall be clearly defined with type hints and help messages.
    
- **FR-CLI-004:** The CLI shall provide mechanisms for specifying:
    
    - Input data file path.
        
    - Configuration file path.
        
    - Calculation method.
        
    - Output report file path and format.
        
- **FR-CLI-005:** The CLI shall support automatic help page generation (inherent from `Typer`).
    
- **FR-CLI-006:** The CLI shall provide clear feedback on progress and errors.
    

#### 3.2 Non-Functional Requirements

##### 3.2.1 Performance

- **NFR-PE-001:** The Rust calculation engine shall process datasets of up to 1,000 participant results using Algorithm A in under 30 seconds, and datasets of up to 5,000 results in under 2 minutes, when run on a reference hardware configuration (e.g., Intel Core i5, 8GB RAM).
    
- **NFR-PE-002:** Report generation time by Quarto should be acceptable for the chosen format and complexity.
    

##### 3.2.2 Reliability

- **NFR-RL-001:** The system shall produce accurate and consistent statistical results as per ISO 13528:2022 guidelines.
    
- **NFR-RL-002:** The system shall handle errors gracefully (e.g., invalid input data, file not found, Quarto rendering errors) and provide informative messages.
    
- **NFR-RL-003:** The Rust components should leverage Rust's memory safety features to prevent common runtime errors.
    

##### 3.2.3 Usability

- **NFR-US-001:** Usability will be assessed through task completion rates by a panel of 3-5 representative users performing predefined common tasks. A target of >90% task completion without assistance will be considered acceptable for these users.
    
- **NFR-US-002:** CLI help messages and documentation shall be clear and comprehensive.
    
- **NFR-US-003:** Error messages shall be user-friendly and guide users toward resolving issues.
    
- **NFR-US-004:** Configuration options shall be well-documented.
    

##### 3.2.4 Maintainability

- **NFR-MA-001:** The Python codebase shall be modular, well-commented, and follow good coding practices (e.g., PEP 8).
    
- **NFR-MA-002:** The Rust codebase shall be modular, well-commented, and follow Rust best practices (e.g., `clippy` lints).
    
- **NFR-MA-003:** The separation of concerns between Python (workflow, I/O, CLI) and Rust (calculations) should enhance maintainability.
    
- **NFR-MA-004:** The build process using `maturin` should be straightforward.
    
- **NFR-MA-005:** A comprehensive test suite (unit and integration tests) shall be provided.
    

##### 3.2.5 Portability

- **NFR-PO-001:** The Python application should be runnable on common operating systems where Python is supported (Windows, macOS, Linux).
    
- **NFR-PO-002:** The Rust extension should be compilable on these target platforms.
    
- **NFR-PO-003:** Quarto CLI dependency implies users must have a compatible Quarto version installed.
    

##### 3.2.6 Security

- **NFR-SE-001:** As a local CLI application processing local files, the primary security concern is validating input to prevent issues like path traversal if file paths are constructed dynamically (though direct user input of full paths is safer).
    
- **NFR-SE-002:** Care should be taken when using `subprocess` to call Quarto, ensuring commands are constructed safely and do not allow arbitrary command injection (generally mitigated by not constructing commands from untrusted external input).
    

#### 3.3 Interface Requirements

##### 3.3.1 User Interfaces

- **IF-UI-001:** The primary user interface will be the Command Line Interface (CLI), as detailed in FR-CLI requirements.
    
- **IF-UI-002:** Console output for progress and immediate results will be provided using the `rich` library.
    

##### 3.3.2 Software Interfaces

- **IF-SI-001 (Python-Rust):** Python will interface with the Rust calculation engine via `PyO3` bindings. Data (e.g., NumPy arrays) will be passed to Rust functions, and results (e.g., tuples, custom Rust structs mapped to Python objects) will be returned.
    
- **IF-SI-002 (Python-Quarto):** Python will interface with the Quarto CLI using the `subprocess` module, passing arguments for rendering specific `.qmd` files to specified output formats and locations.
    
- **IF-SI-003 (File System):** The system will read input data files (CSV, Excel), configuration files (YAML, TOML), and Quarto template files (`.qmd`). It will write output report files (PDF, HTML, Word) and potentially intermediate data files for Quarto.
    

#### 3.4 Data Requirements

##### 3.4.1 Input Data

- **DR-IN-001 (Participant Data):**
    
    - Format: CSV, Excel (XLSX).
        
    - Content: Must include participant identifiers and their numerical results. May include participant result uncertainties.
        
    - Structure: Tabular. Key data columns (e.g., for participant ID, result value, participant uncertainty) shall be mappable to user-defined column names specified in the configuration file.
        
- **DR-IN-002 (Standard Deviation for Proficiency Assessment `σ_pt`):**
    
    - Format: Numerical value, potentially provided via CLI argument or configuration.
        
- **DR-IN-003 (Reference Material Data - if CRM method is used):**
    
    - Format: Values for certified value and its uncertainty, potentially from configuration or dedicated input.
        

##### 3.4.2 Output Data

- **DR-OUT-001 (Reports):**
    
    - Format: PDF, HTML, Word (as generated by Quarto).
        
    - Content: As defined in FR-RP-009.
        
- **DR-OUT-002 (Console Output):**
    
    - Format: Formatted text via `rich`.
        
    - Content: Summaries of calculations, progress messages, error messages.
        
- **DR-OUT-003 (Intermediate Data for Quarto - optional):**
    
    - Format: JSON, CSV.
        
    - Content: Calculated values, prepared datasets to be consumed by `.qmd` files.
        

##### 3.4.3 Configuration Data

- **DR-CFG-001 (User Configuration File):**
    
    - Format: YAML or TOML.
        
    - Content: As defined in FR-CM-003.
        
- **DR-CFG-002 (Quarto Template Files):**
    
    - Format: `.qmd` (Quarto Markdown).
        
    - Content: Structure and content layout for reports, including placeholders or code chunks for dynamic data.
        

This SRS provides a detailed foundation for the development of the PT-CLI application.