import os
from random import Random

from common.io.csv_reader import CsvReader
from common.io.csv_writer import CsvWriter
from common.model_types import Model_Type

from model_inputs.configs.experiment_inputs_config import (
    TwoSpanPostTensionedBeamConfig,
    MultiSpanBeamConfig,
)

from model_inputs.generators.multi_span_beam_input_generator import (
    MultiSpanBeamInputGenerator,

)
from model_inputs.generators.two_span_post_tensioned_input_generator import (
    TwoSpanPostTensionedInputGenerator,
)
from solver_runner.opensees.multi_span_opensees_solver import (
    MultiSpanOpenSeesSolver,
)

from solver_runner.configs.solver_run_config import SolverRunConfig
from solver_runner.opensees.two_span_opensees_solver import TwoSpanOpenSeesSolver


class SolverBatchRunner:
    def __init__(self, config: SolverRunConfig, input_csv_path: str):
        self.config = config
        self.config.validate()

        self.input_csv_path = input_csv_path

        match self.config.model_type:
            case Model_Type.TWO_SPAN_POST_TENSIONED_BEAM:
                schema_helper = TwoSpanPostTensionedInputGenerator(
                    config=TwoSpanPostTensionedBeamConfig(),
                    rng=Random(0),
                )
                self.solver = TwoSpanOpenSeesSolver()

            case Model_Type.MULTI_SPAN_BEAM:
                schema_helper = MultiSpanBeamInputGenerator(
                    config=MultiSpanBeamConfig(),
                    rng=Random(0),
                )
                self.solver = MultiSpanOpenSeesSolver()

            case _:
                raise ValueError(f"Unsupported model_type: {self.config.model_type}")

        self.max_node_id = schema_helper.get_max_node_id()
        self.max_support_count = schema_helper.get_max_support_count()
        input_columns = schema_helper.input_field_order()

        self.input_reader = CsvReader(self.input_csv_path)
       
        self.results_writer = CsvWriter(
            self.config.output_csv_path,
            max_node_id=self.max_node_id,
            max_support_count=self.max_support_count,
            input_columns=input_columns,
        )

    def run(self) -> None:
        self._ensure_output_dir()

        for row_index, sampled in enumerate(self.input_reader.iter_rows(), start=1):
            model_index = int(sampled.get("model_index") or row_index)

            print(f"--- Running OpenSees solver model {model_index} ---")

            try:
                results = self.solver.solve(sampled)
                status = "OK"
                error_message = ""

            except Exception as ex:
                results = {name: None for name in self.config.results_to_save}
                status = "ERROR"
                error_message = str(ex)
                print(f"Model {model_index} failed: {ex}")

            out_row = {}

            if self.config.save_inputs:
                out_row.update(sampled)

            out_row.update(results)

            if self.config.save_analysis_status:
                out_row["analysis_status"] = status
                out_row["error_message"] = error_message

            self.results_writer.write_row(out_row)

        print(f"\nDone. Solver results saved to: {self.config.output_csv_path}")

    def _ensure_output_dir(self) -> None:
        csv_dir = os.path.dirname(self.config.output_csv_path)

        if csv_dir:
            os.makedirs(csv_dir, exist_ok=True)

        if self.config.output_model_dir:
            os.makedirs(self.config.output_model_dir, exist_ok=True)