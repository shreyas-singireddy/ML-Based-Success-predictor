"""
End-to-End ML Data Engineering and Preprocessing Pipeline Orchestrator.

Orchestrates:
Raw Dataset -> Validation -> Quality Report -> Cleaning -> Feature Engineering
-> Split (Temporal/Group) -> Training-Only Fitting -> Transformed Datasets
-> Serialized Preprocessor Artifact + Metadata + Leakage Audit.
"""

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from ml.config.pipeline_config import (
    DEFAULT_CONFIG,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    REGISTRY_DIR,
    REPORTS_DIR,
    PipelineConfig,
)
from ml.pipelines.ingestion import load_canonical_csv, generate_manifest
from ml.pipelines.validation import DataValidator
from ml.pipelines.quality_reporter import DataQualityReporter
from ml.pipelines.cleaning import DataCleaner
from ml.pipelines.engineering import FeatureEngineer, FEATURE_CATALOG
from ml.pipelines.splitter import get_dataset_splitter, SplitResult
from ml.pipelines.preprocessor import AcademicPreprocessor


class MLDataPipeline:
    """End-to-end reproducible data engineering and preprocessing pipeline."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.validator = DataValidator()
        self.reporter = DataQualityReporter(self.config.reports_dir)
        self.cleaner = DataCleaner(self.config)
        self.engineer = FeatureEngineer(self.config)
        self.splitter = get_dataset_splitter(self.config)
        self.preprocessor = AcademicPreprocessor(self.config)

    def run(
        self,
        raw_df: pd.DataFrame,
        source_name: str = "Academic_Benchmark",
        source_path: str = "ml/data/raw/academic_records_benchmark.csv",
    ) -> Dict[str, Any]:
        """Executes the full pipeline and saves all artifacts and reports."""
        start_time = datetime.now(timezone.utc)
        print(f"[{start_time.strftime('%H:%M:%S')}] Starting ML Data Engineering Pipeline for '{source_name}'...")

        # 1. Validation
        print("  -> Step 1/7: Validating schema and numeric ranges...")
        validation_result = self.validator.validate(raw_df)
        print(f"     Validation result: {'PASSED' if validation_result.is_valid else 'ISSUES DETECTED'} ({validation_result.valid_records_count}/{validation_result.total_records} valid)")

        # 2. Cleaning & Imputation
        print("  -> Step 2/7: Cleaning records, deduplicating, and domain clipping...")
        cleaned_df, cleaning_meta = self.cleaner.clean(raw_df, is_training=True)
        print(f"     Cleaned dataset: {len(cleaned_df)} rows retained ({cleaning_meta.exact_duplicates_removed} exact dups, {cleaning_meta.logical_duplicates_resolved} logical dups, {cleaning_meta.missing_target_rows_removed} missing targets dropped)")

        # 3. Data Quality Reporting
        print("  -> Step 3/7: Generating Data Quality Report (JSON + Markdown)...")
        quality_report = self.reporter.generate_report(
            raw_df=raw_df,
            cleaned_df=cleaned_df,
            validation_result=validation_result,
            rows_removed_count=cleaning_meta.initial_row_count - cleaning_meta.final_row_count,
        )

        # 4. Feature Engineering
        print("  -> Step 4/7: Engineering 7 domain features with strict temporal sorting...")
        featured_df = self.engineer.transform(cleaned_df)
        print(f"     Engineered features created. Total columns: {len(featured_df.columns)}")

        # 5. Dataset Splitting (Temporal or Group)
        print(f"  -> Step 5/7: Partitioning dataset using strategy '{self.config.split_strategy}'...")
        split_result = self.splitter.split(featured_df)
        print(f"     Split summary: Train={split_result.train_count} ({split_result.train_percentage}%), Val={split_result.val_count} ({split_result.val_percentage}%), Test={split_result.test_count} ({split_result.test_percentage}%)")

        # 6. Preprocessing: Fit strictly on X_train, transform Val/Test
        print("  -> Step 6/7: Fitting Preprocessor strictly on Train split...")
        X_train, y_train = self.preprocessor.extract_features_and_target(split_result.train_df)
        X_val, y_val = self.preprocessor.extract_features_and_target(split_result.val_df)
        X_test, y_test = self.preprocessor.extract_features_and_target(split_result.test_df)

        self.preprocessor.fit(X_train)
        X_train_trans = self.preprocessor.transform(X_train)
        X_val_trans = self.preprocessor.transform(X_val)
        X_test_trans = self.preprocessor.transform(X_test)

        # Attach targets to transformed data for storage
        train_processed = X_train_trans.copy()
        if y_train is not None:
            train_processed["target_cgpa"] = y_train.values
            
        val_processed = X_val_trans.copy()
        if y_val is not None:
            val_processed["target_cgpa"] = y_val.values
            
        test_processed = X_test_trans.copy()
        if y_test is not None:
            test_processed["target_cgpa"] = y_test.values

        # 7. Save Processed Datasets, Preprocessor Artifacts & Audit Reports
        print("  -> Step 7/7: Saving output datasets, preprocessor artifact, and leakage audit...")
        self.config.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.config.registry_dir.mkdir(parents=True, exist_ok=True)
        self.config.reports_dir.mkdir(parents=True, exist_ok=True)

        # Datasets
        train_csv_path = self.config.processed_data_dir / "train.csv"
        val_csv_path = self.config.processed_data_dir / "val.csv"
        test_csv_path = self.config.processed_data_dir / "test.csv"
        cleaned_csv_path = self.config.processed_data_dir / "cleaned_dataset.csv"

        train_processed.to_csv(train_csv_path, index=False)
        val_processed.to_csv(val_csv_path, index=False)
        test_processed.to_csv(test_csv_path, index=False)
        featured_df.to_csv(cleaned_csv_path, index=False)

        try:
            train_processed.to_parquet(self.config.processed_data_dir / "train.parquet", index=False)
            val_processed.to_parquet(self.config.processed_data_dir / "val.parquet", index=False)
            test_processed.to_parquet(self.config.processed_data_dir / "test.parquet", index=False)
        except Exception:
            # Parquet optional fallback
            pass

        # Save preprocessor artifact
        joblib_path = self.preprocessor.save(self.config.registry_dir / "preprocessor.joblib")

        # Save Dataset Manifest
        manifest = generate_manifest(
            df=raw_df,
            source_name=source_name,
            source_type="CSV",
            source_path=source_path,
            output_dir=self.config.reports_dir,
        )

        # Perform & Save Leakage Audit Report
        leakage_report = self._perform_leakage_audit(
            X_train=X_train,
            X_train_trans=X_train_trans,
            split_result=split_result,
        )
        with open(self.config.reports_dir / "leakage_audit_report.json", "w", encoding="utf-8") as f:
            json.dump(leakage_report, f, indent=2)

        end_time = datetime.now(timezone.utc)
        duration_sec = round((end_time - start_time).total_seconds(), 2)
        print(f"[SUCCESS] Pipeline completed successfully in {duration_sec}s.")

        return {
            "status": "SUCCESS",
            "duration_seconds": duration_sec,
            "raw_records": len(raw_df),
            "cleaned_records": len(cleaned_df),
            "train_records": len(train_processed),
            "val_records": len(val_processed),
            "test_records": len(test_processed),
            "transformed_features_count": len(X_train_trans.columns),
            "artifacts": {
                "preprocessor_joblib": str(joblib_path),
                "feature_metadata": str(self.config.registry_dir / "feature_metadata.json"),
                "train_csv": str(train_csv_path),
                "val_csv": str(val_csv_path),
                "test_csv": str(test_csv_path),
                "quality_report_md": str(self.config.reports_dir / "data_quality_report.md"),
                "leakage_report_json": str(self.config.reports_dir / "leakage_audit_report.json"),
                "manifest_json": str(self.config.reports_dir / "dataset_manifest.json"),
            },
        }

    def _perform_leakage_audit(
        self,
        X_train: pd.DataFrame,
        X_train_trans: pd.DataFrame,
        split_result: SplitResult,
    ) -> Dict[str, Any]:
        """Performs programmatic verification of target and temporal leakage."""
        forbidden_in_X = ["semester_cgpa", "grade", "risk_level"]
        target_leakage_found = [col for col in forbidden_in_X if col in X_train.columns]
        transformed_leakage_found = [col for col in forbidden_in_X if any(col in feat for feat in X_train_trans.columns)]

        audit_table = []
        for feat_name, meta in FEATURE_CATALOG.items():
            audit_table.append({
                "feature": feat_name,
                "source": ", ".join(meta.source_columns),
                "available_at_prediction_time": meta.availability_time,
                "leakage_risk": meta.leakage_risk,
                "status": "PASS" if meta.leakage_risk in ["None", "Target/Future Leakage Protected"] else "FAIL",
            })

        return {
            "audit_title": "Phase 2 — ML Preprocessing Data Leakage Audit",
            "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "target_leakage_in_X": len(target_leakage_found) == 0,
            "target_leakage_in_transformed": len(transformed_leakage_found) == 0,
            "student_crossover_in_splits": split_result.student_crossover_detected == 0,
            "temporal_violations_in_splits": split_result.temporal_violations_detected == 0,
            "overall_audit_status": "PASS" if len(target_leakage_found) == 0 and len(transformed_leakage_found) == 0 else "FAIL",
            "feature_audit_matrix": audit_table,
        }


def main():
    parser = argparse.ArgumentParser(description="Run Phase 2 ML Data Engineering Pipeline")
    parser.add_argument("--input", type=str, default=str(RAW_DATA_DIR / "academic_records_benchmark.csv"), help="Path to raw dataset CSV")
    parser.add_argument("--strategy", type=str, choices=["student_temporal", "student_group"], default="student_temporal", help="Dataset split strategy")
    args = parser.parse_args()

    config = PipelineConfig(split_strategy=args.strategy)
    pipeline = MLDataPipeline(config)
    
    df = load_canonical_csv(args.input)
    pipeline.run(raw_df=df, source_name="Benchmark_Academic_Cohort", source_path=args.input)


if __name__ == "__main__":
    main()
