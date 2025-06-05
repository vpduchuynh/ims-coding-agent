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
            if method:
                config.calculation.method = method
            if sigma_pt:
                config.calculation.sigma_pt = sigma_pt
            
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
            
            # TODO: Call Rust calculation engine here
            # For now, create mock results
            progress.update(task, description="Performing calculations...")
            mock_results = {
                'x_pt': 10.0,  # Mock assigned value
                'u_x_pt': 0.5,  # Mock uncertainty
                'method_used': config.calculation.method,
                'sigma_pt_used': config.calculation.sigma_pt,
                'participant_scores': [0.1, -0.2, 0.5, -0.1] * (len(input_data) // 4 + 1)
            }
            mock_results['participant_scores'] = mock_results['participant_scores'][:len(input_data)]
            
            if verbose:
                console.print(f"✓ Calculations completed using {config.calculation.method}")
            
            # Save intermediate results if requested
            if results_json:
                progress.update(task, description="Saving intermediate results...")
                with open(results_json, 'w') as f:
                    json.dump(mock_results, f, indent=2)
                if verbose:
                    console.print(f"✓ Results saved to {results_json}")
            
            # Generate report
            progress.update(task, description="Generating report...")
            try:
                report_data = aggregate_report_data(input_data, config, mock_results)
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
            f"Method used: {config.calculation.method}",
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