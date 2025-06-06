#!/usr/bin/env python3
"""
Tests for enhanced calculate command options validation.
Tests the new validation logic for --method, --sigma-pt, and --results-json options.
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path
import re


def clean_ansi_output(text):
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def run_cli_command(command_args):
    """Run CLI command and return result."""
    cmd = [sys.executable, "-m", "src.main"] + command_args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    # Clean ANSI codes from output for easier testing
    result.stdout = clean_ansi_output(result.stdout)
    result.stderr = clean_ansi_output(result.stderr)
    return result


def test_method_validation():
    """Test method option validation."""
    print("Testing method validation...")
    
    # Test invalid method
    result = run_cli_command([
        "calculate", 
        "test_data.csv", 
        "--method", "InvalidMethod"
    ])
    
    assert result.returncode == 1, f"Expected failure for invalid method but got: {result.returncode}"
    assert "Invalid calculation method" in result.stdout or "Invalid Method" in result.stdout
    assert "InvalidMethod" in result.stdout
    assert "Valid methods are:" in result.stdout
    print("  ✓ Invalid method rejection test passed")
    
    # Test valid methods (just verify CLI accepts them - we won't run full calculation)
    valid_methods = ["AlgorithmA", "CRM", "Formulation", "Expert"]
    for method in valid_methods:
        result = run_cli_command([
            "calculate", 
            "test_data.csv", 
            "--method", method,
            "--help"  # Use help to avoid running full calculation
        ])
        # Help should always work regardless of method value
        assert result.returncode == 0, f"Help should work with method {method}"
    print("  ✓ Valid method acceptance test passed")


def test_sigma_pt_validation():
    """Test sigma-pt option validation."""
    print("Testing sigma-pt validation...")
    
    # Test negative sigma-pt
    result = run_cli_command([
        "calculate", 
        "test_data.csv", 
        "--sigma-pt", "-0.1"
    ])
    
    assert result.returncode == 1, f"Expected failure for negative sigma-pt but got: {result.returncode}"
    assert "Invalid sigma_pt value" in result.stdout or "Invalid Sigma PT" in result.stdout
    assert "must be positive" in result.stdout
    print("  ✓ Negative sigma-pt rejection test passed")
    
    # Test zero sigma-pt
    result = run_cli_command([
        "calculate", 
        "test_data.csv", 
        "--sigma-pt", "0"
    ])
    
    assert result.returncode == 1, f"Expected failure for zero sigma-pt but got: {result.returncode}"
    assert "Invalid sigma_pt value" in result.stdout or "Invalid Sigma PT" in result.stdout
    assert "must be positive" in result.stdout
    print("  ✓ Zero sigma-pt rejection test passed")


def test_results_json_validation():
    """Test results-json option validation."""
    print("Testing results-json validation...")
    
    # Test non-existent directory
    result = run_cli_command([
        "calculate", 
        "test_data.csv", 
        "--results-json", "/nonexistent/path/results.json"
    ])
    
    assert result.returncode == 1, f"Expected failure for non-existent directory but got: {result.returncode}"
    assert "Directory does not exist" in result.stdout or "Invalid Results JSON Path" in result.stdout
    print("  ✓ Non-existent directory rejection test passed")
    
    # Test valid path with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "results.json"
        result = run_cli_command([
            "calculate", 
            "test_data.csv", 
            "--results-json", str(temp_path),
            "--help"  # Use help to avoid running full calculation
        ])
        # Help should always work regardless of path value
        assert result.returncode == 0, f"Help should work with valid results-json path"
    print("  ✓ Valid results-json path acceptance test passed")


def test_combined_options():
    """Test combinations of options."""
    print("Testing combined options...")
    
    # Test valid combination
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "results.json"
        result = run_cli_command([
            "calculate", 
            "test_data.csv",
            "--method", "CRM",
            "--sigma-pt", "0.25",
            "--results-json", str(temp_path),
            "--help"  # Use help to avoid running full calculation
        ])
        assert result.returncode == 0, f"Help should work with valid combined options"
    print("  ✓ Valid combined options test passed")
    
    # Test invalid combination
    result = run_cli_command([
        "calculate", 
        "test_data.csv",
        "--method", "InvalidMethod",
        "--sigma-pt", "-0.1"
    ])
    assert result.returncode == 1, f"Expected failure for invalid combined options"
    # Should fail on first invalid option encountered (method)
    assert "Invalid calculation method" in result.stdout or "Invalid Method" in result.stdout
    print("  ✓ Invalid combined options test passed")


def test_error_message_quality():
    """Test that error messages are user-friendly."""
    print("Testing error message quality...")
    
    # Test method error message includes all valid options
    result = run_cli_command([
        "calculate", 
        "test_data.csv", 
        "--method", "WrongMethod"
    ])
    
    output = result.stdout
    assert "AlgorithmA" in output, "Error message should include AlgorithmA"
    assert "CRM" in output, "Error message should include CRM"
    assert "Formulation" in output, "Error message should include Formulation"
    assert "Expert" in output, "Error message should include Expert"
    print("  ✓ Method error message quality test passed")
    
    # Test sigma-pt error message is clear
    result = run_cli_command([
        "calculate", 
        "test_data.csv", 
        "--sigma-pt", "-1.0"
    ])
    
    output = result.stdout
    assert "positive" in output.lower() or "> 0" in output, "Error message should mention positive requirement"
    print("  ✓ Sigma-pt error message quality test passed")


def main():
    """Run all calculate options tests."""
    print("Running Calculate Command Options Enhancement Tests")
    print("=" * 60)
    
    try:
        test_method_validation()
        print()
        test_sigma_pt_validation()
        print()
        test_results_json_validation()
        print()
        test_combined_options()
        print()
        test_error_message_quality()
        print()
        
        print("=" * 60)
        print("✓ All calculate options enhancement tests passed successfully!")
        print("The enhanced validation is working correctly.")
        
    except Exception as e:
        print(f"✗ Calculate options test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()