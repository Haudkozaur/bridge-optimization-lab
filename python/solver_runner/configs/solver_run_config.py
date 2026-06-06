from dataclasses import dataclass, field

from common.model_types import Model_Type


@dataclass
class SolverRunConfig:
    model_type: Model_Type = Model_Type.TWO_SPAN_POST_TENSIONED_BEAM

    output_csv_path: str = "solver_output.csv"
    output_model_dir: str = "models_data"

    save_inputs: bool = True
    save_analysis_status: bool = True

    results_to_save: list[str] = field(
        default_factory=lambda: [
            "deflections_dz",
            "moments_my",
            "reactions_fz",
        ]
    )

    def validate(self) -> None:
        if not self.output_csv_path or not self.output_csv_path.strip():
            raise ValueError("output_csv_path cannot be empty")

        if not self.output_model_dir or not self.output_model_dir.strip():
            raise ValueError("output_model_dir cannot be empty")

        if not isinstance(self.results_to_save, list):
            raise ValueError("results_to_save must be list[str]")

        if len(self.results_to_save) == 0:
            raise ValueError("results_to_save cannot be empty")