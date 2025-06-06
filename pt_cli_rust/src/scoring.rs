//! Performance score calculation module
//!
//! This module implements the calculation of participant performance scores
//! (z-scores and zeta-scores) based on calculated assigned values and uncertainties.

use crate::utils::{CalculationError, validate_array_dimensions, validate_floats, is_valid_float};
use ndarray::{Array1, ArrayView1};

/// Calculate z-scores for participant performance assessment
/// 
/// Implements the formula: z = (x_i - x_pt) / σ_pt
/// 
/// # Arguments
/// * `results` - Array view of participant results (x_i)
/// * `x_pt` - Assigned value
/// * `sigma_pt` - Standard deviation for proficiency assessment
/// 
/// # Returns
/// * `Ok(Array1<f64>)` - Array of z-scores for each participant
/// * `Err(CalculationError)` - If calculation fails
pub fn calculate_z_scores(
    results: ArrayView1<f64>,
    x_pt: f64,
    sigma_pt: f64,
) -> Result<Array1<f64>, CalculationError> {
    let data = results.to_vec();
    
    // Validate inputs
    validate_floats(&data, "participant results")?;
    
    if !is_valid_float(x_pt) {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid assigned value x_pt: {}", x_pt),
        });
    }
    
    if !is_valid_float(sigma_pt) || sigma_pt <= 0.0 {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid or non-positive sigma_pt: {}", sigma_pt),
        });
    }
    
    // Calculate z-scores
    let z_scores: Vec<f64> = data.iter()
        .map(|&x_i| (x_i - x_pt) / sigma_pt)
        .collect();
    
    Ok(Array1::from(z_scores))
}

/// Calculate zeta-scores (z'-scores) for participant performance assessment
/// 
/// Implements the formula: z' = (x_i - x_pt) / sqrt(u(x_i)^2 + u(x_pt)^2)
/// 
/// # Arguments
/// * `results` - Array view of participant results (x_i)
/// * `u_results` - Array view of participant uncertainties (u(x_i))
/// * `x_pt` - Assigned value
/// * `u_x_pt` - Uncertainty of the assigned value
/// 
/// # Returns
/// * `Ok(Array1<f64>)` - Array of zeta-scores for each participant
/// * `Err(CalculationError)` - If calculation fails
pub fn calculate_z_prime_scores(
    results: ArrayView1<f64>,
    u_results: ArrayView1<f64>,
    x_pt: f64,
    u_x_pt: f64,
) -> Result<Array1<f64>, CalculationError> {
    let data = results.to_vec();
    let uncertainties = u_results.to_vec();
    
    // Validate array dimensions
    validate_array_dimensions(data.len(), uncertainties.len(), "results", "uncertainties")?;
    
    // Validate inputs
    validate_floats(&data, "participant results")?;
    validate_floats(&uncertainties, "participant uncertainties")?;
    
    if !is_valid_float(x_pt) {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid assigned value x_pt: {}", x_pt),
        });
    }
    
    if !is_valid_float(u_x_pt) || u_x_pt < 0.0 {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid or negative u(x_pt): {}", u_x_pt),
        });
    }
    
    // Check for non-negative uncertainties
    for (i, &u_i) in uncertainties.iter().enumerate() {
        if u_i < 0.0 {
            return Err(CalculationError::InvalidInput {
                message: format!("Negative uncertainty at index {}: {}", i, u_i),
            });
        }
    }
    
    // Calculate zeta-scores
    let mut z_prime_scores = Vec::with_capacity(data.len());
    
    for (i, (&x_i, &u_i)) in data.iter().zip(uncertainties.iter()).enumerate() {
        let combined_uncertainty_squared = u_i.powi(2) + u_x_pt.powi(2);
        
        if combined_uncertainty_squared <= 0.0 {
            return Err(CalculationError::DivisionByZero);
        }
        
        let combined_uncertainty = combined_uncertainty_squared.sqrt();
        let z_prime = (x_i - x_pt) / combined_uncertainty;
        
        z_prime_scores.push(z_prime);
    }
    
    Ok(Array1::from(z_prime_scores))
}

