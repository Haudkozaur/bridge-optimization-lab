import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PYTHON_ROOT))

from datetime import datetime

from common.model_types import Model_Type
from configs.midas_run_config import MidasRunConfig

from midas_runner.app.midas_batch_runner import MidasBatchRunner


def main():
    input_csv_path = (
        PYTHON_ROOT
        / "model_inputs"
        / "prepared_inputs"
        / "20260605_181003"
        / "input.csv"
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    run_dir = (
        PYTHON_ROOT
        / "model_outputs"
        / "models_data"
        / f"midas_run_{timestamp}"
    )

    run_dir.mkdir(parents=True, exist_ok=True)

    output_path = run_dir / "midas_output.csv"

    cfg = MidasRunConfig(
        model_type=Model_Type.MULTI_SPAN_BEAM,
        save_inputs=True,
        save_analysis_status=True,
        results_to_save=[
            "deflections_dz",
            "moments_my",
            "reactions_fz",
        ],
        output_csv_path=str(output_path),
        output_model_dir=str(run_dir),
    )

    runner = MidasBatchRunner(
        config=cfg,
        input_csv_path=str(input_csv_path),
    )

    runner.run()


if __name__ == "__main__":
    main()