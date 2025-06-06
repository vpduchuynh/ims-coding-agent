"""Data Input/Output and Validation Module

This module handles reading input data from CSV and Excel files,
validating data structure and types, and preparing data for calculations.
"""

from pathlib import Path
from typing import List, Optional, Union, Any
import polars as pl
import numpy as np
from pydantic import BaseModel, Field, field_validator

from .config import MainConfig


class ParticipantDataRow(BaseModel):
    """Pydantic model for validating a single row of participant data."""
    participant_id: str = Field(..., description="Participant identifier")
    result: float = Field(..., description="Participant result value")
    uncertainty: Optional[float] = Field(default=None, ge=0, description="Participant uncertainty")

    @field_validator('result')
    @classmethod
    def result_must_be_finite(cls, v):
        """Validate that result is a finite number."""
        if not np.isfinite(v):
            raise ValueError("Result must be a finite number")
        return v

    @field_validator('uncertainty')
    @classmethod
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


def _handle_polars_exceptions(func):
    """Decorator to handle polars-specific exceptions consistently."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pl.ComputeError as e:
            raise DataValidationError(f"Data computation error: {e}")
        except pl.SchemaError as e:
            raise DataValidationError(f"Data schema error: {e}")
        except Exception as e:
            # Re-raise our custom exceptions as-is
            if isinstance(e, (DataValidationError, MissingColumnError, InvalidDataTypeError)):
                raise
            raise DataValidationError(f"Unexpected error: {e}")
    return wrapper


@_handle_polars_exceptions
def _read_csv(file_path: Path) -> pl.DataFrame:
    """Read CSV file into DataFrame with memory efficiency for large files.
    
    Args:
        file_path: Path to CSV file.
        
    Returns:
        DataFrame with loaded data.
        
    Raises:
        DataValidationError: If file cannot be read.
    """
    try:
        # Check file size for memory efficiency optimization
        file_size = file_path.stat().st_size
        
        # For large files (>10MB), use lazy evaluation where beneficial
        if file_size > 10 * 1024 * 1024:  # 10MB threshold
            # Use scan_csv for lazy loading, then collect after basic validation
            lazy_df = pl.scan_csv(file_path)
            
            # Basic schema validation can be done lazily
            try:
                # Collect just the schema first to validate structure
                sample_df = lazy_df.head(100).collect()
                return lazy_df.collect()  # If schema is valid, collect full data
            except Exception as e:
                raise DataValidationError(f"Failed to validate CSV schema: {e}")
        else:
            # For smaller files, use direct reading
            return pl.read_csv(file_path)
            
    except Exception as e:
        raise DataValidationError(f"Failed to read CSV file {file_path}: {e}")


@_handle_polars_exceptions
def _read_excel(file_path: Path) -> pl.DataFrame:
    """Read Excel file into DataFrame with robust engine handling.
    
    Args:
        file_path: Path to Excel file.
        
    Returns:
        DataFrame with loaded data.
        
    Raises:
        DataValidationError: If file cannot be read.
    """
    # Try multiple engines for better compatibility (enhancement from review feedback)
    engines = ['calamine', 'openpyxl']
    last_error = None
    
    for engine in engines:
        try:
            return pl.read_excel(file_path, engine=engine)
        except Exception as e:
            last_error = e
            continue
    
    # If all engines failed, raise error with details
    raise DataValidationError(
        f"Failed to read Excel file {file_path} with any available engine. "
        f"Tried engines: {engines}. Last error: {last_error}"
    )


def _check_required_columns(df: pl.DataFrame, config: MainConfig) -> None:
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


@_handle_polars_exceptions
def _validate_data_types(df: pl.DataFrame, config: MainConfig) -> pl.DataFrame:
    """Validate and convert data types for relevant columns.
    
    Args:
        df: Input DataFrame to validate.
        config: Configuration object with column mappings.
        
    Returns:
        DataFrame with validated and converted types.
        
    Raises:
        InvalidDataTypeError: If data conversion fails.
    """
    # Convert result column to numeric using polars cast with strict=False
    result_col = config.input_data.result_col
    df = df.with_columns(
        pl.col(result_col).cast(pl.Float64, strict=False)
    )
    
    # Enhanced vectorized validation for result column
    validation_results = df.select([
        pl.col(result_col).is_null().sum().alias('null_count'),
        pl.col(result_col).is_infinite().sum().alias('infinite_count'),
        pl.col(result_col).is_nan().sum().alias('nan_count')
    ]).to_dicts()[0]
    
    # Check for null values in results
    if validation_results['null_count'] > 0:
        raise InvalidDataTypeError(
            f"Found {validation_results['null_count']} null or non-numeric values in {result_col} column"
        )
    
    # Check for infinite values in results (enhancement from review feedback)
    if validation_results['infinite_count'] > 0:
        raise InvalidDataTypeError(
            f"Found {validation_results['infinite_count']} infinite values in {result_col} column. "
            "Result values must be finite numbers."
        )
    
    # Check for NaN values in results (explicit check)
    if validation_results['nan_count'] > 0:
        raise InvalidDataTypeError(
            f"Found {validation_results['nan_count']} NaN values in {result_col} column"
        )
    
    # Convert uncertainty column to numeric if present
    uncertainty_col = config.input_data.uncertainty_col
    if uncertainty_col and uncertainty_col in df.columns:
        df = df.with_columns(
            pl.col(uncertainty_col).cast(pl.Float64, strict=False)
        )
        
        # Enhanced vectorized validation for uncertainty column
        uncertainty_validation = df.select([
            (pl.col(uncertainty_col) < 0).sum().alias('negative_count'),
            pl.col(uncertainty_col).is_infinite().sum().alias('infinite_count')
        ]).to_dicts()[0]
        
        # Check for negative uncertainties
        if uncertainty_validation['negative_count'] > 0:
            raise InvalidDataTypeError(
                f"Found {uncertainty_validation['negative_count']} negative values in {uncertainty_col} column. "
                "Uncertainty values must be non-negative."
            )
        
        # Check for infinite uncertainties
        if uncertainty_validation['infinite_count'] > 0:
            raise InvalidDataTypeError(
                f"Found {uncertainty_validation['infinite_count']} infinite values in {uncertainty_col} column. "
                "Uncertainty values must be finite numbers."
            )
    
    return df


def _validate_with_pydantic(df: pl.DataFrame, config: MainConfig) -> None:
    """Perform row-level validation using Pydantic models.
    
    Uses vectorized operations for initial screening, then detailed row-level 
    validation for problematic rows to provide specific error messages.
    
    Args:
        df: Input DataFrame to validate.
        config: Configuration object with column mappings.
        
    Raises:
        DataValidationError: If row validation fails.
    """
    participant_id_col = config.input_data.participant_id_col
    result_col = config.input_data.result_col
    uncertainty_col = config.input_data.uncertainty_col
    
    # Vectorized pre-screening for performance (enhancement from review feedback)
    validation_conditions = [
        pl.col(result_col).is_null(),
        pl.col(result_col).is_infinite(),
        pl.col(result_col).is_nan()
    ]
    
    if uncertainty_col and uncertainty_col in df.columns:
        validation_conditions.extend([
            (pl.col(uncertainty_col) < 0)
        ])
    
    # Find rows with any validation issues using vectorized operations
    problematic_mask = df.select([
        pl.any_horizontal(validation_conditions).alias('has_issues')
    ]).get_column('has_issues')
    
    problematic_rows = df.filter(problematic_mask)
    
    # If we have problematic rows, use detailed validation to get specific errors
    if problematic_rows.height > 0:
        validation_errors = []
        
        # Only validate problematic rows for efficiency
        for i, row_data_dict in enumerate(problematic_rows.to_dicts()):
            try:
                # Get original row index for error reporting
                original_index = df.select([
                    pl.int_range(pl.len()).alias('index')
                ]).filter(problematic_mask).get_column('index').to_list()[i]
                
                # Remap dict keys for Pydantic model
                pydantic_data = {
                    'participant_id': str(row_data_dict[participant_id_col]),
                    'result': row_data_dict[result_col]
                }
                
                # Add uncertainty if column exists and value is not None
                if uncertainty_col and uncertainty_col in row_data_dict:
                    uncertainty_value = row_data_dict[uncertainty_col]
                    if uncertainty_value is not None:
                        pydantic_data['uncertainty'] = uncertainty_value
                
                # Validate with Pydantic
                ParticipantDataRow(**pydantic_data)
                
            except Exception as e:
                validation_errors.append(f"Row {original_index + 1}: {e}")
        
        if validation_errors:
            error_message = "Data validation errors:\n" + "\n".join(validation_errors[:10])
            if len(validation_errors) > 10:
                error_message += f"\n... and {len(validation_errors) - 10} more errors"
            raise DataValidationError(error_message)
    
    # If no problematic rows found via vectorized screening, do a lighter validation
    # Sample validation on a subset for performance on large datasets
    total_rows = df.height
    if total_rows > 1000:
        # For large datasets, validate a sample + first/last rows
        sample_size = min(100, total_rows // 10)
        sample_indices = list(range(0, min(10, total_rows))) + \
                        list(range(max(0, total_rows - 10), total_rows)) + \
                        list(range(total_rows // 4, total_rows // 4 + sample_size))
        sample_indices = sorted(set(sample_indices))
        sample_df = df.select([pl.all()]).slice(0, total_rows).gather(sample_indices)
        rows_to_validate = sample_df.to_dicts()
    else:
        # For smaller datasets, validate all rows
        rows_to_validate = df.to_dicts()
    
    validation_errors = []
    
    for i, row_data_dict in enumerate(rows_to_validate):
        try:
            # Remap dict keys for Pydantic model
            pydantic_data = {
                'participant_id': str(row_data_dict[participant_id_col]),
                'result': row_data_dict[result_col]
            }
            
            # Add uncertainty if column exists and value is not None
            if uncertainty_col and uncertainty_col in row_data_dict:
                uncertainty_value = row_data_dict[uncertainty_col]
                if uncertainty_value is not None:
                    pydantic_data['uncertainty'] = uncertainty_value
            
            # Validate with Pydantic
            ParticipantDataRow(**pydantic_data)
            
        except Exception as e:
            validation_errors.append(f"Row {i + 1}: {e}")
    
    if validation_errors:
        error_message = "Data validation errors:\n" + "\n".join(validation_errors[:10])
        if len(validation_errors) > 10:
            error_message += f"\n... and {len(validation_errors) - 10} more errors"
        raise DataValidationError(error_message)


def load_and_validate_data(file_path: Path, config: MainConfig) -> pl.DataFrame:
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
    if df.height == 0:
        raise DataValidationError("Input file contains no data")
    
    # Validate column presence
    _check_required_columns(df, config)
    
    # Validate and convert data types
    df = _validate_data_types(df, config)
    
    # Perform row-level Pydantic validation
    _validate_with_pydantic(df, config)
    
    return df


def prepare_calculation_data(df: pl.DataFrame, config: MainConfig) -> dict:
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
        'participant_ids': df[participant_id_col].to_numpy(),
        'results': df[result_col].to_numpy()
    }
    
    # Add uncertainties if available
    if uncertainty_col and uncertainty_col in df.columns:
        # Get uncertainties as numpy array
        uncertainties = df[uncertainty_col].to_numpy()
        calculation_data['uncertainties'] = uncertainties
    
    return calculation_data