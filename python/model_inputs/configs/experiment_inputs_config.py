from dataclasses import dataclass, field
from enum import Enum
from typing import Union

from common.ranges import FloatRange, IntRange
from common.model_types import Model_Type


# Configuration for cases

@dataclass
class MultiSpanBeamConfig:

    class TendonShapeType(Enum):
        FULL_RANDOM = 1

        FORCED_REASONABLE = 2

        FORCED_CONSTANT_SPANS = 3

        FORCED_REASONABLE_CONSTANT_SPANS = 4

        FORCED_REASONABLE_CONSTANT_SPANS_SYMMETRIC = 5

        FORCED_SYMMETRIC = 6

        FORCED_REASONABLE_SYMMETRIC = 7

    class UdlLoadType(Enum):
        TRUE_UDL = 1
        RANDOM_SPAN_UDL = 2
        RANDOM_UDL = 3
        RANDOM_SPAN_RANDOM_UDL = 4

        SYMMETRIC_RANDOM_SPAN_UDL = 5
        SYMMETRIC_RANDOM_UDL = 6

    n_spans: IntRange = field(default_factory=lambda: IntRange("random", 2, 10))
    span_length_m: FloatRange = field(default_factory=lambda: FloatRange("random", 8.0, 30.0))

    beam_height_m: FloatRange = field(default_factory=lambda: FloatRange("random", 0.75, 2.0))
    beam_width_m: FloatRange = field(default_factory=lambda: FloatRange("random", 0.4, 1.2))

    udl_kn_per_m: FloatRange = field(default_factory=lambda: FloatRange("random", 0.0, 15.0))
    udl_load_type_randomizer: IntRange = field(default_factory=lambda: IntRange("random", 1, 4))
    udl_load_type: UdlLoadType | None = None


    self_weight_case: str = "Self Weight"
    udl_case: str = "UDL"
    prestress_case: str = "Prestress"

    left_support: str = "111000"
    internal_support: str = "011000"
    right_support: str = "011000"

    concrete_material_name: str = "C40/50"
    concrete_material_code: str = "EN04(RC)"
    concrete_material_grade: str = "C40/50"

    tendon_material_name: str = "TD_steel"
    tendon_material_code: str = "IS(S)"
    tendon_material_grade: str = "E450"
    tendon_material_id: int = 1

    section_name: str = "PSC_RECT_VALUE"
    section_id: int = 2

    outer_polygon: list[tuple[float, float]] | None = None
    inner_polygons: list[list[tuple[float, float]]] = field(default_factory=list)

    n_tendons: IntRange = field(default_factory=lambda: IntRange("random", 1, 5))
    
    tendon_force_kn: FloatRange = field(default_factory=lambda: FloatRange("fixed", 220.0))
    tendon_area_mm2: FloatRange = field(default_factory=lambda: FloatRange("fixed", 150.0))

    tendon_cover_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 0.05))

    tendon_control_points_per_span: int = 5

    tendon_shape_randomizer: IntRange = field(default_factory=lambda: IntRange("random", 1, 7)) 
    tendon_shape_type: TendonShapeType | None = None

    def validate(self) -> None:
        self.n_spans.validate("n_spans")
        self.span_length_m.validate("span_length_m")

        self.beam_height_m.validate("beam_height_m")
        self.beam_width_m.validate("beam_width_m")

        self.udl_kn_per_m.validate("udl_kn_per_m")
        self.udl_load_type_randomizer.validate("udl_load_type_randomizer")

        self.n_tendons.validate("n_tendons")
        self.tendon_force_kn.validate("tendon_force_kn")
        self.tendon_area_mm2.validate("tendon_area_mm2")
        self.tendon_cover_m.validate("tendon_cover_m")

        if self.n_spans.min < 2:
            raise ValueError("n_spans.min must be >= 2 for MultiSpanBeamConfig")

        if self.span_length_m.min <= 0:
            raise ValueError("span_length_m must be > 0")

        if self.beam_height_m.min <= 0:
            raise ValueError("beam_height_m must be > 0")

        if self.beam_width_m.min <= 0:
            raise ValueError("beam_width_m must be > 0")

        if self.udl_kn_per_m.min < 0:
            raise ValueError("udl_kn_per_m must be >= 0")

        if self.n_tendons.min < 1:
            raise ValueError("n_tendons.min must be >= 1")

        if self.tendon_force_kn.min <= 0:
            raise ValueError("tendon_force_kn must be > 0")

        if self.tendon_area_mm2.min <= 0:
            raise ValueError("tendon_area_mm2 must be > 0")

        if self.tendon_cover_m.min < 0:
            raise ValueError("tendon_cover_m must be >= 0")

        if self.tendon_control_points_per_span != 5:
            raise ValueError(
                "Only tendon_control_points_per_span == 5 is currently supported"
            )

        if self.outer_polygon is not None and len(self.outer_polygon) < 3:
            raise ValueError("outer_polygon must contain at least 3 points")
        
        self.tendon_shape_randomizer.validate("tendon_shape_randomizer")

        if self.tendon_shape_randomizer.min < 1:
            raise ValueError("tendon_shape_randomizer.min must be >= 1")

        if self.tendon_shape_randomizer.max > 7:
            raise ValueError("tendon_shape_randomizer.max must be <= 7")

        if self.tendon_shape_type is not None and not isinstance(
            self.tendon_shape_type,
            self.TendonShapeType,
        ):
            raise ValueError("tendon_shape_type must be TendonShapeType or None")
        
        if self.udl_load_type_randomizer.min < 1:
            raise ValueError("udl_load_type_randomizer.min must be >= 1")

        if self.udl_load_type_randomizer.max > 6:
            raise ValueError("udl_load_type_randomizer.max must be <= 6")

        if self.udl_load_type is not None and not isinstance(
            self.udl_load_type,
            self.UdlLoadType,
        ):
            raise ValueError("udl_load_type must be UdlLoadType or None")

        
