from pathlib import Path
from datetime import datetime

from experiment.experiment_config import ExperimentConfig, Model_Type
from experiment.batch_generator import BatchGenerator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():

    # Getting paths and timpestamp to save models and results in a unique directory for each run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = PROJECT_ROOT / "models_data" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "results.csv"


    # DEFINE EXPERIMENT CONFIGURATION HERE
    cfg = ExperimentConfig(
        
        n_models=100, # number of models to generate
        model_type=Model_Type.FIXED_PARAMS_TWO_SPAN_POST_TENSIONED_BEAM, # type of model to generate
        random_seed=None, # random seed for reproducibility, use same seed to get same results, use None for random seed
        save_inputs=True, # whether to save input parameters in the output csv
        save_analysis_status=True, # whether to save analysis status (OK/ERROR) in the output csv
        results_to_save=[
            "deflections_dz",
            "moments_my",
            "reactions_fz",

            # "mid_deflection_sw",
            # "mid_deflection_udl",
            # "mid_deflection_ps",
            # "mid_deflection_ts",
            # "mid_deflection_total",

            # "left_reaction_sw",
            # "left_reaction_udl",
            # "left_reaction_ps",
            # "left_reaction_ts",
            # "left_reaction_total",

            # "right_reaction_sw",
            # "right_reaction_udl",
            # "right_reaction_ps",
            # "right_reaction_ts",
            # "right_reaction_total",

            # "support_reaction_total_sw",
            # "support_reaction_total_udl",
            # "support_reaction_total_ps",
            # "support_reaction_total_ts",
            # "support_reaction_total_fz",

            # "mid_moment_sw",
            # "mid_moment_udl",
            # "mid_moment_ps",
            # "mid_moment_ts",
            # "mid_moment_total",
        ], # results to save in the output csv.

        # Paths to save results and models - these will be created in a unique directory for each run based on timestamp
        output_csv_path=str(output_path), # here path with name of csv file is expected, default is "models_data/results.csv"
        output_model_dir=str(run_dir), # here path to directory is expected, default is "models_data"
    )
    generator = BatchGenerator(cfg)
    generator.run()


if __name__ == "__main__":
    main()