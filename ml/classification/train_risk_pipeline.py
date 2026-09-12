"""
CLI Runner for AI Academic Risk Model Training Pipeline.

Loads Phase 2 processed datasets (train.csv, val.csv, test.csv) and executes RiskTrainingEngine.
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
from ml.classification.risk_trainer import RiskTrainingEngine


def main():
    parser = argparse.ArgumentParser(description="Train and Evaluate AI Academic Risk Classifiers")
    parser.add_argument("--data-dir", type=str, default=str(PROCESSED_DATA_DIR), help="Directory containing processed datasets")
    parser.add_argument("--min-high-recall", type=float, default=0.50, help="Minimum acceptable HIGH class recall")
    parser.add_argument("--min-critical-recall", type=float, default=0.50, help="Minimum acceptable CRITICAL class recall")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    cleaned_path = data_dir / "cleaned_dataset.csv"

    if not cleaned_path.exists():
        print(f"Error: Processed dataset cleaned_dataset.csv missing in {data_dir}. Run Phase 2 pipeline first.")
        sys.exit(1)

    cleaned_df = pd.read_csv(cleaned_path)

    trainer = RiskTrainingEngine(
        minimum_high_recall=args.min_high_recall,
        minimum_critical_recall=args.min_critical_recall,
    )
    result = trainer.train_and_evaluate_all(cleaned_df=cleaned_df)

    print("\n" + "=" * 50)
    print("PHASE 4 RISK CLASSIFICATION TRAINING SUMMARY")
    print("=" * 50)
    print(f"Status: {result['status']}")
    print(f"Champion Model: {result['champion_model']}")
    print(f"Validation Macro F1: {result['val_metrics']['macro_f1']}")
    print(f"Validation HIGH Recall: {result['val_metrics']['high_recall']}")
    print(f"Validation CRITICAL Recall: {result['val_metrics']['critical_recall']}")
    print(f"Test Macro F1: {result['test_metrics']['macro_f1']}")
    print(f"Test Accuracy: {result['test_metrics']['accuracy']}")
    print("Artifacts generated:")
    for k, v in result["artifacts"].items():
        print(f"  - {k}: {v}")


if __name__ == "__main__":
    main()
