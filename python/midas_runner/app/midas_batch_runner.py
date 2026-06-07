import os
from pathlib import Path
import random
import time
import shutil

from midas_civil import *

from common.io.csv_reader import CsvReader
from common.io.csv_writer import CsvWriter

from common.model_types import Model_Type
from configs.midas_run_config import MidasRunConfig


from model_inputs.generators.two_span_post_tensioned_input_generator import (
    TwoSpanPostTensionedInputGenerator,
)
from model_inputs.generators.multi_span_beam_input_generator import (
    MultiSpanBeamInputGenerator,
)

from model_inputs.configs.experiment_inputs_config import (
    TwoSpanPostTensionedBeamConfig,
    MultiSpanBeamConfig,
)

from midas_runner.builders.two_span_post_tensioned_midas_builder import (
    TwoSpanPostTensionedMidasBuilder,
)
from midas_runner.builders.multi_span_beam_midas_builder import (
    MultiSpanBeamMidasBuilder,
)

from midas_runner.app.result_collector import ResultCollector
from midas_runner.app.api_config import config as app_config



class MidasBatchRunner:
    def __init__(self, config: MidasRunConfig, input_csv_path: str):
        self.config = config
        self.config.validate()

        self.input_csv_path = input_csv_path
        self.rng = random.Random(self.config.random_seed)

        match self.config.model_type:
            case Model_Type.TWO_SPAN_POST_TENSIONED_BEAM:
                model_config = TwoSpanPostTensionedBeamConfig()

                self.input_generator = TwoSpanPostTensionedInputGenerator(
                    config=model_config,
                    rng=self.rng,
                )

                self.model_builder = TwoSpanPostTensionedMidasBuilder(
                    config=model_config,
                    rng=self.rng,
                )

            case Model_Type.MULTI_SPAN_BEAM:
                model_config = MultiSpanBeamConfig()

                self.input_generator = MultiSpanBeamInputGenerator(
                    config=model_config,
                    rng=self.rng,
                )

                self.model_builder = MultiSpanBeamMidasBuilder(
                    config=model_config,
                    rng=self.rng,
                )

            case _:
                raise ValueError(f"Unsupported model_type: {self.config.model_type}")

        self.max_node_id = self.input_generator.get_max_node_id()
        self.max_support_count = self.input_generator.get_max_support_count()
        input_columns = self.input_generator.input_field_order()

        self.input_reader = CsvReader(self.input_csv_path)
        self.results_writer = CsvWriter(
            self.config.output_csv_path,
            max_node_id=self.max_node_id,
            max_support_count=self.max_support_count,
            input_columns=input_columns,
        )
        self.result_collector = ResultCollector(self.config)

    def run(self) -> None:
        self._initialize_midas()
        self._ensure_output_dir()
        self._copy_input_csv_to_output_dir()

        for row_index, sampled in enumerate(self.input_reader.iter_rows(), start=1):
            model_index = int(sampled.get("model_index") or row_index)

            print(f"\n--- Running MIDAS model {model_index} ---")

            try:
                self._reset_model_if_possible()

                sampled = self._cleanup_sampled_row(sampled)
                model_meta = self.model_builder.build_model(sampled)

                Model.create()

                model_file_path = self._build_model_file_path(model_index)
                print(f"Saving MIDAS model to: {model_file_path}")
                Model.saveAs(str(model_file_path))

                Model.analyse()

                results = self._collect_results_with_retry(model_meta)
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

        print(f"\nDone. MIDAS results saved to: {self.config.output_csv_path}")

    def _copy_input_csv_to_output_dir(self) -> None:
        input_copy_path = Path(self.config.output_model_dir) / "input_used.csv"

        if not input_copy_path.exists():
            shutil.copy2(self.input_csv_path, input_copy_path)

    def _cleanup_sampled_row(self, row: dict) -> dict:
        out = dict(row)
        return out

    def _initialize_midas(self) -> None:
        app_config.validate_config()
        MAPI_KEY(app_config.MIDAS_MAPI_KEY)
        MAPI_BASEURL(app_config.MIDAS_BASE_URL)

    def _collect_results_with_retry(
        self,
        model_meta: dict,
        retries: int = 3,
        delay_s: int = 5,
    ) -> dict:
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                return self.result_collector.collect(model_meta)
            except Exception as ex:
                last_error = ex
                print(f"Result collection failed ({attempt}/{retries}): {ex}")

                if attempt < retries:
                    time.sleep(delay_s)

        raise last_error

    def _ensure_output_dir(self) -> None:
        csv_dir = os.path.dirname(self.config.output_csv_path)
        if csv_dir:
            os.makedirs(csv_dir, exist_ok=True)

        if self.config.output_model_dir:
            os.makedirs(self.config.output_model_dir, exist_ok=True)

    def _build_model_file_path(self, model_index: int) -> Path:
        return Path(self.config.output_model_dir) / f"model_{model_index:04d}.mcb"

    def _reset_model_if_possible(self) -> None:
        try:
            Model.close()
        except Exception:
            pass

        try:
            Model.new()
        except Exception:
            pass

        try:
            Model.clear()
        except Exception:
            pass

        Model.units(force="KN", length="M")
        Model.type()