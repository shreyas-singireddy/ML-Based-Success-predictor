# ML Pipeline Phase 3 — CGPA Regression Model Comparison Report

**Generated (UTC):** 2026-09-12T20:10:45.906151+00:00  
**Selected Champion Model:** `LinearRegression`

## 1. Dataset Partition Summary
| Partition | Records | Percentage |
| :--- | :--- | :--- |
| Total Records | 715 | 100% |
| Training Split | 480 | 67.1% |
| Validation Split | 94 | 13.1% |
| Test Split | 141 | 19.7% |

## 2. Model Performance Comparison (Validation Split)
| Model | Model Type | Val MAE | Val MSE | Val RMSE | Val R² | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `LinearRegression` | baseline_linear | 0.1515 | 0.0371 | 0.1926 | 0.9843 | **CHAMPION** |
| `RandomForestRegressor` | tree_ensemble | 0.1753 | 0.0495 | 0.2225 | 0.979 | BASELINE/CANDIDATE |
| `XGBRegressor` | gradient_boosting | 0.1617 | 0.0416 | 0.204 | 0.9823 | BASELINE/CANDIDATE |

## 3. Final Champion Performance (Unbiased Test Partition)
| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **Test MAE** | 0.2138 | Average absolute deviation in CGPA points |
| **Test MSE** | 0.0672 | Mean squared error penalty |
| **Test RMSE** | 0.2593 | Root mean squared error in CGPA units |
| **Test R²** | 0.9707 | Proportion of CGPA variance explained |

## 4. Model Selection Rationale
> Selected 'LinearRegression' because it achieved the lowest Validation RMSE (0.1926) and Validation MAE (0.1515) with R² of 0.9843.

## 5. Feature Importance / Interpretability
*(Note: Feature importance indicates which pre-exam features were most influential to this model; it does not imply direct causation.)*

| Feature | Importance / Weight |
| :--- | :--- |
| `academic_average` | 15.0479 |
| `mid_term_average` | 12.7005 |
| `mid_2` | -12.4715 |
| `mid_1` | -11.9466 |
| `internal_marks` | -2.575 |
| `internal_average` | -2.575 |
| `previous_cgpa` | 1.0466 |
| `backlogs` | -0.2307 |
| `attendance_risk_score` | 0.1311 |
| `enc_department_code_MECH` | -0.0954 |