//! Uncertainty calculation module
//!
//! This module implements the logic for calculating the standard uncertainty 
//! of the assigned value (u(x_pt)) corresponding to different methods.

use crate::utils::{CalculationError, constants::UNCERTAINTY_FACTOR, is_valid_float};

/// Calculate uncertainty for consensus values (Algorithm A)
/// 
/// Implements u(x_pt) = 1.25 * s* / sqrt(p) where:
/// - s* is the robust standard deviation from Algorithm A
/// - p is the number of participants included in the calculation
/// 
/// # Arguments
/// * `robust_std_dev` - The robust standard deviation (s*) from Algorithm A
/// * `num_participants` - Number of participants included in the robust calculation
/// 
/// # Returns
/// * `Ok(f64)` - The calculated uncertainty u(x_pt)
/// * `Err(CalculationError)` - If inputs are invalid
pub fn calculate_uncertainty_consensus(
    robust_std_dev: f64,
    num_participants: usize,
) -> Result<f64, CalculationError> {
    if !is_valid_float(robust_std_dev) || robust_std_dev < 0.0 {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid robust standard deviation: {}", robust_std_dev),
        });
    }
    
    if num_participants == 0 {
        return Err(CalculationError::InsufficientData {
            required: 1,
            actual: 0,
        });
    }
    
    let uncertainty = UNCERTAINTY_FACTOR * robust_std_dev / (num_participants as f64).sqrt();
    
    Ok(uncertainty)
}

/// Calculate uncertainty for CRM values
/// 
/// For CRM-based assigned values, the uncertainty is taken directly from
/// the certificate.
/// 
/// # Arguments
/// * `crm_uncertainty` - The standard uncertainty stated on the CRM certificate
/// 
/// # Returns
/// * `Ok(f64)` - The CRM uncertainty as u(x_pt)
/// * `Err(CalculationError)` - If the uncertainty value is invalid
pub fn calculate_uncertainty_crm(crm_uncertainty: f64) -> Result<f64, CalculationError> {
    if !is_valid_float(crm_uncertainty) || crm_uncertainty < 0.0 {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid CRM uncertainty: {}", crm_uncertainty),
        });
    }
    
    Ok(crm_uncertainty)
}

/// Calculate uncertainty for formulation values
/// 
/// For formulation-based assigned values, the uncertainty is estimated
/// based on the formulation process and propagated uncertainties.
/// 
/// # Arguments
/// * `formulation_uncertainty` - The estimated uncertainty from the formulation process
/// 
/// # Returns
/// * `Ok(f64)` - The formulation uncertainty as u(x_pt)
/// * `Err(CalculationError)` - If the uncertainty value is invalid
pub fn calculate_uncertainty_formulation(
    formulation_uncertainty: f64,
) -> Result<f64, CalculationError> {
    if !is_valid_float(formulation_uncertainty) || formulation_uncertainty < 0.0 {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid formulation uncertainty: {}", formulation_uncertainty),
        });
    }
    
    Ok(formulation_uncertainty)
}

/// Calculate uncertainty for expert consensus values
/// 
/// For expert consensus values, the uncertainty can be calculated as the
/// standard error of the mean of expert results, or taken from expert assessment.
/// 
/// # Arguments
/// * `expert_uncertainty` - The uncertainty from expert consensus assessment
/// 
/// # Returns
/// * `Ok(f64)` - The expert consensus uncertainty as u(x_pt)
/// * `Err(CalculationError)` - If the uncertainty value is invalid
pub fn calculate_uncertainty_expert(expert_uncertainty: f64) -> Result<f64, CalculationError> {
    if !is_valid_float(expert_uncertainty) || expert_uncertainty < 0.0 {
        return Err(CalculationError::InvalidInput {
            message: format!("Invalid expert uncertainty: {}", expert_uncertainty),
        });
    }
    
    Ok(expert_uncertainty)
}

