# ML Pipeline Phase 2 — Data Quality & Integrity Report

**Generated (UTC):** 2026-09-12T19:57:37.868393+00:00  
**Validation Status:** `VALID`  
**Total Records:** 715 | **Columns:** 16 | **Rows Retained:** 715 | **Rows Removed:** 0

## 1. Executive Summary Table
| Metric | Value | Status |
| :--- | :--- | :--- |
| Total Raw Rows | 715 | INFO |
| Exact Duplicates | 0 | VALID |
| Logical Duplicates (Student+Sem) | 0 | VALID |
| Total Validation Issues | 0 | VALID |
| Final Cleaned Rows Retained | 715 | VALID |

## 2. Column-Level Quality Metrics
| Column | Type | Missing Count | Missing % | Min | Mean | Max | IQR Outliers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `student_number` | `object` | 0 | 0.0% | - | - | - | 0 |
| `name` | `object` | 0 | 0.0% | - | - | - | 0 |
| `gender` | `object` | 0 | 0.0% | - | - | - | 0 |
| `age` | `int64` | 0 | 0.0% | 18.0 | 20.2 | 23.0 | 0 |
| `department_code` | `object` | 0 | 0.0% | - | - | - | 0 |
| `semester` | `int64` | 0 | 0.0% | 1.0 | 3.65 | 8.0 | 0 |
| `academic_year` | `object` | 0 | 0.0% | - | - | - | 0 |
| `attendance_percentage` | `float64` | 0 | 0.0% | 36.04 | 79.84 | 100.0 | 47 |
| `previous_cgpa` | `float64` | 0 | 0.0% | 3.4 | 7.21 | 9.8 | 10 |
| `mid_1` | `float64` | 0 | 0.0% | 22.61 | 72.59 | 100.0 | 15 |
| `mid_2` | `float64` | 0 | 0.0% | 19.65 | 72.62 | 100.0 | 6 |
| `internal_marks` | `float64` | 0 | 0.0% | 34.38 | 73.01 | 100.0 | 2 |
| `backlogs` | `int64` | 0 | 0.0% | 0.0 | 0.4 | 4.0 | 24 |
| `semester_cgpa` | `float64` | 0 | 0.0% | 3.1 | 7.15 | 10.0 | 26 |
| `grade` | `object` | 0 | 0.0% | - | - | - | 0 |
| `risk_level` | `object` | 0 | 0.0% | - | - | - | 0 |

## 3. Validation Issues & Actions
✓ No validation issues detected. All records comply with canonical domain constraints.