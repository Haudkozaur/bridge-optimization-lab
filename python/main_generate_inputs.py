from pathlib import Path
from datetime import datetime

from common.model_types import Model_Type
from model_inputs.configs.experiment_inputs_config import ExperimentInputsConfig
from model_inputs.input_batch_generator import InputBatchGenerator

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    run_dir = PROJECT_ROOT / "python" / "model_inputs" / "prepared_inputs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    input_path = run_dir / "input.csv"

    cfg = ExperimentInputsConfig(
        n_models=100, 
        model_type=Model_Type.MULTI_SPAN_BEAM,
        random_seed=None,
        input_csv_path=str(input_path),
    )

    generator = InputBatchGenerator(cfg)
    generator.run()


if __name__ == "__main__":
    main()