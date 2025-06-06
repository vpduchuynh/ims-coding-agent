"""CLI Entry Point and Workflow Orchestration

This module serves as the main entry point for the PT-CLI application.
It uses Typer for CLI structure and Rich for user feedback.
"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich import print as rich_print
import json
import numpy as np

# Import Rust calculation engine
try:
    import pt_cli_rust
    RUST_ENGINE_AVAILABLE = True
except ImportError:
    RUST_ENGINE_AVAILABLE = False
    print("Warning: Rust calculation engine not available. Install with: pip install ./pt_cli_rust")

from .config import load_config, ConfigValidationError, MainConfig
from .data_io import (
    load_and_validate_data, prepare_calculation_data,
    DataValidationError, MissingColumnError, InvalidDataTypeError
)
from .reporting import (
    generate_report, aggregate_report_data,
    ReportingError, QuartoNotFoundError
)

# Create Typer app and Rich console
app = typer.Typer(help="Proficiency Testing CLI - Statistical analysis and reporting tool")
console = Console()


class PTCLIError(Exception):
    """Base exception for PT-CLI application errors."""
    pass


def display_error(message: str, error_type: str = "Error") -> None:
    """Display error message using Rich formatting.
    
    Args:
        message: Error message to display.
        error_type: Type of error (for styling).
    """
    console.print(Panel(
        f"[red]{message}[/red]",
        title=f"[red]{error_type}[/red]",
        border_style="red"
    ))


def display_success(message: str, title: str = "Success") -> None:
    """Display success message using Rich formatting.
    
    Args:
        message: Success message to display.
        title: Title for the panel.
    """
    console.print(Panel(
        f"[green]{message}[/green]",
        title=f"[green]{title}[/green]",
        border_style="green"
    ))


def display_info(message: str, title: str = "Info") -> None:
    """Display info message using Rich formatting.
    
    Args:
        message: Info message to display.
        title: Title for the panel.
    """
    console.print(Panel(
        f"[blue]{message}[/blue]",
        title=f"[blue]{title}[/blue]",
        border_style="blue"
    ))


def validate_method(method: str) -> None:
    """Validate calculation method option.
    
    Args:
        method: Method to validate.
        
    Raises:
        ValueError: If method is invalid.
    """
    valid_methods = ["AlgorithmA", "CRM", "Formulation", "Expert"]
    if method not in valid_methods:
        raise ValueError(
            f"Invalid calculation method: '{method}'. "
            f"Valid methods are: {', '.join(valid_methods)}"
        )


def validate_sigma_pt(sigma_pt: float) -> None:
    """Validate sigma_pt option.
    
    Args:
        sigma_pt: Sigma PT value to validate.
        
    Raises:
        ValueError: If sigma_pt is invalid.
    """
    if sigma_pt <= 0:
        raise ValueError(
            f"Invalid sigma_pt value: {sigma_pt}. "
            "Sigma PT must be positive (> 0)"
        )


def validate_results_json_path(results_json: Path) -> None:
    """Validate results JSON path option.
    
    Args:
        results_json: Path to validate.
        
    Raises:
        ValueError: If path is invalid or directory doesn't exist.
    """
    # Check if parent directory exists
    parent_dir = results_json.parent
    if not parent_dir.exists():
        raise ValueError(
            f"Directory does not exist: {parent_dir}. "
            "Please create the directory first or use an existing path."
        )
    
    # Check if parent directory is writable
    if not parent_dir.is_dir():
        raise ValueError(
            f"Parent path is not a directory: {parent_dir}"
        )
    
    # Check if file already exists and is writable
    if results_json.exists() and not results_json.is_file():
        raise ValueError(
            f"Path exists but is not a file: {results_json}"
        )


def perform_calculations(calculation_data: dict, config: MainConfig) -> dict:
    """Perform statistical calculations using the Rust engine.
    
    Args:
        calculation_data: Dictionary with participant data arrays
        config: Configuration object with calculation parameters
        
    Returns:
        Dictionary with calculation results
        
    Raises:
        RuntimeError: If Rust engine is not available or calculation fails
    """
    if not RUST_ENGINE_AVAILABLE:
        raise RuntimeError("Rust calculation engine is not available")
    
    method = config.calculation.method
    results_array = calculation_data['results']
    
    # Ensure results are numpy arrays with proper dtype
    results = np.asarray(results_array, dtype=np.float64)
    
    try:
        # Calculate assigned value based on method
        if method == "AlgorithmA":
            # Use robust Algorithm A
            tolerance = config.calculation.algorithm_a.tolerance
            max_iterations = config.calculation.algorithm_a.max_iterations
            
            x_pt, s_star, participants_used, iterations = pt_cli_rust.py_calculate_algorithm_a(
                results, tolerance, max_iterations
            )
            
            # Calculate uncertainty for consensus value
            u_x_pt = pt_cli_rust.py_calculate_uncertainty_consensus(s_star, participants_used)
            
            calc_details = {
                's_star': s_star,
                'participants_used': participants_used,
                'iterations': iterations,
                'tolerance': tolerance,
                'max_iterations': max_iterations
            }
            
        elif method == "CRM":
            # CRM-based calculation
            crm_value = config.calculation.crm.certified_value
            crm_uncertainty = config.calculation.crm.uncertainty
            
            if crm_value is None:
                raise ValueError("CRM certified value not specified in configuration")
            if crm_uncertainty is None:
                raise ValueError("CRM uncertainty not specified in configuration")
                
            x_pt = pt_cli_rust.py_calculate_from_crm(crm_value)
            u_x_pt = pt_cli_rust.py_calculate_uncertainty_crm(crm_uncertainty)
            
            calc_details = {
                'certified_value': crm_value,
                'uncertainty': crm_uncertainty
            }
            
        elif method == "Formulation":
            # Formulation-based calculation
            formulation_value = config.calculation.formulation.known_value
            formulation_uncertainty = config.calculation.formulation.uncertainty
            
            if formulation_value is None:
                raise ValueError("Formulation known value not specified in configuration")
            if formulation_uncertainty is None:
                raise ValueError("Formulation uncertainty not specified in configuration")
                
            x_pt = pt_cli_rust.py_calculate_from_formulation(formulation_value)
            u_x_pt = pt_cli_rust.py_calculate_uncertainty_formulation(formulation_uncertainty)
            
            calc_details = {
                'known_value': formulation_value,
                'uncertainty': formulation_uncertainty
            }
            
        elif method == "Expert":
            # Expert consensus calculation
            expert_value = config.calculation.expert_consensus.consensus_value
            expert_uncertainty = config.calculation.expert_consensus.uncertainty
            
            if expert_value is None:
                raise ValueError("Expert consensus value not specified in configuration")
            if expert_uncertainty is None:
                raise ValueError("Expert consensus uncertainty not specified in configuration")
                
            x_pt = pt_cli_rust.py_calculate_from_expert_consensus(expert_value)
            u_x_pt = pt_cli_rust.py_calculate_uncertainty_expert(expert_uncertainty)
            
            calc_details = {
                'consensus_value': expert_value,
                'uncertainty': expert_uncertainty
            }
            
        else:
            raise ValueError(f"Unknown calculation method: {method}")
        
        # Calculate performance scores
        sigma_pt = config.calculation.sigma_pt
        z_scores = pt_cli_rust.py_calculate_z_scores(results, x_pt, sigma_pt)
        
        # Calculate zeta-scores if participant uncertainties are available
        if 'uncertainties' in calculation_data and calculation_data['uncertainties'] is not None:
            uncertainties = np.asarray(calculation_data['uncertainties'], dtype=np.float64)
            # Check if uncertainties are valid (not NaN and not all zero)
            valid_uncertainties = ~np.isnan(uncertainties) & (uncertainties > 0)
            
            if np.any(valid_uncertainties):
                z_prime_scores = pt_cli_rust.py_calculate_z_prime_scores(
                    results, uncertainties, x_pt, u_x_pt
                )
            else:
                # Use simplified zeta-scores without participant uncertainties
                z_prime_scores = pt_cli_rust.py_calculate_z_prime_scores_no_uncertainties(
                    results, x_pt, u_x_pt
                )
        else:
            # Use simplified zeta-scores without participant uncertainties
            z_prime_scores = pt_cli_rust.py_calculate_z_prime_scores_no_uncertainties(
                results, x_pt, u_x_pt
            )
        
        # Compile results
        calculation_results = {
            'x_pt': float(x_pt),
            'u_x_pt': float(u_x_pt),
            'method_used': method,
            'sigma_pt_used': sigma_pt,
            'participant_scores': z_scores.tolist(),
            'participant_z_prime_scores': z_prime_scores.tolist(),
            'calculation_details': calc_details
        }
        
        return calculation_results
        
    except Exception as e:
        raise RuntimeError(f"Calculation failed: {str(e)}") from e


@app.command()
def calculate(
    input_file: Path = typer.Argument(
        ..., 
        exists=True, 
        file_okay=True, 
        readable=True,
        help="Path to the input data file (CSV or XLSX)"
    ),
    config_file: Optional[Path] = typer.Option(
        None, 
        "--config", 
        "-c",
        help="Path to configuration file (YAML or TOML). Uses defaults if not provided."
    ),
    output_report: Path = typer.Option(
        Path("report"),
        "--output-report",
        "-o",
        help="Base path and filename for the output report (extension added automatically)"
    ),
    output_format: str = typer.Option(
        "pdf",
        "--output-format",
        "-f",
        help="Format for the output report (pdf, html, docx)"
    ),
    method: Optional[str] = typer.Option(
        None,
        "--method",
        help="Override calculation method (AlgorithmA, CRM, Formulation, Expert)"
    ),
    sigma_pt: Optional[float] = typer.Option(
        None,
        "--sigma-pt",
        help="Override standard deviation for proficiency assessment"
    ),
    results_json: Optional[Path] = typer.Option(
        None,
        "--results-json",
        help="Optional path to save intermediate calculation results as JSON"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
) -> None:
    """Perform full proficiency testing analysis with report generation."""
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Load configuration
            task = progress.add_task("Loading configuration...", total=None)
            try:
                config = load_config(config_file)
                if verbose:
                    console.print("✓ Configuration loaded successfully")
            except ConfigValidationError as e:
                display_error(f"Configuration error: {e}", "Configuration Error")
                raise typer.Exit(1)
            
            # Override config values from CLI if provided
            if method is not None:
                try:
                    validate_method(method)
                    config.calculation.method = method
                except ValueError as e:
                    display_error(str(e), "Invalid Method")
                    raise typer.Exit(1)
            
            if sigma_pt is not None:
                try:
                    validate_sigma_pt(sigma_pt)
                    config.calculation.sigma_pt = sigma_pt
                except ValueError as e:
                    display_error(str(e), "Invalid Sigma PT")
                    raise typer.Exit(1)
            
            # Validate results JSON path if provided
            if results_json is not None:
                try:
                    validate_results_json_path(results_json)
                except ValueError as e:
                    display_error(str(e), "Invalid Results JSON Path")
                    raise typer.Exit(1)
            
            # Load and validate data
            progress.update(task, description="Loading and validating data...")
            try:
                input_data = load_and_validate_data(input_file, config)
                if verbose:
                    console.print(f"✓ Data loaded: {len(input_data)} participants")
            except (DataValidationError, MissingColumnError, InvalidDataTypeError) as e:
                display_error(f"Data validation error: {e}", "Data Validation Error")
                raise typer.Exit(1)
            
            # Prepare data for calculation
            progress.update(task, description="Preparing calculation data...")
            calculation_data = prepare_calculation_data(input_data, config)
            
            # Perform calculations using Rust engine
            progress.update(task, description="Performing calculations...")
            try:
                results = perform_calculations(calculation_data, config)
                if verbose:
                    console.print(f"✓ Calculations completed using {config.calculation.method}")
                    if 'calculation_details' in results:
                        details = results['calculation_details']
                        if config.calculation.method == "AlgorithmA":
                            console.print(f"  - Iterations: {details['iterations']}")
                            console.print(f"  - Participants used: {details['participants_used']}")
                            console.print(f"  - Robust std dev (s*): {details['s_star']:.6f}")
            except RuntimeError as e:
                display_error(f"Calculation error: {e}", "Calculation Error")
                raise typer.Exit(1)
            
            # Save intermediate results if requested
            if results_json:
                progress.update(task, description="Saving intermediate results...")
                try:
                    with open(results_json, 'w') as f:
                        json.dump(results, f, indent=2)
                    if verbose:
                        console.print(f"✓ Results saved to {results_json}")
                except (OSError, IOError, PermissionError) as e:
                    display_error(f"Failed to save results to {results_json}: {e}", "File Write Error")
                    raise typer.Exit(1)
            
            # Generate report
            progress.update(task, description="Generating report...")
            try:
                report_data = aggregate_report_data(input_data, config, results)
                generate_report(report_data, config, output_report, output_format)
                if verbose:
                    final_report_path = output_report.with_suffix(f".{output_format}")
                    console.print(f"✓ Report generated: {final_report_path}")
            except (ReportingError, QuartoNotFoundError) as e:
                display_error(f"Report generation error: {e}", "Reporting Error")
                raise typer.Exit(1)
        
        # Display success summary
        final_report_path = output_report.with_suffix(f".{output_format}")
        display_success(
            f"Analysis completed successfully!\\n"
            f"Report generated: {final_report_path}\\n"
            f"Participants analyzed: {len(input_data)}\\n"
            f"Method used: {config.calculation.method}\\n"
            f"Assigned value (x_pt): {results['x_pt']:.6f}\\n"
            f"Uncertainty u(x_pt): {results['u_x_pt']:.6f}",
            "Analysis Complete"
        )
        
    except typer.Exit:
        raise
    except Exception as e:
        display_error(f"Unexpected error: {e}", "Internal Error")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command("validate-data")
def validate_data(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        readable=True,
        help="Path to the input data file (CSV or XLSX) to validate"
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (YAML or TOML). Uses defaults if not provided."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
) -> None:
    """Validate input data file structure and content."""
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Load configuration
            task = progress.add_task("Loading configuration...", total=None)
            try:
                config = load_config(config_file)
                if verbose:
                    console.print("✓ Configuration loaded successfully")
            except ConfigValidationError as e:
                display_error(f"Configuration error: {e}", "Configuration Error")
                raise typer.Exit(1)
            
            # Validate data
            progress.update(task, description="Validating data...")
            try:
                input_data = load_and_validate_data(input_file, config)
            except (DataValidationError, MissingColumnError, InvalidDataTypeError) as e:
                display_error(f"Data validation failed: {e}", "Validation Failed")
                raise typer.Exit(1)
        
        # Display validation results
        table = Table(title="Data Validation Results")
        table.add_column("Attribute", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("File", str(input_file))
        table.add_row("Format", input_file.suffix.upper())
        table.add_row("Participants", str(len(input_data)))
        table.add_row("Participant ID Column", config.input_data.participant_id_col)
        table.add_row("Result Column", config.input_data.result_col)
        
        if config.input_data.uncertainty_col:
            has_uncertainty = config.input_data.uncertainty_col in input_data.columns
            table.add_row("Uncertainty Column", 
                         f"{config.input_data.uncertainty_col} ({'Found' if has_uncertainty else 'Not Found'})")
        
        console.print(table)
        display_success("Data validation passed successfully!", "Validation Complete")
        
    except typer.Exit:
        raise
    except Exception as e:
        display_error(f"Unexpected error: {e}", "Internal Error")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command("generate-report-only")
def generate_report_only(
    results_input: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        readable=True,
        help="Path to file containing pre-calculated results (JSON)"
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (YAML or TOML). Uses defaults if not provided."
    ),
    output_report: Path = typer.Option(
        Path("report"),
        "--output-report",
        "-o",
        help="Base path and filename for the output report (extension added automatically)"
    ),
    output_format: str = typer.Option(
        "pdf",
        "--output-format",
        "-f",
        help="Format for the output report (pdf, html, docx)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
) -> None:
    """Generate report from pre-calculated results."""
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Load configuration
            task = progress.add_task("Loading configuration...", total=None)
            try:
                config = load_config(config_file)
                if verbose:
                    console.print("✓ Configuration loaded successfully")
            except ConfigValidationError as e:
                display_error(f"Configuration error: {e}", "Configuration Error")
                raise typer.Exit(1)
            
            # Load pre-calculated results
            progress.update(task, description="Loading pre-calculated results...")
            try:
                with open(results_input, 'r') as f:
                    results_data = json.load(f)
                if verbose:
                    console.print("✓ Results data loaded successfully")
            except Exception as e:
                display_error(f"Failed to load results: {e}", "Data Loading Error")
                raise typer.Exit(1)
            
            # Generate report
            progress.update(task, description="Generating report...")
            try:
                generate_report(results_data, config, output_report, output_format)
                if verbose:
                    final_report_path = output_report.with_suffix(f".{output_format}")
                    console.print(f"✓ Report generated: {final_report_path}")
            except (ReportingError, QuartoNotFoundError) as e:
                display_error(f"Report generation error: {e}", "Reporting Error")
                raise typer.Exit(1)
        
        # Display success
        final_report_path = output_report.with_suffix(f".{output_format}")
        display_success(
            f"Report generated successfully!\\n"
            f"Output: {final_report_path}\\n"
            f"Format: {output_format.upper()}",
            "Report Generation Complete"
        )
        
    except typer.Exit:
        raise
    except Exception as e:
        display_error(f"Unexpected error: {e}", "Internal Error")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


def main() -> None:
    """Main entry point for the application."""
    app()


if __name__ == "__main__":
    main()