/// Calculate zeta-scores when participant uncertainties are zero or missing
/// 
/// This is a fallback that uses only the assigned value uncertainty.
/// 
/// # Arguments
/// * `results` - Array view of participant results (x_i)
/// * `x_pt` - Assigned value
/// * `u_x_pt` - Uncertainty of the assigned value
/// 
/// # Returns
/// * `Ok(Array1<f64>)` - Array of modified zeta-scores
/// * `Err(CalculationError)` - If calculation fails
pub fn calculate_z_prime_scores_no_participant_uncertainties(
    results: ArrayView1<f64>,
    x_pt: f64,
    u_x_pt: f64,
) -> Result<Array1<f64>, CalculationError> {
    let data = results.to_vec();
    
    // Validate inputs
    validate_floats(&data, "participant results")?;
    
    if !is_valid_float(x_pt) {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid assigned value x_pt: {}", x_pt),
        });
    }
    
    if !is_valid_float(u_x_pt) || u_x_pt <= 0.0 {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid or non-positive u(x_pt): {}", u_x_pt),
        });
    }
    
    // Calculate simplified zeta-scores using only assigned value uncertainty
    let z_prime_scores: Vec<f64> = data.iter()
        .map(|&x_i| (x_i - x_pt) / u_x_pt)
        .collect();
    
    Ok(Array1::from(z_prime_scores))
}

/// Interpret z-score performance according to ISO 13528:2022
/// 
/// # Arguments
/// * `z_score` - The calculated z-score
/// 
/// # Returns
/// * String describing the performance level
pub fn interpret_z_score(z_score: f64) -> String {
    let abs_z = z_score.abs();
    
    if abs_z <= 2.0 {
        "Satisfactory".to_string()
    } else if abs_z <= 3.0 {
        "Questionable".to_string()
    } else {
        "Unsatisfactory".to_string()
    }
}

