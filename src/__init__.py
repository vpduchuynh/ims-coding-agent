"""PT-CLI: Proficiency Testing Command Line Interface

A Python application for statistical analysis and reporting in proficiency testing.
"""

__version__ = "0.1.0"
__author__ = "PT-CLI Development Team"

from .config import MainConfig, load_config, ConfigValidationError
from .data_io import load_and_validate_data, DataValidationError, MissingColumnError, InvalidDataTypeError
from .reporting import generate_report, aggregate_report_data, ReportingError, QuartoNotFoundError
from .main import app

__all__ = [
    "MainConfig",
    "load_config", 
    "ConfigValidationError",
    "load_and_validate_data",
    "DataValidationError",
    "MissingColumnError", 
    "InvalidDataTypeError",
    "generate_report",
    "aggregate_report_data",
    "ReportingError",
    "QuartoNotFoundError",
    "app"
]