"""Configuration Management Module

This module handles loading, validating, and providing access to application
configuration settings. It supports YAML and TOML formats with Pydantic validation.
"""

from pathlib import Path
from typing import Optional, Literal, Dict, Any
import yaml
import toml
from pydantic import BaseModel, Field, validator


class InputDataConfig(BaseModel):
    """Configuration for input data column mappings."""
    participant_id_col: str = Field(default="ParticipantID", description="Column name for participant IDs")
    result_col: str = Field(default="Value", description="Column name for participant results")
    uncertainty_col: Optional[str] = Field(default="Uncertainty", description="Column name for uncertainties")


class AlgorithmAParams(BaseModel):
    """Parameters for Algorithm A."""
    tolerance: float = Field(default=1.0e-5, gt=0, description="Convergence tolerance")
    max_iterations: int = Field(default=50, gt=0, description="Maximum iterations")


class CRMParams(BaseModel):
    """Parameters for CRM method."""
    certified_value: Optional[float] = Field(default=None, description="Certified reference value")
    uncertainty: Optional[float] = Field(default=None, ge=0, description="Certified uncertainty")


class FormulationParams(BaseModel):
    """Parameters for Formulation method."""
    known_value: Optional[float] = Field(default=None, description="Known formulation value")
    uncertainty: Optional[float] = Field(default=None, ge=0, description="Known uncertainty")


class ExpertConsensusParams(BaseModel):
    """Parameters for Expert Consensus method."""
    consensus_value: Optional[float] = Field(default=None, description="Expert consensus value")
    uncertainty: Optional[float] = Field(default=None, ge=0, description="Consensus uncertainty")


class OutlierHandlingConfig(BaseModel):
    """Configuration for outlier handling."""
    method: Literal["RobustAlgorithmA", "Grubbs", "DixonsQ", "None"] = Field(
        default="RobustAlgorithmA", 
        description="Outlier detection method"
    )


class CalculationConfig(BaseModel):
    """Configuration for calculation parameters."""
    method: Literal["AlgorithmA", "CRM", "Formulation", "Expert"] = Field(
        default="AlgorithmA", 
        description="Calculation method"
    )
    sigma_pt: float = Field(default=0.15, gt=0, description="Standard deviation for proficiency assessment")
    algorithm_a: AlgorithmAParams = Field(default_factory=AlgorithmAParams)
    crm: CRMParams = Field(default_factory=CRMParams)
    formulation: FormulationParams = Field(default_factory=FormulationParams)
    expert_consensus: ExpertConsensusParams = Field(default_factory=ExpertConsensusParams)
    outlier_handling: OutlierHandlingConfig = Field(default_factory=OutlierHandlingConfig)


class PlotConfig(BaseModel):
    """Configuration for plot generation."""
    generate_histogram: bool = Field(default=True, description="Generate histogram plots")
    histogram_bins: int = Field(default=30, gt=0, description="Number of histogram bins")


class ReportingConfig(BaseModel):
    """Configuration for reporting."""
    default_format: Literal["pdf", "html", "docx"] = Field(
        default="pdf", 
        description="Default report format"
    )
    custom_template: Optional[Path] = Field(default=None, description="Path to custom Quarto template")
    plots: PlotConfig = Field(default_factory=PlotConfig)


class MainConfig(BaseModel):
    """Main configuration model."""
    input_data: InputDataConfig = Field(default_factory=InputDataConfig)
    calculation: CalculationConfig = Field(default_factory=CalculationConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


def _load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load YAML configuration file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"Invalid YAML in config file {file_path}: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Failed to read config file {file_path}: {e}")


def _load_toml_file(file_path: Path) -> Dict[str, Any]:
    """Load TOML configuration file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return toml.load(file)
    except toml.TomlDecodeError as e:
        raise ConfigValidationError(f"Invalid TOML in config file {file_path}: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Failed to read config file {file_path}: {e}")


def load_config(config_path: Optional[Path] = None) -> MainConfig:
    """Load and validate configuration.
    
    Args:
        config_path: Optional path to configuration file. If None, uses defaults.
        
    Returns:
        Validated configuration object.
        
    Raises:
        ConfigValidationError: If configuration loading or validation fails.
    """
    config_data = {}
    
    if config_path is not None:
        if not config_path.exists():
            raise ConfigValidationError(f"Configuration file not found: {config_path}")
        
        # Detect file type by extension
        suffix = config_path.suffix.lower()
        if suffix in ['.yaml', '.yml']:
            config_data = _load_yaml_file(config_path)
        elif suffix == '.toml':
            config_data = _load_toml_file(config_path)
        else:
            raise ConfigValidationError(
                f"Unsupported config file format: {suffix}. "
                "Supported formats: .yaml, .yml, .toml"
            )
    
    # Parse and validate with Pydantic
    try:
        return MainConfig(**config_data)
    except Exception as e:
        raise ConfigValidationError(f"Configuration validation failed: {e}")