@dataclass
class TwoSpanPostTensionedBeamConfig:
    
    class TendonShapeType(Enum):
        RANDOM_TWO_SPAN = 1
        FORCED_REALISTIC_TWO_SPAN = 2
        FORCED_SYMMETRIC_TWO_SPAN = 3
        FORCED_REALISTIC_SYMMETRIC_TWO_SPAN = 4
    
    left_span_length_m: FloatRange = field(default_factory=lambda: FloatRange("random", 5.0, 30.0))
    right_span_length_m: FloatRange = field(default_factory=lambda: FloatRange("random", 5.0, 30.0))

    beam_height_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 1.0))
    beam_width_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 0.5))
    udl_kn_per_m: FloatRange = field(default_factory=lambda: FloatRange("random", 5.0, 10.0))

    concrete_material_name: str = "C40/50"
    concrete_material_code: str = "EN04(RC)"
    concrete_material_grade: str = "C40/50"

    tendon_material_name: str = "TD_steel"
    tendon_material_code: str = "IS(S)"
    tendon_material_grade: str = "E450"
    tendon_material_id: int = 1

    section_name: str = "PSC_RECT_VALUE"
    section_id: int = 2

    outer_polygon: list[tuple[float, float]] | None = None
    inner_polygons: list[list[tuple[float, float]]] = field(default_factory=list)

    left_support: str = "111000"
    middle_support: str = "011000"
    right_support: str = "011000"

    self_weight_case: str = "Self Weight"
    udl_case: str = "UDL"
    prestress_case: str = "Prestress"

    n_tendons: IntRange = field(default_factory=lambda: IntRange("fixed", 3))
    
    tendon_force_kn: FloatRange = field(default_factory=lambda: FloatRange("fixed", 220.0))
    tendon_area_mm2: FloatRange = field(default_factory=lambda: FloatRange("fixed", 150.0))

    tendon_ecc_left_m: FloatRange = None
    tendon_ecc_left_span_mid_m: FloatRange = None
    
    tendon_ecc_mid_support_m: FloatRange = None
    
    tendon_ecc_right_span_mid_m: FloatRange = None
    tendon_ecc_right_m: FloatRange = None
    
    # 1 - random two span, 2 - forced realistic two span, 3 - forced symetric two span, 4 - forced realistic symmetric two span
    tendon_shape_randomizer: IntRange = field(default_factory=lambda: IntRange("random", 1, 4)) 
    tendon_shape_type: TendonShapeType | None = None


    
    def validate(self) -> None:
        self.left_span_length_m.validate("left_span_length_m")
        self.right_span_length_m.validate("right_span_length_m")
        self.beam_height_m.validate("beam_height_m")
        self.beam_width_m.validate("beam_width_m")
        self.udl_kn_per_m.validate("udl_kn_per_m")

        self.n_tendons.validate("n_tendons")
        self.tendon_force_kn.validate("tendon_force_kn")
        self.tendon_area_mm2.validate("tendon_area_mm2")

        self.tendon_shape_randomizer.validate("tendon_shape_randomizer")

        if self.tendon_shape_randomizer.min < 1:
            raise ValueError("tendon_shape_randomizer.min must be >= 1")

        if self.tendon_shape_randomizer.max > 4:
            raise ValueError("tendon_shape_randomizer.max must be <= 4")

        if self.tendon_shape_type is not None and not isinstance(
            self.tendon_shape_type,
            self.TendonShapeType,
        ):
            raise ValueError("tendon_shape_type must be TendonShapeType or None")

        if self.outer_polygon is not None and len(self.outer_polygon) < 3:
            raise ValueError("outer_polygon must contain at least 3 points")


