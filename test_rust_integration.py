#!/usr/bin/env python3
"""
Integration test for the PT-CLI Rust calculation engine.
Tests all calculation methods and validates results.
"""

import sys
import numpy as np
import pt_cli_rust

def test_algorithm_a():
    """Test Algorithm A calculation."""
    print("Testing Algorithm A...")
    results = np.array([9.8, 10.0, 10.2, 9.9, 10.1, 9.7, 10.3, 10.05, 9.95, 10.15])
    
    x_pt, s_star, participants_used, iterations = pt_cli_rust.py_calculate_algorithm_a(results)
    print(f"  x_pt: {x_pt:.6f}")
    print(f"  s_star: {s_star:.6f}")
    print(f"  participants_used: {participants_used}")
    print(f"  iterations: {iterations}")
    
    # Calculate uncertainty
    u_x_pt = pt_cli_rust.py_calculate_uncertainty_consensus(s_star, participants_used)
    print(f"  u(x_pt): {u_x_pt:.6f}")
    
    # Basic sanity checks
    assert 9.5 < x_pt < 10.5, f"x_pt {x_pt} is not reasonable"
    assert s_star > 0, f"s_star {s_star} should be positive"
    assert u_x_pt > 0, f"u_x_pt {u_x_pt} should be positive"
    assert participants_used <= len(results), f"participants_used {participants_used} exceeds input size"
    
    print("  ✓ Algorithm A test passed")
    return x_pt, u_x_pt


def test_crm():
    """Test CRM calculation."""
    print("Testing CRM method...")
    crm_value = 10.0
    crm_uncertainty = 0.05
    
    x_pt = pt_cli_rust.py_calculate_from_crm(crm_value)
    u_x_pt = pt_cli_rust.py_calculate_uncertainty_crm(crm_uncertainty)
    
    print(f"  x_pt: {x_pt:.6f}")
    print(f"  u(x_pt): {u_x_pt:.6f}")
    
    assert x_pt == crm_value, f"CRM x_pt {x_pt} should equal certified value {crm_value}"
    assert u_x_pt == crm_uncertainty, f"CRM u_x_pt {u_x_pt} should equal certified uncertainty {crm_uncertainty}"
    
    print("  ✓ CRM test passed")
    return x_pt, u_x_pt


def test_formulation():
    """Test Formulation calculation."""
    print("Testing Formulation method...")
    formulation_value = 9.95
    formulation_uncertainty = 0.03
    
    x_pt = pt_cli_rust.py_calculate_from_formulation(formulation_value)
    u_x_pt = pt_cli_rust.py_calculate_uncertainty_formulation(formulation_uncertainty)
    
    print(f"  x_pt: {x_pt:.6f}")
    print(f"  u(x_pt): {u_x_pt:.6f}")
    
    assert x_pt == formulation_value, f"Formulation x_pt {x_pt} should equal known value {formulation_value}"
    assert u_x_pt == formulation_uncertainty, f"Formulation u_x_pt {u_x_pt} should equal known uncertainty {formulation_uncertainty}"
    
    print("  ✓ Formulation test passed")
    return x_pt, u_x_pt


def test_expert():
    """Test Expert consensus calculation."""
    print("Testing Expert consensus method...")
    expert_value = 10.05
    expert_uncertainty = 0.08
    
    x_pt = pt_cli_rust.py_calculate_from_expert_consensus(expert_value)
    u_x_pt = pt_cli_rust.py_calculate_uncertainty_expert(expert_uncertainty)
    
    print(f"  x_pt: {x_pt:.6f}")
    print(f"  u(x_pt): {u_x_pt:.6f}")
    
    assert x_pt == expert_value, f"Expert x_pt {x_pt} should equal consensus value {expert_value}"
    assert u_x_pt == expert_uncertainty, f"Expert u_x_pt {u_x_pt} should equal consensus uncertainty {expert_uncertainty}"
    
    print("  ✓ Expert consensus test passed")
    return x_pt, u_x_pt


def test_scoring():
    """Test scoring calculations."""
    print("Testing scoring calculations...")
    results = np.array([9.8, 10.0, 10.2, 9.9, 10.1])
    uncertainties = np.array([0.05, 0.06, 0.04, 0.07, 0.05])
    x_pt = 10.0
    u_x_pt = 0.05
    sigma_pt = 0.15
    
    # Test z-scores
    z_scores = pt_cli_rust.py_calculate_z_scores(results, x_pt, sigma_pt)
    print(f"  z_scores: {z_scores}")
    
    assert len(z_scores) == len(results), "z_scores length should match results length"
    assert abs(z_scores[1]) < 1e-10, "z_score for exact match should be ~0"  # results[1] == x_pt
    
    # Test zeta-scores
    z_prime_scores = pt_cli_rust.py_calculate_z_prime_scores(results, uncertainties, x_pt, u_x_pt)
    print(f"  z_prime_scores: {z_prime_scores}")
    
    assert len(z_prime_scores) == len(results), "z_prime_scores length should match results length"
    
    # Test simplified zeta-scores
    z_prime_simple = pt_cli_rust.py_calculate_z_prime_scores_no_uncertainties(results, x_pt, u_x_pt)
    print(f"  z_prime_simple: {z_prime_simple}")
    
    assert len(z_prime_simple) == len(results), "z_prime_simple length should match results length"
    
    print("  ✓ Scoring test passed")


def test_error_handling():
    """Test error handling."""
    print("Testing error handling...")
    
    # Test insufficient data for Algorithm A
    try:
        small_data = np.array([1.0, 2.0])  # Too few points
        pt_cli_rust.py_calculate_algorithm_a(small_data)
        assert False, "Should have raised an error for insufficient data"
    except ValueError:
        print("  ✓ Insufficient data error caught correctly")
    
    # Test invalid values
    try:
        invalid_data = np.array([1.0, np.nan, 3.0])
        pt_cli_rust.py_calculate_algorithm_a(invalid_data)
        assert False, "Should have raised an error for NaN values"
    except ValueError:
        print("  ✓ Invalid data error caught correctly")
    
    # Test invalid sigma_pt
    try:
        valid_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        pt_cli_rust.py_calculate_z_scores(valid_data, 3.0, 0.0)  # sigma_pt = 0
        assert False, "Should have raised an error for zero sigma_pt"
    except ValueError:
        print("  ✓ Invalid sigma_pt error caught correctly")
    
    print("  ✓ Error handling test passed")


def main():
    """Run all tests."""
    print("Running PT-CLI Rust Engine Integration Tests")
    print("=" * 50)
    
    try:
        test_algorithm_a()
        print()
        test_crm()
        print()
        test_formulation()
        print()
        test_expert()
        print()
        test_scoring()
        print()
        test_error_handling()
        print()
        
        print("=" * 50)
        print("✓ All tests passed successfully!")
        print("The Rust calculation engine is working correctly.")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()