from dataclasses import dataclass, field

from common.model_types import Model_Type


@dataclass
class MidasRunConfig:
    model_type: Model_Type = Model_Type.MULTI_SPAN_BEAM
    random_seed: int | None = None

    output_csv_path: str = "midas_output.csv"
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

        allowed_results = {
            "deflections_dz",
            "moments_my",
            "reactions_fz",
        }

        invalid = [r for r in self.results_to_save if r not in allowed_results]
        if invalid:
            raise ValueError(
                f"Unsupported results_to_save: {invalid}. "
                f"Allowed values: {sorted(allowed_results)}"
            )

        if not isinstance(self.model_type, Model_Type):
            raise ValueError("model_type must be Model_Type")