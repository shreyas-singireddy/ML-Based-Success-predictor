"""
Tests for Reproducibility and Determinism of the ML Pipeline.
"""

import hashlib
import pandas as pd
import pytest

from ml.config.pipeline_config import PipelineConfig, RAW_DATA_DIR
from ml.pipelines.ingestion import load_canonical_csv
from ml.pipelines.pipeline import MLDataPipeline


def test_pipeline_deterministic_reproducibility(tmp_path):
    benchmark_path = RAW_DATA_DIR / "academic_records_benchmark.csv"
    if not benchmark_path.exists():
        pytest.skip("Benchmark CSV not found.")

    raw_df = load_canonical_csv(benchmark_path)

    # Run 1
    dir1 = tmp_path / "run1"
    cfg1 = PipelineConfig(
        random_seed=42,
        processed_data_dir=dir1 / "data",
        registry_dir=dir1 / "registry",
        reports_dir=dir1 / "reports",
    )
    pipeline1 = MLDataPipeline(cfg1)
    res1 = pipeline1.run(raw_df, source_name="Benchmark", source_path=str(benchmark_path))

    # Run 2
    dir2 = tmp_path / "run2"
    cfg2 = PipelineConfig(
        random_seed=42,
        processed_data_dir=dir2 / "data",
        registry_dir=dir2 / "registry",
        reports_dir=dir2 / "reports",
    )
    pipeline2 = MLDataPipeline(cfg2)
    res2 = pipeline2.run(raw_df, source_name="Benchmark", source_path=str(benchmark_path))

    # Compare processed dataset CSV files
    train1 = pd.read_csv(dir1 / "data" / "train.csv")
    train2 = pd.read_csv(dir2 / "data" / "train.csv")
    pd.testing.assert_frame_equal(train1, train2)

    val1 = pd.read_csv(dir1 / "data" / "val.csv")
    val2 = pd.read_csv(dir2 / "data" / "val.csv")
    pd.testing.assert_frame_equal(val1, val2)

    test1 = pd.read_csv(dir1 / "data" / "test.csv")
    test2 = pd.read_csv(dir2 / "data" / "test.csv")
    pd.testing.assert_frame_equal(test1, test2)
