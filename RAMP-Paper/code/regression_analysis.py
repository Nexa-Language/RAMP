#!/usr/bin/env python3
"""Compute regression analysis for process metrics → outcome prediction.

Addresses reviewer concern C3: "Process metrics lack causal insight beyond 
descriptive statistics." We show that build count and elapsed time can 
predict pipeline score via regression.
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats

CSV_PATH = Path("RAMP-paper/results/leaderboard_with_process.csv")
OUTPUT_DIR = Path("RAMP-paper/results")

def main():
    import csv
    rows = []
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    # Extract variables
    builds = np.array([float(r['builds']) for r in rows])
    elapsed = np.array([float(r['elapsed']) for r in rows])
    scores = np.array([float(r['scores']) for r in rows])
    pl = np.array([float(r['pl']) for r in rows])
    
    # Regression 1: build count → pipeline score
    slope_b, intercept_b, r_b, p_b, se_b = stats.linregress(builds, pl)
    
    # Regression 2: elapsed time → pipeline score
    slope_e, intercept_e, r_e, p_e, se_e = stats.linregress(elapsed, pl)
    
    # Regression 3: build count + elapsed time → pipeline score (multiple regression)
    # Using simple OLS: PL = a + b*builds + c*elapsed
    X = np.column_stack([builds, elapsed])
    X_with_const = np.column_stack([np.ones(len(builds)), builds, elapsed])
    # OLS: beta = (X'X)^-1 X'y
    beta = np.linalg.lstsq(X_with_const, pl, rcond=None)[0]
    residuals = pl - X_with_const @ beta
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((pl - np.mean(pl))**2)
    r2_multi = 1 - ss_res / ss_tot
    
    # Pearson correlations
    pearson_builds_pl, p_pearson_builds = stats.pearsonr(builds, pl)
    pearson_elapsed_pl, p_pearson_elapsed = stats.pearsonr(elapsed, pl)
    
    print("=== Regression Analysis: Process Metrics → Outcome ===")
    print(f"\nRegression 1: Build count → Pipeline Score")
    print(f"  slope = {slope_b:.4f}, intercept = {intercept_b:.2f}")
    print(f"  R² = {r_b**2:.4f}, p = {p_b:.6f}")
    print(f"  Pearson r = {pearson_builds_pl:.4f}, p = {p_pearson_builds:.6f}")
    
    print(f"\nRegression 2: Elapsed time → Pipeline Score")
    print(f"  slope = {slope_e:.6f}, intercept = {intercept_e:.2f}")
    print(f"  R² = {r_e**2:.4f}, p = {p_e:.6f}")
    print(f"  Pearson r = {pearson_elapsed_pl:.4f}, p = {p_pearson_elapsed:.6f}")
    
    print(f"\nRegression 3: Build count + Elapsed time → Pipeline Score (multiple)")
    print(f"  beta = {beta}")
    print(f"  R² = {r2_multi:.4f}")
    
    # Interpretation
    print(f"\n=== Interpretation ===")
    if r_b**2 > 0.3:
        print(f"Build count has moderate predictive power (R²={r_b**2:.3f}) for pipeline score.")
    else:
        print(f"Build count has weak predictive power (R²={r_b**2:.3f}) for pipeline score.")
    
    if r_e**2 > 0.3:
        print(f"Elapsed time has moderate predictive power (R²={r_e**2:.3f}) for pipeline score.")
    else:
        print(f"Elapsed time has weak predictive power (R²={r_e**2:.3f}) for pipeline score.")
    
    print(f"Combined model R²={r2_multi:.3f} — process metrics jointly explain {r2_multi*100:.1f}% of pipeline score variance.")
    
    # Save results
    output = {
        "regression_builds_pl": {"slope": slope_b, "intercept": intercept_b, "r_squared": r_b**2, "p_value": p_b, "pearson_r": pearson_builds_pl},
        "regression_elapsed_pl": {"slope": slope_e, "intercept": intercept_e, "r_squared": r_e**2, "p_value": p_e, "pearson_r": pearson_elapsed_pl},
        "regression_multiple": {"beta": list(beta), "r_squared": r2_multi},
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_DIR / "regression_analysis.json").write_text(json.dumps(output, indent=2))
    print(f"\nSaved regression_analysis.json")


if __name__ == "__main__":
    main()