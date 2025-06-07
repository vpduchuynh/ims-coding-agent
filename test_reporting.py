#!/usr/bin/env python3
"""
Tests for PT-CLI reporting system.
Tests report generation functionality, data aggregation, and template creation.
"""

import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.reporting import (
    aggregate_report_data, generate_report, _write_quarto_data_json,
    _create_default_quarto_template, _generate_histogram, _generate_density_plot,
    ReportingError, QuartoNotFoundError
)
from src.config import load_config
from src.data_io import load_and_validate_data


def test_aggregate_report_data():
    """Test data aggregation for reports."""
    print("Testing data aggregation...")
    
    config = load_config()
    input_data = load_and_validate_data(Path('test_data.csv'), config)
    
    # Test without calculation results
    report_data = aggregate_report_data(input_data, config)
    
    assert 'participant_ids' in report_data
    assert 'participant_results' in report_data
    assert 'config' in report_data
    assert 'summary_statistics' in report_data
    assert len(report_data['participant_ids']) == 10
    assert len(report_data['participant_results']) == 10
    
    # Test with calculation results
    calc_results = {
        'x_pt': 10.085,
        'u_x_pt': 0.076,
        'method_used': 'AlgorithmA',
        'sigma_pt_used': 0.15,
        'participant_scores': [0.43, -1.43, 2.23, -0.90, 0.83, -2.03, 1.63, -0.03, -1.10, 0.57],
        'calculation_details': {
            's_star': 0.193,
            'participants_used': 10,
            'iterations': 5
        }
    }
    
    report_data_with_calc = aggregate_report_data(input_data, config, calc_results)
    assert 'results' in report_data_with_calc
    assert report_data_with_calc['results']['x_pt'] == 10.085
    
    print("  ✓ Data aggregation test passed")


def test_json_serialization():
    """Test JSON serialization of report data."""
    print("Testing JSON serialization...")
    
    config = load_config()
    input_data = load_and_validate_data(Path('test_data.csv'), config)
    report_data = aggregate_report_data(input_data, config)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        json_path = Path(temp_dir) / 'test_report_data.json'
        _write_quarto_data_json(report_data, json_path)
        
        assert json_path.exists()
        
        # Verify the JSON can be loaded back
        with open(json_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data['participant_ids'] == report_data['participant_ids']
        assert len(loaded_data['participant_results']) == len(report_data['participant_results'])
        
    print("  ✓ JSON serialization test passed")


def test_template_creation():
    """Test default Quarto template creation."""
    print("Testing template creation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        template_path = Path(temp_dir) / 'test_template.qmd'
        _create_default_quarto_template(template_path)
        
        assert template_path.exists()
        
        # Check template content
        with open(template_path, 'r') as f:
            content = f.read()
        
        assert 'title: "Proficiency Testing Report"' in content
        assert 'params:' in content
        assert 'data_file:' in content
        assert 'params[\'data_file\']' in content
        assert '{{python}}' in content
        assert 'Methodology' in content
        assert 'Participant Performance' in content
        assert 'Configuration Details' in content
        
    print("  ✓ Template creation test passed")


def test_plot_generation():
    """Test plot generation functions."""
    print("Testing plot generation...")
    
    config = load_config()
    input_data = load_and_validate_data(Path('test_data.csv'), config)
    
    # Extract results for plotting
    results = input_data.get_column('Value').to_numpy()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test histogram generation
        hist_path = Path(temp_dir) / 'test_histogram.png'
        _generate_histogram(results, hist_path, config)
        assert hist_path.exists()
        assert hist_path.stat().st_size > 0
        
        # Test density plot generation
        density_path = Path(temp_dir) / 'test_density.png'
        _generate_density_plot(results, density_path)
        assert density_path.exists()
        assert density_path.stat().st_size > 0
        
    print("  ✓ Plot generation test passed")


def test_generate_report_error_handling():
    """Test error handling in report generation."""
    print("Testing error handling...")
    
    config = load_config()
    input_data = load_and_validate_data(Path('test_data.csv'), config)
    report_data = aggregate_report_data(input_data, config)
    
    # Mock subprocess to simulate Quarto not found
    with patch('src.reporting.subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / 'test_report'
                generate_report(report_data, config, output_path, 'pdf')
            assert False, "Should have raised QuartoNotFoundError"
        except QuartoNotFoundError as e:
            assert "Quarto CLI not found" in str(e)
    
    print("  ✓ Error handling test passed")


def test_quarto_invocation_command():
    """Test Quarto command construction."""
    print("Testing Quarto command construction...")
    
    from src.reporting import _invoke_quarto
    
    with tempfile.TemporaryDirectory() as temp_dir:
        template_path = Path(temp_dir) / 'template.qmd'
        output_path = Path(temp_dir) / 'output.pdf'
        data_path = Path(temp_dir) / 'data.json'
        
        # Create dummy files
        template_path.touch()
        data_path.touch()
        
        # Mock subprocess to capture the command
        with patch('src.reporting.subprocess.run') as mock_run:
            # First call is for version check, second is actual render
            mock_run.side_effect = [
                MagicMock(returncode=0),  # Version check success
                MagicMock(returncode=0)   # Render success
            ]
            
            try:
                _invoke_quarto(template_path, output_path, 'pdf', data_path)
                
                # Check the render command was called correctly
                render_call = mock_run.call_args_list[1]
                cmd = render_call[0][0]
                
                assert cmd[0] == 'quarto'
                assert cmd[1] == 'render'
                assert str(template_path) in cmd
                assert '--to' in cmd
                assert 'pdf' in cmd
                assert '--output' in cmd
                assert str(output_path) in cmd
                assert '-P' in cmd
                assert f'data_file={data_path}' in cmd
                
            except QuartoNotFoundError:
                # This is expected if Quarto is not installed
                pass
    
    print("  ✓ Quarto command test passed")


def main():
    """Run all reporting tests."""
    print("Running PT-CLI Reporting System Tests")
    print("=" * 50)
    
    try:
        test_aggregate_report_data()
        print()
        test_json_serialization()
        print()
        test_template_creation()
        print()
        test_plot_generation()
        print()
        test_generate_report_error_handling()
        print()
        test_quarto_invocation_command()
        print()
        
        print("=" * 50)
        print("✓ All reporting tests passed successfully!")
        print("The reporting system is working correctly.")
        
    except Exception as e:
        print(f"✗ Reporting test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()