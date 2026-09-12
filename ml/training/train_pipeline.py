"""
ML Training CLI Pipeline for Phase 3.

Loads Phase 2 processed datasets (train.csv, val.csv, test.csv) and executes ModelTrainingEngine.
"""

import argparse
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from ml.config.pipeline_config import DEFAULT_CONFIG, PROCESSED_DATA_DIR, PipelineConfig
from ml.training.trainer import ModelTrainingEngine


def main():
    parser = argparse.ArgumentParser(description="Train and Evaluate CGPA Regression Models")
    parser.add_argument("--data-dir", type=str, default=str(PROCESSED_DATA_DIR), help="Directory containing processed datasets")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    train_path = data_dir / "train.csv"
    val_path = data_dir / "val.csv"
    test_path = data_dir / "test.csv"

    if not train_path.exists() or not val_path.exists() or not test_path.exists():
        print(f"Error: Processed dataset files missing in {data_dir}. Run Phase 2 pipeline first.")
        sys.exit(1)

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    target_col = "target_cgpa"
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]

    X_val = val_df.drop(columns=[target_col])
    y_val = val_df[target_col]

    X_test = test_df.drop(columns=[target_col])
    y_test = test_df[target_col]

    trainer = ModelTrainingEngine()
    result = trainer.train_and_evaluate_all(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
    )
    print("\nTraining summary:")
    print(f"Champion Model: {result['champion_model']}")
    print(f"Validation Metrics: {result['val_metrics']}")
    print(f"Test Metrics: {result['test_metrics']}")


if __name__ == "__main__":
    main()
