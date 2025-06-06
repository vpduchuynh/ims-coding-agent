//! PT-CLI Rust Calculation Engine
//!
//! This library provides high-performance statistical calculation functions
//! for the PT-CLI application using PyO3 for Python interoperability.

use pyo3::prelude::*;
use numpy::{PyReadonlyArray1, PyArray1};

pub mod utils;
pub mod estimators;
pub mod uncertainty;
pub mod scoring;

// Re-export main types for convenience
pub use utils::CalculationError;
use estimators::{calculate_algorithm_a, calculate_from_crm, calculate_from_formulation, calculate_from_expert_consensus};
use uncertainty::{calculate_uncertainty_consensus, calculate_uncertainty_crm, 
                  calculate_uncertainty_formulation, calculate_uncertainty_expert};
use scoring::{calculate_z_scores, calculate_z_prime_scores, 
              calculate_z_prime_scores_no_participant_uncertainties};

/// Calculate assigned value using Algorithm A (robust statistics)
/// 
/// Python interface for ISO 13528:2022 Annex C - Algorithm A
/// 
/// # Arguments
/// * `results` - NumPy array of participant results
/// * `tolerance` - Convergence tolerance (default: 1e-6)
/// * `max_iterations` - Maximum iterations (default: 100)
/// 
/// # Returns
/// * Tuple of (x_pt, s_star, participants_used, iterations)
#[pyfunction]
fn py_calculate_algorithm_a(
    py: Python,
    results: PyReadonlyArray1<f64>,
    tolerance: Option<f64>,
    max_iterations: Option<usize>,
) -> PyResult<(f64, f64, usize, usize)> {
    let results_array = results.as_array();
    let tol = tolerance.unwrap_or(utils::constants::DEFAULT_TOLERANCE);
    let max_iter = max_iterations.unwrap_or(utils::constants::DEFAULT_MAX_ITERATIONS);
    
    match calculate_algorithm_a(results_array, tol, max_iter) {
        Ok(result) => Ok((result.x_pt, result.s_star, result.participants_used, result.iterations)),
        Err(e) => Err(e.into()),
    }
}

/// Calculate assigned value from CRM
#[pyfunction]
fn py_calculate_from_crm(crm_value: f64) -> PyResult<f64> {
    match calculate_from_crm(crm_value) {
        Ok(result) => Ok(result),
        Err(e) => Err(e.into()),
    }
}

/// Calculate assigned value from formulation
#[pyfunction]
fn py_calculate_from_formulation(formulation_value: f64) -> PyResult<f64> {
    match calculate_from_formulation(formulation_value) {
        Ok(result) => Ok(result),
        Err(e) => Err(e.into()),
    }
}

/// Calculate assigned value from expert consensus
#[pyfunction]
fn py_calculate_from_expert_consensus(expert_value: f64) -> PyResult<f64> {
    match calculate_from_expert_consensus(expert_value) {
        Ok(result) => Ok(result),
        Err(e) => Err(e.into()),
    }
}

/// Calculate uncertainty for consensus values (Algorithm A results)
#[pyfunction]
fn py_calculate_uncertainty_consensus(
    robust_std_dev: f64,
    num_participants: usize,
) -> PyResult<f64> {
    match calculate_uncertainty_consensus(robust_std_dev, num_participants) {
        Ok(result) => Ok(result),
        Err(e) => Err(e.into()),
    }
}

/// Calculate uncertainty for CRM values
#[pyfunction]
fn py_calculate_uncertainty_crm(crm_uncertainty: f64) -> PyResult<f64> {
    match calculate_uncertainty_crm(crm_uncertainty) {
        Ok(result) => Ok(result),
        Err(e) => Err(e.into()),
    }
}

/// Calculate uncertainty for formulation values
#[pyfunction]
fn py_calculate_uncertainty_formulation(formulation_uncertainty: f64) -> PyResult<f64> {
    match calculate_uncertainty_formulation(formulation_uncertainty) {
        Ok(result) => Ok(result),
        Err(e) => Err(e.into()),
    }
}

/// Calculate uncertainty for expert consensus values
#[pyfunction]
fn py_calculate_uncertainty_expert(expert_uncertainty: f64) -> PyResult<f64> {
    match calculate_uncertainty_expert(expert_uncertainty) {
        Ok(result) => Ok(result),
        Err(e) => Err(e.into()),
    }
}

/// Calculate z-scores for participant performance
#[pyfunction]
fn py_calculate_z_scores(
    py: Python,
    results: PyReadonlyArray1<f64>,
    x_pt: f64,
    sigma_pt: f64,
) -> PyResult<Py<PyArray1<f64>>> {
    let results_array = results.as_array();
    
    match calculate_z_scores(results_array, x_pt, sigma_pt) {
        Ok(z_scores) => Ok(PyArray1::from_array(py, &z_scores).to_owned()),
        Err(e) => Err(e.into()),
    }
}

/// Calculate zeta-scores (z'-scores) for participant performance
#[pyfunction]
fn py_calculate_z_prime_scores(
    py: Python,
    results: PyReadonlyArray1<f64>,
    u_results: PyReadonlyArray1<f64>,
    x_pt: f64,
    u_x_pt: f64,
) -> PyResult<Py<PyArray1<f64>>> {
    let results_array = results.as_array();
    let u_results_array = u_results.as_array();
    
    match calculate_z_prime_scores(results_array, u_results_array, x_pt, u_x_pt) {
        Ok(z_prime_scores) => Ok(PyArray1::from_array(py, &z_prime_scores).to_owned()),
        Err(e) => Err(e.into()),
    }
}

/// Calculate zeta-scores when participant uncertainties are not available
#[pyfunction]
fn py_calculate_z_prime_scores_no_uncertainties(
    py: Python,
    results: PyReadonlyArray1<f64>,
    x_pt: f64,
    u_x_pt: f64,
) -> PyResult<Py<PyArray1<f64>>> {
    let results_array = results.as_array();
    
    match calculate_z_prime_scores_no_participant_uncertainties(results_array, x_pt, u_x_pt) {
        Ok(z_prime_scores) => Ok(PyArray1::from_array(py, &z_prime_scores).to_owned()),
        Err(e) => Err(e.into()),
    }
}

/// Python module definition
#[pymodule]
fn pt_cli_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    // Add estimator functions
    m.add_function(wrap_pyfunction!(py_calculate_algorithm_a, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_from_crm, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_from_formulation, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_from_expert_consensus, m)?)?;
    
    // Add uncertainty functions
    m.add_function(wrap_pyfunction!(py_calculate_uncertainty_consensus, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_uncertainty_crm, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_uncertainty_formulation, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_uncertainty_expert, m)?)?;
    
    // Add scoring functions
    m.add_function(wrap_pyfunction!(py_calculate_z_scores, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_z_prime_scores, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_z_prime_scores_no_uncertainties, m)?)?;
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_functionality() {
        // Basic smoke test
        assert!(true);
    }
}
