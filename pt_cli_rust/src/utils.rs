//! Common utilities and data structures for the PT-CLI Rust calculation engine.
//!
//! This module provides shared code used by other modules within the Rust engine,
//! including custom error types, mathematical constants, and helper functions.

use thiserror::Error;
use pyo3::prelude::*;

/// Custom error type for calculation failures in the Rust engine.
#[derive(Error, Debug)]
pub enum CalculationError {
    #[error("Algorithm A failed to converge after {max_iterations} iterations")]
    NonConvergence { max_iterations: usize },
    
    #[error("Invalid input: {message}")]
    InvalidInput { message: String },
    
    #[error("Division by zero encountered in calculation")]
    DivisionByZero,
    
    #[error("Insufficient data: need at least {required} data points, got {actual}")]
    InsufficientData { required: usize, actual: usize },
    
    #[error("Array dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    
    #[error("Mathematical error: {message}")]
    MathematicalError { message: String },
    
    #[error("Internal calculation error: {message}")]
    InternalError { message: String },
}

impl From<CalculationError> for PyErr {
    fn from(err: CalculationError) -> PyErr {
        match err {
            CalculationError::NonConvergence { .. } => {
                pyo3::exceptions::PyRuntimeError::new_err(err.to_string())
            }
            CalculationError::InvalidInput { .. } => {
                pyo3::exceptions::PyValueError::new_err(err.to_string())
            }
            CalculationError::DivisionByZero => {
                pyo3::exceptions::PyZeroDivisionError::new_err(err.to_string())
            }
            CalculationError::InsufficientData { .. } => {
                pyo3::exceptions::PyValueError::new_err(err.to_string())
            }
            CalculationError::DimensionMismatch { .. } => {
                pyo3::exceptions::PyValueError::new_err(err.to_string())
            }
            CalculationError::MathematicalError { .. } => {
                pyo3::exceptions::PyArithmeticError::new_err(err.to_string())
            }
            CalculationError::InternalError { .. } => {
                pyo3::exceptions::PyRuntimeError::new_err(err.to_string())
            }
        }
    }
}

/// Mathematical constants used in robust statistics calculations
pub mod constants {
    /// Scaling factor for converting MAD (Median Absolute Deviation) to standard deviation estimate
    /// This is approximately 1.4826 = 1/Φ^(-1)(3/4) where Φ^(-1) is the inverse normal CDF
    pub const MAD_TO_SIGMA: f64 = 1.4826;
    
    /// Default tolerance for iterative Algorithm A convergence
    pub const DEFAULT_TOLERANCE: f64 = 1e-6;
    
    /// Default maximum iterations for Algorithm A
    pub const DEFAULT_MAX_ITERATIONS: usize = 100;
    
    /// Minimum number of participants required for Algorithm A
    pub const MIN_PARTICIPANTS_ALGORITHM_A: usize = 5;
    
    /// Factor for calculating uncertainty from robust standard deviation
    /// u(x_pt) = 1.25 * s* / sqrt(p) for consensus values
    pub const UNCERTAINTY_FACTOR: f64 = 1.25;
}

/// Helper function to calculate the median of a slice of f64 values
/// Returns None if the slice is empty
pub fn median(data: &mut [f64]) -> Option<f64> {
    if data.is_empty() {
        return None;
    }
    
    data.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let len = data.len();
    
    if len % 2 == 0 {
        Some((data[len / 2 - 1] + data[len / 2]) / 2.0)
    } else {
        Some(data[len / 2])
    }
}

/// Helper function to calculate the Median Absolute Deviation (MAD)
/// Returns the MAD value, which needs to be scaled by MAD_TO_SIGMA to get a standard deviation estimate
pub fn mad(data: &[f64], median_value: f64) -> Result<f64, CalculationError> {
    if data.is_empty() {
        return Err(CalculationError::InsufficientData {
            required: 1,
            actual: 0,
        });
    }
    
    let mut abs_deviations: Vec<f64> = data.iter()
        .map(|&x| (x - median_value).abs())
        .collect();
    
    median(&mut abs_deviations).ok_or_else(|| CalculationError::InternalError {
        message: "Failed to calculate median of absolute deviations".to_string(),
    })
}

/// Huber's psi function for robust estimation
/// This implements the weighting function used in Algorithm A
pub fn huber_psi(x: f64, c: f64) -> f64 {
    if x.abs() <= c {
        x
    } else {
        c * x.signum()
    }
}

/// Validate that input arrays have compatible dimensions
pub fn validate_array_dimensions(
    arr1_len: usize,
    arr2_len: usize,
    name1: &str,
    name2: &str,
) -> Result<(), CalculationError> {
    if arr1_len != arr2_len {
        return Err(CalculationError::DimensionMismatch {
            expected: arr1_len,
            actual: arr2_len,
        });
    }
    Ok(())
}

/// Check if a value is valid (not NaN or infinite)
pub fn is_valid_float(value: f64) -> bool {
    value.is_finite()
}

/// Validate that all values in a slice are valid floats
pub fn validate_floats(data: &[f64], name: &str) -> Result<(), CalculationError> {
    for (i, &value) in data.iter().enumerate() {
        if !is_valid_float(value) {
            return Err(CalculationError::InvalidInput {
                message: format!("{} contains invalid value at index {}: {}", name, i, value),
            });
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;

    #[test]
    fn test_median_odd_length() {
        let mut data = vec![1.0, 3.0, 2.0];
        assert_eq!(median(&mut data), Some(2.0));
    }

    #[test]
    fn test_median_even_length() {
        let mut data = vec![1.0, 2.0, 3.0, 4.0];
        assert_eq!(median(&mut data), Some(2.5));
    }

    #[test]
    fn test_median_empty() {
        let mut data = vec![];
        assert_eq!(median(&mut data), None);
    }

    #[test]
    fn test_mad_calculation() {
        let data = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let median_val = 3.0;
        let mad_val = mad(&data, median_val).unwrap();
        assert_abs_diff_eq!(mad_val, 1.0, epsilon = 1e-10);
    }

    #[test]
    fn test_huber_psi() {
        let c = 1.5;
        assert_eq!(huber_psi(1.0, c), 1.0);
        assert_eq!(huber_psi(-1.0, c), -1.0);
        assert_eq!(huber_psi(2.0, c), 1.5);
        assert_eq!(huber_psi(-2.0, c), -1.5);
    }

    #[test]
    fn test_validate_floats() {
        assert!(validate_floats(&[1.0, 2.0, 3.0], "test").is_ok());
        assert!(validate_floats(&[1.0, f64::NAN, 3.0], "test").is_err());
        assert!(validate_floats(&[1.0, f64::INFINITY, 3.0], "test").is_err());
    }

    #[test]
    fn test_array_dimension_validation() {
        assert!(validate_array_dimensions(3, 3, "arr1", "arr2").is_ok());
        assert!(validate_array_dimensions(3, 4, "arr1", "arr2").is_err());
    }
}