/// Calculate uncertainty for expert consensus from multiple expert results
/// 
/// Alternative method that calculates uncertainty as standard error of expert results.
/// 
/// # Arguments  
/// * `expert_results` - Array of results from expert laboratories
/// 
/// # Returns
/// * `Ok(f64)` - The calculated uncertainty as standard error of the mean
/// * `Err(CalculationError)` - If calculation fails
pub fn calculate_uncertainty_expert_from_results(
    expert_results: &[f64],
) -> Result<f64, CalculationError> {
    if expert_results.is_empty() {
        return Err(CalculationError::InsufficientData {
            required: 1,
            actual: 0,
        });
    }
    
    // Validate all expert results
    for (i, &result) in expert_results.iter().enumerate() {
        if !is_valid_float(result) {
            return Err(CalculationError::InvalidInput {
                message: format!("Invalid expert result at index {}: {}", i, result),
            });
        }
    }
    
    if expert_results.len() == 1 {
        // Single expert - return zero uncertainty or require external uncertainty
        return Ok(0.0);
    }
    
    // Calculate mean
    let mean = expert_results.iter().sum::<f64>() / expert_results.len() as f64;
    
    // Calculate sample standard deviation
    let variance = expert_results.iter()
        .map(|&x| (x - mean).powi(2))
        .sum::<f64>() / (expert_results.len() - 1) as f64;
    
    let std_dev = variance.sqrt();
    
    // Standard error of the mean
    let uncertainty = std_dev / (expert_results.len() as f64).sqrt();
    
    Ok(uncertainty)
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;

    #[test]
    fn test_uncertainty_consensus() {
        let robust_std = 1.0;
        let participants = 25;
        let result = calculate_uncertainty_consensus(robust_std, participants).unwrap();
        
        // u(x_pt) = 1.25 * 1.0 / sqrt(25) = 1.25 / 5 = 0.25
        assert_abs_diff_eq!(result, 0.25, epsilon = 1e-10);
    }

    #[test]
    fn test_uncertainty_consensus_invalid_inputs() {
        // Invalid standard deviation
        assert!(calculate_uncertainty_consensus(f64::NAN, 10).is_err());
        assert!(calculate_uncertainty_consensus(-1.0, 10).is_err());
        
        // Zero participants
        assert!(calculate_uncertainty_consensus(1.0, 0).is_err());
    }

    #[test]
    fn test_uncertainty_crm() {
        let crm_unc = 0.15;
        let result = calculate_uncertainty_crm(crm_unc).unwrap();
        assert_eq!(result, 0.15);
        
        // Invalid uncertainty
        assert!(calculate_uncertainty_crm(f64::NAN).is_err());
        assert!(calculate_uncertainty_crm(-0.1).is_err());
    }

    #[test]
    fn test_uncertainty_formulation() {
        let form_unc = 0.08;
        let result = calculate_uncertainty_formulation(form_unc).unwrap();
        assert_eq!(result, 0.08);
        
        // Invalid uncertainty
        assert!(calculate_uncertainty_formulation(f64::INFINITY).is_err());
        assert!(calculate_uncertainty_formulation(-0.05).is_err());
    }

    #[test]
    fn test_uncertainty_expert() {
        let expert_unc = 0.12;
        let result = calculate_uncertainty_expert(expert_unc).unwrap();
        assert_eq!(result, 0.12);
        
        // Invalid uncertainty
        assert!(calculate_uncertainty_expert(f64::NEG_INFINITY).is_err());
        assert!(calculate_uncertainty_expert(-0.01).is_err());
    }

    #[test]
    fn test_uncertainty_expert_from_results() {
        let expert_results = vec![10.0, 10.2, 9.8, 10.1, 9.9];
        let result = calculate_uncertainty_expert_from_results(&expert_results).unwrap();
        
        // Should calculate standard error of the mean
        assert!(result > 0.0);
        assert!(result < 1.0); // Should be reasonable
    }

    #[test]
    fn test_uncertainty_expert_from_results_single() {
        let expert_results = vec![10.0];
        let result = calculate_uncertainty_expert_from_results(&expert_results).unwrap();
        assert_eq!(result, 0.0); // Single result has zero standard error
    }

    #[test]
    fn test_uncertainty_expert_from_results_empty() {
        let expert_results = vec![];
        let result = calculate_uncertainty_expert_from_results(&expert_results);
        assert!(result.is_err());
        matches!(result.unwrap_err(), CalculationError::InsufficientData { .. });
    }

    #[test]
    fn test_uncertainty_expert_from_results_invalid() {
        let expert_results = vec![10.0, f64::NAN, 9.8];
        let result = calculate_uncertainty_expert_from_results(&expert_results);
        assert!(result.is_err());
        matches!(result.unwrap_err(), CalculationError::InvalidInput { .. });
    }
}