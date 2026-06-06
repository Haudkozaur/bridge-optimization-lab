import random

from common.model_types import Model_Type
from model_inputs.configs.experiment_inputs_config import ExperimentInputsConfig
from model_inputs.generators.two_span_post_tensioned_input_generator import (
    TwoSpanPostTensionedInputGenerator,
)
from model_inputs.generators.multi_span_beam_input_generator import (
    MultiSpanBeamInputGenerator,
)
from common.io.csv_writer import CsvWriter


class InputBatchGenerator:
    def __init__(self, config: ExperimentInputsConfig):
        self.config = config
        self.config.validate()

        self.rng = random.Random(self.config.random_seed)
        self.writer = CsvWriter(self.config.input_csv_path)

        match self.config.model_type:
            case Model_Type.TWO_SPAN_POST_TENSIONED_BEAM:
                self.model_generator = TwoSpanPostTensionedInputGenerator(
                    config=self.config.model_config,
                    rng=self.rng,
                )

            case Model_Type.MULTI_SPAN_BEAM:
                self.model_generator = MultiSpanBeamInputGenerator(
                    config=self.config.model_config,
                    rng=self.rng,
                )

            case _:
                raise ValueError(
                    f"Input generation not supported yet for: {self.config.model_type}"
                )

    def run(self) -> None:
        rows = []

        for i in range(1, self.config.n_models + 1):
            sampled = self.model_generator.sample_parameters()

            row = {
                "model_index": i,
                "model_type": self.config.model_type.value,
            }
            row.update(sampled)

            rows.append(row)

        preferred_order = []

        if hasattr(self.model_generator, "input_field_order"):
            preferred_order = self.model_generator.input_field_order()

        self.writer.write_rows(
            rows,
            preferred_order=preferred_order,
        )

        print(f"Input CSV saved to: {self.config.input_csv_path}")
        print(f"Rows: {len(rows)}")