from pathlib import Path
from datetime import datetime

from model_inputs.configs.experiment_config import ExperimentConfig, Model_Type
from model_inputs.input_batch_generator import InputBatchGenerator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    run_dir = PROJECT_ROOT / "python" / "model_inputs" / "prepared_inputs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    input_path = run_dir / "input.csv"

    cfg = ExperimentConfig(
        n_models=10,
        model_type=Model_Type.TWO_SPAN_POST_TENSIONED_BEAM,
        random_seed=None,
        save_inputs=True,
        save_analysis_status=False,
        results_to_save=["deflections_dz"],
        output_csv_path=str(input_path),
        output_model_dir=str(run_dir),
    )

    generator = InputBatchGenerator(cfg)
    generator.run()


if __name__ == "__main__":
    main()