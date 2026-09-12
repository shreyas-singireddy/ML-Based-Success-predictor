"""
End-to-End Tests for ML Pipeline.
"""

from pathlib import Path
import pandas as pd
import pytest

from ml.config.pipeline_config import PipelineConfig, RAW_DATA_DIR
from ml.pipelines.ingestion import load_canonical_csv
from ml.pipelines.pipeline import MLDataPipeline


def test_pipeline_e2e_execution(tmp_path):
    benchmark_path = RAW_DATA_DIR / "academic_records_benchmark.csv"
    if not benchmark_path.exists():
        pytest.skip("Benchmark CSV not found.")

    raw_df = load_canonical_csv(benchmark_path)

    test_processed_dir = tmp_path / "processed"
    test_registry_dir = tmp_path / "registry"
    test_reports_dir = tmp_path / "reports"

    cfg = PipelineConfig(
        processed_data_dir=test_processed_dir,
        registry_dir=test_registry_dir,
        reports_dir=test_reports_dir,
    )

    pipeline = MLDataPipeline(cfg)
    result = pipeline.run(
        raw_df=raw_df,
        source_name="Benchmark_E2E_Test",
        source_path=str(benchmark_path),
    )

    assert result["status"] == "SUCCESS"
    assert (test_processed_dir / "train.csv").exists()
    assert (test_processed_dir / "val.csv").exists()
    assert (test_processed_dir / "test.csv").exists()
    assert (test_registry_dir / "preprocessor.joblib").exists()
    assert (test_registry_dir / "feature_metadata.json").exists()
    assert (test_reports_dir / "data_quality_report.md").exists()
    assert (test_reports_dir / "data_quality_report.json").exists()
    assert (test_reports_dir / "leakage_audit_report.json").exists()
    assert (test_reports_dir / "dataset_manifest.json").exists()