@dataclass
class FixedParamsTwoSpanPostTensionedBeamConfig(TwoSpanPostTensionedBeamConfig):
    left_span_length_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 20.0))
    right_span_length_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 20.0))

    beam_height_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 1.0))
    beam_width_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 0.5))
    udl_kn_per_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 10.0))

    n_tendons: IntRange = field(default_factory=lambda: IntRange("fixed", 3))
    tendon_force_kn: FloatRange = field(default_factory=lambda: FloatRange("fixed", 220.0))
    tendon_area_mm2: FloatRange = field(default_factory=lambda: FloatRange("fixed", 150.0))

    tendon_ecc_left_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 0.00))
    tendon_ecc_left_span_mid_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", -0.45))
    tendon_ecc_mid_support_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 0.45))
    tendon_ecc_right_span_mid_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", -0.45))
    tendon_ecc_right_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 0.00))

    tendon_shape_randomizer: IntRange = field(default_factory=lambda: IntRange("fixed", 2))
    tendon_shape_type: TwoSpanPostTensionedBeamConfig.TendonShapeType = (
        TwoSpanPostTensionedBeamConfig.TendonShapeType.FORCED_REALISTIC_TWO_SPAN
    )
@dataclass
class SingleSpanPostTensionedBeamConfig:
    span_length_m: FloatRange = field(default_factory=lambda: FloatRange("random", 8.0, 12.0))
    beam_height_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 0.8))
    beam_width_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 0.4))
    udl_kn_per_m: FloatRange = field(default_factory=lambda: FloatRange("random", 5.0, 10.0))
    beam_divisions: IntRange = field(default_factory=lambda: IntRange("random", 10, 16))

    ts_left_force_kn: FloatRange = field(default_factory=lambda: FloatRange("fixed", 70.0))
    ts_right_force_kn: FloatRange = field(default_factory=lambda: FloatRange("fixed", 70.0))
    ts_spacing_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", 2.0)) # Currently not used

    concrete_material_name: str = "C40/50"
    concrete_material_code: str = "EN04(RC)"
    concrete_material_grade: str = "C40/50"

    tendon_material_name: str = "TD_steel"
    tendon_material_code: str = "IS(S)"
    tendon_material_grade: str = "E450"
    tendon_material_id: int = 1

    section_name: str = "PSC_RECT_VALUE"
    section_id: int = 2

    outer_polygon: list[tuple[float, float]] | None = None
    inner_polygons: list[list[tuple[float, float]]] = field(default_factory=list)

    left_support: str = "111000"
    right_support: str = "011000"

    self_weight_case: str = "Self Weight"
    udl_case: str = "UDL"
    ts_case: str = "TS"
    prestress_case: str = "Prestress"

    n_tendons: IntRange = field(default_factory=lambda: IntRange("fixed", 3))
    tendon_force_kn: FloatRange = field(default_factory=lambda: FloatRange("fixed", 220.0))
    
    tendon_ecc_start_m: FloatRange = field(default_factory=lambda: FloatRange("random", -0.2, 0.0))
    symetric = True # if True, tendon_ecc_end_m will be set to tendon_ecc_start_m
    tendon_ecc_end_m: FloatRange = field(default_factory=lambda: FloatRange("random", -0.2, 0.0))

    tendon_ecc_mid_m: FloatRange = field(default_factory=lambda: FloatRange("fixed", -0.35))
    tendon_area_mm2: FloatRange = field(default_factory=lambda: FloatRange("fixed", 150.0))
    tendon_profile_type: str = "parabolic"

    def validate(self) -> None:
        self.span_length_m.validate("span_length_m")
        self.beam_height_m.validate("beam_height_m")
        self.beam_width_m.validate("beam_width_m")
        self.udl_kn_per_m.validate("udl_kn_per_m")
        self.beam_divisions.validate("beam_divisions")

        self.tendon_force_kn.validate("tendon_force_kn")
        self.tendon_ecc_start_m.validate("tendon_ecc_start_m")
        self.tendon_ecc_mid_m.validate("tendon_ecc_mid_m")
        self.tendon_ecc_end_m.validate("tendon_ecc_end_m")
        self.tendon_area_mm2.validate("tendon_area_mm2")

        self.ts_left_force_kn.validate("ts_left_force_kn")
        self.ts_right_force_kn.validate("ts_right_force_kn")
        self.ts_spacing_m.validate("ts_spacing_m")

        if self.ts_spacing_m.min <= 0:
            raise ValueError("ts_spacing_m must be > 0")
        if self.beam_divisions.min < 2:
            raise ValueError("beam_divisions.min must be >= 2")

        if self.tendon_profile_type not in {"parabolic", "straight"}:
            raise ValueError("tendon_profile_type must be 'parabolic' or 'straight'")

        if self.outer_polygon is not None and len(self.outer_polygon) < 3:
            raise ValueError("outer_polygon must contain at least 3 points")

