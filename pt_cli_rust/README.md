# PT-CLI Rust Calculation Engine

High-performance statistical calculation engine for the PT-CLI application, implementing algorithms specified in ISO 13528:2022.

## Features

- **Algorithm A**: Robust statistics for assigned value calculation
- **Multiple estimation methods**: CRM, formulation, and expert consensus
- **Uncertainty calculations**: Corresponding to each estimation method
- **Performance scoring**: z-scores and zeta-scores
- **PyO3 integration**: Seamless Python-Rust interoperability
- **Memory safety**: Leveraging Rust's ownership system
- **High performance**: Optimized numerical computations

## Building

```bash
pip install maturin
maturin develop
```

## Usage

```python
import numpy as np
import pt_cli_rust

# Calculate assigned value using Algorithm A
results = np.array([9.8, 10.0, 10.2, 9.9, 10.1])
x_pt, s_star, participants_used, iterations = pt_cli_rust.py_calculate_algorithm_a(results)

# Calculate uncertainty
u_x_pt = pt_cli_rust.py_calculate_uncertainty_consensus(s_star, participants_used)

# Calculate z-scores
z_scores = pt_cli_rust.py_calculate_z_scores(results, x_pt, 0.1)
```