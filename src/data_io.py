"""Data Input/Output and Validation Module

This module handles reading input data from CSV and Excel files,
validating data structure and types, and preparing data for calculations.
"""

from pathlib import Path
from typing import List, Optional, Union, Any
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, validator

from .config import MainConfig


class ParticipantDataRow(BaseModel):
    """Pydantic model for validating a single row of participant data."""
    participant_id: str = Field(..., description="Participant identifier")
    result: float = Field(..., description="Participant result value")
    uncertainty: Optional[float] = Field(default=None, ge=0, description="Participant uncertainty")

    @validator('result')
    def result_must_be_finite(cls, v):
        """Validate that result is a finite number."""
        if not np.isfinite(v):
            raise ValueError("Result must be a finite number")
        return v

    @validator('uncertainty')
    def uncertainty_must_be_positive_or_none(cls, v):
        """Validate that uncertainty is positive if provided."""
        if v is not None and v < 0:
            raise ValueError("Uncertainty must be non-negative")
        return v


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class MissingColumnError(DataValidationError):
    """Raised when required columns are missing from input data."""
    pass


class InvalidDataTypeError(DataValidationError):
    """Raised when data contains invalid types."""
    pass


def _read_csv(file_path: Path) -> pd.DataFrame:
    """Read CSV file into DataFrame.
    
    Args:
        file_path: Path to CSV file.
        
    Returns:
        DataFrame with loaded data.
        
    Raises:
        DataValidationError: If file cannot be read.
    """
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        raise DataValidationError(f"Failed to read CSV file {file_path}: {e}")


def _read_excel(file_path: Path) -> pd.DataFrame:
    """Read Excel file into DataFrame.
    
    Args:
        file_path: Path to Excel file.
        
    Returns:
        DataFrame with loaded data.
        
    Raises:
        DataValidationError: If file cannot be read.
    """
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        raise DataValidationError(f"Failed to read Excel file {file_path}: {e}")


def _check_required_columns(df: pd.DataFrame, config: MainConfig) -> None:
    """Check that required columns exist in the DataFrame.
    
    Args:
        df: Input DataFrame to validate.
        config: Configuration object with column mappings.
        
    Raises:
        MissingColumnError: If required columns are missing.
    """
    required_columns = [
        config.input_data.participant_id_col,
        config.input_data.result_col
    ]
    
    # Add uncertainty column if specified
    if config.input_data.uncertainty_col:
        required_columns.append(config.input_data.uncertainty_col)
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise MissingColumnError(
            f"Missing required columns: {missing_columns}. "
            f"Available columns: {list(df.columns)}"
        )


def _validate_data_types(df: pd.DataFrame, config: MainConfig) -> pd.DataFrame:
    """Validate and convert data types for relevant columns.
    
    Args:
        df: Input DataFrame to validate.
        config: Configuration object with column mappings.
        
    Returns:
        DataFrame with validated and converted types.
        
    Raises:
        InvalidDataTypeError: If data conversion fails.
    """
    df = df.copy()
    
    # Convert result column to numeric
    result_col = config.input_data.result_col
    try:
        df[result_col] = pd.to_numeric(df[result_col], errors='coerce')
    except Exception as e:
        raise InvalidDataTypeError(f"Failed to convert {result_col} to numeric: {e}")
    
    # Check for NaN values in results
    nan_count = df[result_col].isna().sum()
    if nan_count > 0:
        raise InvalidDataTypeError(
            f"Found {nan_count} non-numeric or missing values in {result_col} column"
        )
    
    # Convert uncertainty column to numeric if present
    uncertainty_col = config.input_data.uncertainty_col
    if uncertainty_col and uncertainty_col in df.columns:
        try:
            df[uncertainty_col] = pd.to_numeric(df[uncertainty_col], errors='coerce')
        except Exception as e:
            raise InvalidDataTypeError(f"Failed to convert {uncertainty_col} to numeric: {e}")
        
        # Check for negative uncertainties
        negative_uncertainties = (df[uncertainty_col] < 0).sum()
        if negative_uncertainties > 0:
            raise InvalidDataTypeError(
                f"Found {negative_uncertainties} negative values in {uncertainty_col} column"
            )
    
    return df


def _validate_with_pydantic(df: pd.DataFrame, config: MainConfig) -> None:
    """Perform row-level validation using Pydantic models.
    
    Args:
        df: Input DataFrame to validate.
        config: Configuration object with column mappings.
        
    Raises:
        DataValidationError: If row validation fails.
    """
    participant_id_col = config.input_data.participant_id_col
    result_col = config.input_data.result_col
    uncertainty_col = config.input_data.uncertainty_col
    
    validation_errors = []
    
    for idx, row in df.iterrows():
        try:
            row_data = {
                'participant_id': str(row[participant_id_col]),
                'result': float(row[result_col])
            }
            
            # Add uncertainty if column exists and value is not NaN
            if uncertainty_col and uncertainty_col in df.columns:
                uncertainty_value = row[uncertainty_col]
                if pd.notna(uncertainty_value):
                    row_data['uncertainty'] = float(uncertainty_value)
            
            # Validate with Pydantic
            ParticipantDataRow(**row_data)
            
        except Exception as e:
            validation_errors.append(f"Row {idx + 1}: {e}")
    
    if validation_errors:
        error_message = "Data validation errors:\n" + "\n".join(validation_errors[:10])
        if len(validation_errors) > 10:
            error_message += f"\n... and {len(validation_errors) - 10} more errors"
        raise DataValidationError(error_message)


def load_and_validate_data(file_path: Path, config: MainConfig) -> pd.DataFrame:
    """Load and validate input data file.
    
    Args:
        file_path: Path to input data file (CSV or Excel).
        config: Configuration object with validation settings.
        
    Returns:
        Validated DataFrame ready for calculations.
        
    Raises:
        DataValidationError: If file loading or validation fails.
        MissingColumnError: If required columns are missing.
        InvalidDataTypeError: If data contains invalid types.
    """
    if not file_path.exists():
        raise DataValidationError(f"Input file not found: {file_path}")
    
    # Determine file type and read data
    suffix = file_path.suffix.lower()
    if suffix == '.csv':
        df = _read_csv(file_path)
    elif suffix in ['.xlsx', '.xls']:
        df = _read_excel(file_path)
    else:
        raise DataValidationError(
            f"Unsupported file format: {suffix}. "
            "Supported formats: .csv, .xlsx, .xls"
        )
    
    # Check if DataFrame is empty
    if df.empty:
        raise DataValidationError("Input file contains no data")
    
    # Validate column presence
    _check_required_columns(df, config)
    
    # Validate and convert data types
    df = _validate_data_types(df, config)
    
    # Perform row-level Pydantic validation
    _validate_with_pydantic(df, config)
    
    return df


def prepare_calculation_data(df: pd.DataFrame, config: MainConfig) -> dict:
    """Prepare validated data for calculation engine.
    
    Args:
        df: Validated DataFrame.
        config: Configuration object with column mappings.
        
    Returns:
        Dictionary with arrays ready for calculation engine.
    """
    result_col = config.input_data.result_col
    uncertainty_col = config.input_data.uncertainty_col
    participant_id_col = config.input_data.participant_id_col
    
    calculation_data = {
        'participant_ids': df[participant_id_col].values,
        'results': df[result_col].values
    }
    
    # Add uncertainties if available
    if uncertainty_col and uncertainty_col in df.columns:
        # Fill NaN uncertainties with None or a default value
        uncertainties = df[uncertainty_col].values
        calculation_data['uncertainties'] = uncertainties
    
    return calculation_data