@dataclass
class SingleSpanBeamConfig:
    span_length_m: FloatRange = field(default_factory=lambda: FloatRange("random", 5.0, 20.0))
    udl_kn_per_m: FloatRange = field(default_factory=lambda: FloatRange("random", 5.0, 30.0))
    beam_divisions: IntRange = field(default_factory=lambda: IntRange("fixed", 10))

    material_name: str = "A36"
    material_code: str = "ASTM(S)"
    material_grade: str = "A36"

    section_name: str = "W8x35"
    section_shape: str = "H"
    section_db: str = "AISC"
    section_db_name: str = "W8x35"
    section_id: int = 1

    left_support: str = "111000"   # pin
    right_support: str = "011000"  # roller

    self_weight_case: str = "Self Weight"
    udl_case: str = "UDL"

    def validate(self) -> None:
        self.span_length_m.validate("span_length_m")
        self.udl_kn_per_m.validate("udl_kn_per_m")
        self.beam_divisions.validate("beam_divisions")

        if self.beam_divisions.min < 2:
            raise ValueError("beam_divisions.min must be >= 2")


@dataclass
class ExperimentInputsConfig:
    n_models: int
    model_type: Model_Type = Model_Type.TWO_SPAN_POST_TENSIONED_BEAM
    random_seed: int | None = None
    input_csv_path: str = "input.csv"

    # in this part we have to add all currently supported Model_Types as possible types for model_config, 
    # and then in __post_init__ we set the default config based on the model_type
    ###
    model_config: Union[
        SingleSpanBeamConfig,
        SingleSpanPostTensionedBeamConfig,
        TwoSpanPostTensionedBeamConfig,
        FixedParamsTwoSpanPostTensionedBeamConfig,
        MultiSpanBeamConfig,
        None,
    ] = None

    def __post_init__(self) -> None:
        if self.model_config is None:
            match self.model_type:
                case Model_Type.SINGLE_SPAN_BEAM:
                    self.model_config = SingleSpanBeamConfig()
                case Model_Type.SINGLE_SPAN_POST_TENSIONED_BEAM:
                    self.model_config = SingleSpanPostTensionedBeamConfig()
                case Model_Type.TWO_SPAN_POST_TENSIONED_BEAM:
                    self.model_config = TwoSpanPostTensionedBeamConfig()
                case Model_Type.FIXED_PARAMS_TWO_SPAN_POST_TENSIONED_BEAM:
                    self.model_config = FixedParamsTwoSpanPostTensionedBeamConfig()
                case Model_Type.MULTI_SPAN_BEAM:
                    self.model_config = MultiSpanBeamConfig()
                case _:
                    raise ValueError(f"Unsupported model_type: {self.model_type}")

    def validate(self) -> None:
        if self.n_models <= 0:
            raise ValueError("n_models must be > 0")
        if self.random_seed is not None and not isinstance(self.random_seed, int):
            raise ValueError("random_seed must be int or None")
        if not self.input_csv_path or not self.input_csv_path.strip():
            raise ValueError("input_csv_path cannot be empty")

