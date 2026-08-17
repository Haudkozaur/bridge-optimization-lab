import sys
from pathlib import Path
from datetime import datetime

PYTHON_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PYTHON_ROOT))

from common.model_types import Model_Type
from solver_runner.configs.solver_run_config import SolverRunConfig
from solver_runner.app.solver_batch_runner import SolverBatchRunner


def main():
    # input_csv_path = (
    #     PYTHON_ROOT
    #     / "model_inputs"
    #     / "prepared_inputs"
    #     / "test"
    #     / "input.csv"
    # )
    # input_csv_path = (
    #     PYTHON_ROOT
    #     / "model_inputs"
    #     / "prepared_inputs"
    #     / "20260515_104115"
    #     / "input.csv"
    # 
    input_csv_path = (
        PYTHON_ROOT
        / "model_inputs"
        / "prepared_inputs"
        / "20260709_190958"
        / "input.csv"
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    run_dir = (
        PYTHON_ROOT
        / "model_outputs"
        / "models_data"
        / f"solver_run_{timestamp}"
    )

    run_dir.mkdir(parents=True, exist_ok=True)

    output_path = run_dir / "solver_output.csv"

    cfg = SolverRunConfig(
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

    runner = SolverBatchRunner(
        config=cfg,
        input_csv_path=str(input_csv_path),
    )

    runner.run()


if __name__ == "__main__":
    main()