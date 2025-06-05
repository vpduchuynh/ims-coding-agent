## 9. Deployment and Installation Plan

This section outlines the plan for packaging the PT-CLI application, including its Rust calculation engine, and provides a guide for end-user installation. The goal is to provide a straightforward installation process for users on common operating systems (Windows, macOS, Linux), addressing NFR-PO-001 and NFR-PO-002, while clearly stating dependencies like Quarto (NFR-PO-003).

### 9.1 Packaging Strategy (Python + Rust extension via Maturin) (NFR-MA-004)

The PT-CLI application, consisting of the Python application layer and the Rust calculation engine, will be packaged as a standard Python wheel (`.whl`) distribution. This allows installation using `pip`, the standard Python package installer.

**Tooling:**
`maturin` will be the primary tool used for building and packaging. Maturin is specifically designed for building Python packages that include Rust code compiled via PyO3. It simplifies the process of compiling the Rust extension and bundling it correctly within the Python wheel for different target platforms and Python versions.

**Build Process:**

1.  **Project Structure:** The project will be structured to be compatible with Maturin. Typically, this involves having the Python code (`main.py`, `config.py`, etc.) in a source directory (e.g., `src/pt_cli/`) and the Rust crate (`Cargo.toml`, `src/lib.rs`, etc.) at the project root or in a dedicated subdirectory.
2.  **`pyproject.toml` Configuration:** A `pyproject.toml` file will be configured at the project root. This file defines project metadata (name, version, author, description), Python dependencies (Typer, Pandas, Pydantic, etc.), and Maturin build settings.
    ```toml
    # Example pyproject.toml snippet
    [build-system]
    requires = ["maturin>=1.0,<2.0"]
    build-backend = "maturin"

    [project]
    name = "pt-cli"
    version = "0.1.0"
    requires-python = ">=3.8"
    description = "Command Line Interface for Proficiency Testing Data Analysis (ISO 13528)"
    authors = [{name = "Your Name/Org", email = "your@email.com"}]
    dependencies = [
        "typer[all]>=0.9.0",
        "pandas>=1.5.0",
        "pydantic>=1.10.0",
        "pyyaml>=6.0",
        "toml>=0.10.0",
        "rich>=13.0.0",
        "matplotlib>=3.6.0",
        "seaborn>=0.12.0",
        "numpy>=1.21.0"
    ]
    # Add classifiers, license, readme, etc.

    [tool.maturin]
    features = ["pyo3/extension-module"]
    # Specify path to Cargo.toml if not at root
    # manifest-path = "path/to/rust/Cargo.toml"
    ```
3.  **Compilation and Packaging:** Running `maturin build --release` will compile the Rust code into a shared library (`.so` on Linux, `.dylib` on macOS, `.pyd` on Windows) and package it along with the Python code and metadata into a platform-specific wheel file in the `target/wheels/` directory.
4.  **Cross-Platform Builds (Optional):** For distributing pre-compiled wheels for multiple platforms (to avoid users needing a Rust toolchain), CI/CD pipelines (like GitHub Actions with `maturin-action`) can be set up to build wheels for Windows, macOS (x86_64, arm64), and Linux (e.g., `manylinux` wheels).
5.  **Source Distribution:** A source distribution (`sdist`) can also be generated (`maturin sdist`), allowing users with a Rust toolchain to compile the extension themselves during installation.

**Distribution:**
The packaged wheels (and potentially the sdist) can be uploaded to the Python Package Index (PyPI) for easy installation via `pip install pt-cli`, or distributed directly.

### 9.2 Installation Guide (Prerequisites: Python, Quarto, Package)

This guide outlines the steps for end-users to install and run the PT-CLI application.

**Prerequisites:**

Before installing PT-CLI, users must ensure they have the following software installed on their system (Windows, macOS, or Linux):

1.  **Python:** A compatible version of Python (>= 3.8, as specified in `pyproject.toml`). Users can download Python from [python.org](https://python.org/) or install it using system package managers (like `apt` on Debian/Ubuntu, `brew` on macOS). It is highly recommended to use a virtual environment (`venv` or `conda`) to install PT-CLI and its dependencies.
    *   Verify installation by running `python --version` or `python3 --version` in the terminal.
2.  **Quarto CLI:** The external Quarto command-line tool is required for report generation (FR-RP-001, Constraint 2.4). Users must download and install Quarto separately from the official Quarto website: [https://quarto.org/docs/get-started/](https://quarto.org/docs/get-started/).
    *   Verify installation by running `quarto --version` in the terminal. Ensure the Quarto executable is added to the system's PATH environment variable during installation.
3.  **(Optional) Rust Toolchain:** If installing from a source distribution (`sdist`) or if pre-compiled wheels are not available for the user's specific platform/Python version, the Rust toolchain (including `rustc` and `cargo`) will be required to compile the Rust calculation engine during installation. Instructions are available at [https://rustup.rs/](https://rustup.rs/). If pre-compiled wheels are provided, this is *not* necessary.

**Installation Steps:**

1.  **(Recommended) Create a Virtual Environment:** Open a terminal or command prompt and create/activate a Python virtual environment:
    ```bash
    # Create a virtual environment named 'ptcli-env'
    python -m venv ptcli-env 
    # Activate on Linux/macOS
    source ptcli-env/bin/activate 
    # Activate on Windows (Command Prompt)
    ptcli-env\Scripts\activate.bat
    # Activate on Windows (PowerShell)
    .\ptcli-env\Scripts\Activate.ps1
    ```
2.  **Install PT-CLI using pip:**
    *   **From PyPI (if published):**
        ```bash
        pip install pt-cli
        ```
    *   **From a local wheel file:**
        ```bash
        pip install /path/to/pt_cli-<version>-<platform_tag>.whl
        ```
    *   **From source (requires Rust toolchain if no wheel matches):**
        ```bash
        pip install /path/to/pt-cli-source-directory/
        # OR
        pip install pt-cli-<version>.tar.gz 
        ```
    `pip` will automatically handle downloading and installing the Python dependencies listed in `pyproject.toml`.

3.  **Verify Installation:** After installation, run the following command to check if the CLI is accessible and display the help message:
    ```bash
    pt-cli --help
    ```
    If this command executes successfully and shows the main help text, the installation is complete.

**Troubleshooting:**

*   If `pt-cli` command is not found, ensure the virtual environment is activated or that the Python installation's `Scripts` (Windows) or `bin` (Linux/macOS) directory is in the system PATH.
*   If installation fails during compilation (when installing from source), ensure the Rust toolchain is correctly installed.
*   If report generation fails, verify that Quarto is installed correctly and accessible via the `quarto` command in the terminal (`quarto --version`).

This deployment and installation plan provides a standard and relatively simple path for users to obtain and set up the PT-CLI application.
