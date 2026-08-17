from __future__ import annotations

import argparse
import configparser
import re
from datetime import datetime
from pathlib import Path

from common.model_types import Model_Type
from common.ranges import FloatRange, IntRange
from model_inputs.configs.experiment_inputs_config import (
    ExperimentInputsConfig,
    MultiSpanBeamConfig,
)
from model_inputs.input_batch_generator import InputBatchGenerator

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate multi-span beam inputs from a BridgeAppUI configuration file."
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--n-models", type=int, default=None)
    parser.add_argument("--random-seed", type=int, default=None)
    return parser.parse_args()


def read_config(path: Path) -> configparser.ConfigParser:
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    config = configparser.ConfigParser(interpolation=None)
    config.read(path, encoding="utf-8-sig")
    return config


def as_float(value: str) -> float:
    return float(value.strip().replace(",", "."))


def as_int(value: str) -> int:
    return int(float(value.strip().replace(",", ".")))


def leading_int(value: str) -> int:
    match = re.match(r"\s*(\d+)", value)
    if not match:
        raise ValueError(f"Expected a value beginning with an integer, got: {value!r}")
    return int(match.group(1))


def read_range(
    config: configparser.ConfigParser,
    section: str,
    name: str,
    range_type: type[IntRange] | type[FloatRange],
    converter,
):
    mode = config.get(section, f"{name}.mode").strip().lower()

    if mode == "fixed":
        value = converter(config.get(section, f"{name}.value"))
        return range_type("fixed", value)

    if mode == "random":
        minimum = converter(config.get(section, f"{name}.from"))
        maximum = converter(config.get(section, f"{name}.to"))
        return range_type("random", minimum, maximum)

    raise ValueError(f"Unsupported mode for {name}: {mode!r}")


def read_enum_range(
    config: configparser.ConfigParser,
    section: str,
    name: str,
    enum_type,
) -> tuple[IntRange, object | None]:
    mode = config.get(section, f"{name}.mode").strip().lower()

    if mode == "fixed":
        value = leading_int(config.get(section, f"{name}.value"))
        return IntRange("fixed", value), enum_type(value)

    if mode == "random":
        minimum = leading_int(config.get(section, f"{name}.from"))
        maximum = leading_int(config.get(section, f"{name}.to"))
        return IntRange("random", minimum, maximum), None

    raise ValueError(f"Unsupported mode for {name}: {mode!r}")


def build_multi_span_config(config: configparser.ConfigParser) -> MultiSpanBeamConfig:
    udl_randomizer, udl_type = read_enum_range(
        config,
        "LOADS",
        "udl_load_type",
        MultiSpanBeamConfig.UdlLoadType,
    )

    tendon_shape_randomizer, tendon_shape_type = read_enum_range(
        config,
        "TENDON",
        "tendon_shape_type",
        MultiSpanBeamConfig.TendonShapeType,
    )

    model_config = MultiSpanBeamConfig(
        n_spans=read_range(config, "GEOMETRY", "n_spans", IntRange, as_int),
        span_length_m=read_range(
            config, "GEOMETRY", "span_length_m", FloatRange, as_float
        ),
        beam_height_m=read_range(
            config, "GEOMETRY", "beam_height_m", FloatRange, as_float
        ),
        beam_width_m=read_range(
            config, "GEOMETRY", "beam_width_m", FloatRange, as_float
        ),
        udl_kn_per_m=read_range(
            config, "LOADS", "udl_kn_per_m", FloatRange, as_float
        ),
        udl_load_type_randomizer=udl_randomizer,
        udl_load_type=udl_type,
        self_weight_case=config.get("LOADS", "self_weight_case"),
        udl_case=config.get("LOADS", "udl_case"),
        prestress_case=config.get("LOADS", "prestress_case"),
        left_support=config.get("SUPPORTS", "left_support"),
        internal_support=config.get("SUPPORTS", "internal_support"),
        right_support=config.get("SUPPORTS", "right_support"),
        concrete_material_name=config.get(
            "MATERIALS_AND_SECTION", "concrete_material_name"
        ),
        concrete_material_code=config.get(
            "MATERIALS_AND_SECTION", "concrete_material_code"
        ),
        concrete_material_grade=config.get(
            "MATERIALS_AND_SECTION", "concrete_material_grade"
        ),
        tendon_material_name=config.get(
            "MATERIALS_AND_SECTION", "tendon_material_name"
        ),
        tendon_material_code=config.get(
            "MATERIALS_AND_SECTION", "tendon_material_code"
        ),
        tendon_material_grade=config.get(
            "MATERIALS_AND_SECTION", "tendon_material_grade"
        ),
        tendon_material_id=config.getint(
            "MATERIALS_AND_SECTION", "tendon_material_id"
        ),
        section_name=config.get("MATERIALS_AND_SECTION", "section_name"),
        section_id=config.getint("MATERIALS_AND_SECTION", "section_id"),
        outer_polygon=None,
        inner_polygons=[],
        n_tendons=read_range(config, "TENDON", "n_tendons", IntRange, as_int),
        tendon_force_kn=read_range(
            config, "TENDON", "tendon_force_kn", FloatRange, as_float
        ),
        tendon_area_mm2=read_range(
            config, "TENDON", "tendon_area_mm2", FloatRange, as_float
        ),
        tendon_cover_m=read_range(
            config, "TENDON", "tendon_cover_m", FloatRange, as_float
        ),
        tendon_control_points_per_span=config.getint(
            "TENDON", "tendon_control_points_per_span"
        ),
        tendon_shape_randomizer=tendon_shape_randomizer,
        tendon_shape_type=tendon_shape_type,
    )

    model_config.validate()
    return model_config


def get_optional_seed(
    config: configparser.ConfigParser,
    command_line_seed: int | None,
) -> int | None:
    if command_line_seed is not None:
        return command_line_seed

    value = config.get("RUN", "random_seed", fallback="None").strip()
    if value.lower() in {"", "none", "null"}:
        return None
    return as_int(value)


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = read_config(config_path)

    n_models = args.n_models
    if n_models is None:
        n_models = config.getint("RUN", "n_models", fallback=1_000_000)

    random_seed = get_optional_seed(config, args.random_seed)

    if args.output is not None:
        input_path = args.output.resolve()
        input_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = (
            PROJECT_ROOT
            / "python"
            / "model_inputs"
            / "prepared_inputs"
            / timestamp
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        input_path = run_dir / "input.csv"

    model_config = build_multi_span_config(config)

    experiment_config = ExperimentInputsConfig(
        n_models=n_models,
        model_type=Model_Type.MULTI_SPAN_BEAM,
        random_seed=random_seed,
        input_csv_path=str(input_path),
        model_config=model_config,
    )
    experiment_config.validate()

    print(f"Generating {n_models} models...")
    print(f"Configuration: {config_path}")
    print(f"Output: {input_path}")

    generator = InputBatchGenerator(experiment_config)
    generator.run()

    print(f"GENERATED_INPUT_PATH={input_path.resolve()}")


if __name__ == "__main__":
    main()