/// Interpret zeta-score performance according to ISO 13528:2022
/// 
/// # Arguments
/// * `z_prime_score` - The calculated zeta-score
/// 
/// # Returns
/// * String describing the performance level
pub fn interpret_z_prime_score(z_prime_score: f64) -> String {
    let abs_z_prime = z_prime_score.abs();
    
    if abs_z_prime <= 2.0 {
        "Satisfactory".to_string()
    } else {
        "Unsatisfactory".to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;
    use ndarray::array;

    #[test]
    fn test_z_scores_calculation() {
        let results = array![9.8, 10.0, 10.2, 9.9, 10.1];
        let x_pt = 10.0;
        let sigma_pt = 0.1;
        
        let z_scores = calculate_z_scores(results.view(), x_pt, sigma_pt).unwrap();
        
        assert_eq!(z_scores.len(), 5);
        assert_abs_diff_eq!(z_scores[0], -2.0, epsilon = 1e-10); // (9.8 - 10.0) / 0.1
        assert_abs_diff_eq!(z_scores[1], 0.0, epsilon = 1e-10);  // (10.0 - 10.0) / 0.1
        assert_abs_diff_eq!(z_scores[2], 2.0, epsilon = 1e-10);  // (10.2 - 10.0) / 0.1
    }

    #[test]
    fn test_z_scores_invalid_sigma() {
        let results = array![9.8, 10.0, 10.2];
        let x_pt = 10.0;
        let sigma_pt = 0.0; // Invalid
        
        let result = calculate_z_scores(results.view(), x_pt, sigma_pt);
        assert!(result.is_err());
    }

    #[test]
    fn test_z_prime_scores_calculation() {
        let results = array![9.8, 10.0, 10.2];
        let u_results = array![0.05, 0.05, 0.05];
        let x_pt = 10.0;
        let u_x_pt = 0.03;
        
        let z_prime_scores = calculate_z_prime_scores(
            results.view(), 
            u_results.view(), 
            x_pt, 
            u_x_pt
        ).unwrap();
        
        assert_eq!(z_prime_scores.len(), 3);
        
        // Combined uncertainty = sqrt(0.05^2 + 0.03^2) = sqrt(0.0034) ≈ 0.0583
        let combined_u = (0.05_f64.powi(2) + 0.03_f64.powi(2)).sqrt();
        assert_abs_diff_eq!(z_prime_scores[0], -0.2 / combined_u, epsilon = 1e-6);
        assert_abs_diff_eq!(z_prime_scores[1], 0.0, epsilon = 1e-10);
        assert_abs_diff_eq!(z_prime_scores[2], 0.2 / combined_u, epsilon = 1e-6);
    }

    #[test]
    fn test_z_prime_scores_dimension_mismatch() {
        let results = array![9.8, 10.0, 10.2];
        let u_results = array![0.05, 0.05]; // Wrong size
        let x_pt = 10.0;
        let u_x_pt = 0.03;
        
        let result = calculate_z_prime_scores(
            results.view(), 
            u_results.view(), 
            x_pt, 
            u_x_pt
        );
        assert!(result.is_err());
        matches!(result.unwrap_err(), CalculationError::DimensionMismatch { .. });
    }

    #[test]
    fn test_z_prime_scores_negative_uncertainty() {
        let results = array![9.8, 10.0, 10.2];
        let u_results = array![0.05, -0.05, 0.05]; // Negative uncertainty
        let x_pt = 10.0;
        let u_x_pt = 0.03;
        
        let result = calculate_z_prime_scores(
            results.view(), 
            u_results.view(), 
            x_pt, 
            u_x_pt
        );
        assert!(result.is_err());
        matches!(result.unwrap_err(), CalculationError::InvalidInput { .. });
    }

    #[test]
    fn test_z_prime_scores_no_participant_uncertainties() {
        let results = array![9.8, 10.0, 10.2];
        let x_pt = 10.0;
        let u_x_pt = 0.1;
        
        let z_prime_scores = calculate_z_prime_scores_no_participant_uncertainties(
            results.view(), 
            x_pt, 
            u_x_pt
        ).unwrap();
        
        assert_eq!(z_prime_scores.len(), 3);
        assert_abs_diff_eq!(z_prime_scores[0], -2.0, epsilon = 1e-10); // (9.8 - 10.0) / 0.1
        assert_abs_diff_eq!(z_prime_scores[1], 0.0, epsilon = 1e-10);  // (10.0 - 10.0) / 0.1
        assert_abs_diff_eq!(z_prime_scores[2], 2.0, epsilon = 1e-10);  // (10.2 - 10.0) / 0.1
    }

    #[test]
    fn test_z_score_interpretation() {
        assert_eq!(interpret_z_score(1.5), "Satisfactory");
        assert_eq!(interpret_z_score(-1.8), "Satisfactory");
        assert_eq!(interpret_z_score(2.5), "Questionable");
        assert_eq!(interpret_z_score(-2.7), "Questionable");
        assert_eq!(interpret_z_score(3.2), "Unsatisfactory");
        assert_eq!(interpret_z_score(-4.0), "Unsatisfactory");
    }

    #[test]
    fn test_z_prime_score_interpretation() {
        assert_eq!(interpret_z_prime_score(1.5), "Satisfactory");
        assert_eq!(interpret_z_prime_score(-1.9), "Satisfactory");
        assert_eq!(interpret_z_prime_score(2.1), "Unsatisfactory");
        assert_eq!(interpret_z_prime_score(-3.0), "Unsatisfactory");
    }

    #[test]
    fn test_z_scores_with_invalid_data() {
        let results = array![9.8, f64::NAN, 10.2];
        let x_pt = 10.0;
        let sigma_pt = 0.1;
        
        let result = calculate_z_scores(results.view(), x_pt, sigma_pt);
        assert!(result.is_err());
        matches!(result.unwrap_err(), CalculationError::InvalidInput { .. });
    }
}