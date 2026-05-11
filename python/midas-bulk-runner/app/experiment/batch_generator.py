import os
import random
from pathlib import Path
import time


from midas_civil import *

from experiment.cases.single_span_post_tensioned_beam import SingleSpanPostTensionedBeam
from experiment.cases.single_span_beam import SingleSpanBeam
from experiment.cases.two_span_post_tensioned_beam import TwoSpanPostTensionedBeam
from experiment.result_collector import ResultCollector
from experiment.writers.csv_writer import CsvWriter

import config as app_config
from experiment.experiment_config import ExperimentConfig, Model_Type


class BatchGenerator:
    def __init__(self, experiment_config: ExperimentConfig):
        self.config = experiment_config
        self.config.validate()
        self.rng = random.Random(self.config.random_seed)
        self.results_writer = CsvWriter(self.config.output_csv_path)
        self.result_collector = ResultCollector(self.config)

        match self.config.model_type:
            case Model_Type.SINGLE_SPAN_BEAM:
                self.model_generator = SingleSpanBeam(
                    config=self.config.model_config,
                    rng=self.rng,
                )
            case Model_Type.SINGLE_SPAN_POST_TENSIONED_BEAM:
                self.model_generator = SingleSpanPostTensionedBeam(
                    config=self.config.model_config,
                    rng=self.rng,
                )
            case Model_Type.TWO_SPAN_POST_TENSIONED_BEAM:
                self.model_generator = TwoSpanPostTensionedBeam(
                    config=self.config.model_config,
                    rng=self.rng,
                )
            case Model_Type.FIXED_PARAMS_TWO_SPAN_POST_TENSIONED_BEAM:
                self.model_generator = TwoSpanPostTensionedBeam(
                    config=self.config.model_config,
                    rng=self.rng,
                )
            case _:
                raise ValueError(f"Unsupported model_type: {self.config.model_type}")

    # def run(self) -> None:
    #     self._initialize_midas()
    #     self._ensure_output_dir()

    #     for i in range(1, self.config.n_models + 1):
    #         print(f"\n--- Generating model {i}/{self.config.n_models} ---")

    #         try:
    #             self._reset_model_if_possible()

    #             sampled = self.model_generator.sample_parameters()
    #             model_meta = self.model_generator.build_model(sampled)

    #             Model.create()

    #             model_file_path = self._build_model_file_path(i)
    #             print(f"Saving MIDAS model to: {model_file_path}")
    #             Model.saveAs(str(model_file_path))

    #             Model.analyse()

    #             results = self._collect_results_with_retry(model_meta)
    #             status = "OK"
    #             error_message = ""

    #         except Exception as ex:
    #             sampled = {}
    #             results = {name: None for name in self.config.results_to_save}
    #             status = "ERROR"
    #             error_message = str(ex)
    #             print(f"Model {i} failed: {ex}")

    #         row = {}

    #         row["model_index"] = i

    #         if self.config.save_inputs:
    #             row.update(sampled)

    #         row.update(results)

    #         if self.config.save_analysis_status:
    #             row["analysis_status"] = status
    #             row["error_message"] = error_message

    #         self.results_writer.write_row(row)

    #     print(f"\nDone. Dataset saved to: {self.config.output_csv_path}")
    def run(self) -> None:
        self._initialize_midas()
        self._ensure_output_dir()

        i = 1

        print("\nInfinite generation started.")
        print("Press Ctrl+C to stop safely and save results.\n")

        try:
            while True:
                print(f"\n--- Generating model {i} ---")

                sampled = {}

                try:
                    self._reset_model_if_possible()

                    sampled = self.model_generator.sample_parameters()
                    model_meta = self.model_generator.build_model(sampled)

                    Model.create()

                    model_file_path = self._build_model_file_path(i)
                    print(f"Saving MIDAS model to: {model_file_path}")
                    Model.saveAs(str(model_file_path))

                    Model.analyse()

                    results = self.result_collector.collect(model_meta)
                    status = "OK"
                    error_message = ""

                except Exception as ex:
                    results = {name: None for name in self.config.results_to_save}
                    status = "ERROR"
                    error_message = str(ex)
                    print(f"Model {i} failed: {ex}")

                row = {}

                row["model_index"] = i

                if self.config.save_inputs:
                    row.update(sampled)

                row.update(results)

                if self.config.save_analysis_status:
                    row["analysis_status"] = status
                    row["error_message"] = error_message

                # zapisujemy TYLKO aktualny wiersz
                self.results_writer.write_row(row)

                i += 1

        except KeyboardInterrupt:
            print("\nStopping generation...")

        finally:
            print(f"\nDone. Dataset saved to: {self.config.output_csv_path}")

    def _initialize_midas(self) -> None:
        app_config.validate_config()
        MAPI_KEY(app_config.MIDAS_MAPI_KEY)
        MAPI_BASEURL(app_config.MIDAS_BASE_URL)
    def _collect_results_with_retry(self, model_meta: dict, retries: int = 3, delay_s: int = 5) -> dict:
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