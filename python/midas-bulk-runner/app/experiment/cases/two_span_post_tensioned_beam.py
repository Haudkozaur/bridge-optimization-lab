from random import Random

from midas_civil import Boundary, Element, Load, Material, Model, Section, Tendon, Offset

from experiment.experiment_config import Model_Type, TwoSpanPostTensionedBeamConfig, FixedParamsTwoSpanPostTensionedBeamConfig
from experiment.ranges import FloatRange

class TwoSpanPostTensionedBeam:
    def __init__(self, config: TwoSpanPostTensionedBeamConfig, rng: Random):
        self.config = config
        self.rng = rng

    def _sample_float_range(self, value_range: FloatRange, ndigits: int = 3) -> float:
        if value_range is None:
            raise ValueError("value_range cannot be None")

        if value_range.mode == "fixed":
            return round(value_range.min, ndigits)

        return round(
            self.rng.uniform(value_range.min, value_range.max),
            ndigits,
        )

    def _sample_tendon_shape_type(self):
        shape_value = self.rng.randint(
            self.config.tendon_shape_randomizer.min,
            self.config.tendon_shape_randomizer.max,
        )

        return self.config.TendonShapeType(shape_value)
    
    def _get_tendon_ecc_ranges(self, shape_type):
        match shape_type:
            case self.config.TendonShapeType.RANDOM_TWO_SPAN:
                return {
                    "left": FloatRange("random", -0.45, 0.45),
                    "left_mid": FloatRange("random", -0.45, 0.45),
                    "support": FloatRange("random", -0.45, 0.45),
                    "right_mid": FloatRange("random", -0.45, 0.45),
                    "right": FloatRange("random", -0.45, 0.45),
                }

            case self.config.TendonShapeType.FORCED_REALISTIC_TWO_SPAN:
                return {
                    "left": FloatRange("random", -0.10, 0.10),
                    "left_mid": FloatRange("random", -0.45, -0.15),
                    "support": FloatRange("random", -0.25, 0.45),
                    "right_mid": FloatRange("random", -0.45, -0.15),
                    "right": FloatRange("random", -0.10, 0.10),
                }

            case self.config.TendonShapeType.FORCED_SYMMETRIC_TWO_SPAN:
                return {
                    "left": FloatRange("random", -0.45, 0.45),
                    "left_mid": FloatRange("random", -0.45, 0.45),
                    "support": FloatRange("random", -0.45, 0.45),
                    "right_mid": None,
                    "right": None,
                }

            case self.config.TendonShapeType.FORCED_REALISTIC_SYMMETRIC_TWO_SPAN:
                return {
                    "left": FloatRange("random", -0.10, 0.10),
                    "left_mid": FloatRange("random", -0.45, -0.15),
                    "support": FloatRange("random", -0.25, 0.45),
                    "right_mid": None,
                    "right": None,
                }

            case _:
                raise ValueError(f"Unsupported tendon shape type: {shape_type}")
    
    def _make_even(self, value: int) -> int:
        if value % 2 != 0:
            value += 1
        return value


    def sample_parameters(self) -> dict:
        tendon_shape_type = self._sample_tendon_shape_type()

        is_symmetric = tendon_shape_type in {
            self.config.TendonShapeType.FORCED_SYMMETRIC_TWO_SPAN,
            self.config.TendonShapeType.FORCED_REALISTIC_SYMMETRIC_TWO_SPAN,
        }

        left_span_length = round(
            self.rng.uniform(
                self.config.left_span_length_m.min,
                self.config.left_span_length_m.max,
            ),
            1,
        )

        if is_symmetric:
            right_span_length = left_span_length
        else:
            right_span_length = round(
                self.rng.uniform(
                    self.config.right_span_length_m.min,
                    self.config.right_span_length_m.max,
                ),
                1,
            )

        left_beam_divisions = self._make_even(max(4, round(left_span_length / 1.5)))

        if is_symmetric:
            right_beam_divisions = left_beam_divisions
        else:
            right_beam_divisions = self._make_even(max(4, round(right_span_length / 1.5)))

        if is_symmetric:
            right_beam_divisions = left_beam_divisions
        else:
            right_beam_divisions = self._make_even(max(4, round(right_span_length / 1.5)))

        tendon_ranges = self._get_tendon_ecc_ranges(tendon_shape_type)

        if self.config.tendon_ecc_left_m is not None:
            tendon_ecc_left = self._sample_float_range(self.config.tendon_ecc_left_m)
        else:
            tendon_ecc_left = self._sample_float_range(tendon_ranges["left"])

        if self.config.tendon_ecc_left_span_mid_m is not None:
            tendon_ecc_left_mid = self._sample_float_range(self.config.tendon_ecc_left_span_mid_m)
        else:
            tendon_ecc_left_mid = self._sample_float_range(tendon_ranges["left_mid"])

        if self.config.tendon_ecc_mid_support_m is not None:
            tendon_ecc_support = self._sample_float_range(self.config.tendon_ecc_mid_support_m)
        else:
            tendon_ecc_support = self._sample_float_range(tendon_ranges["support"])

        if self.config.tendon_ecc_right_span_mid_m is not None:
            tendon_ecc_right_mid = self._sample_float_range(self.config.tendon_ecc_right_span_mid_m)
        elif tendon_ranges["right_mid"] is None:
            tendon_ecc_right_mid = tendon_ecc_left_mid
        else:
            tendon_ecc_right_mid = self._sample_float_range(tendon_ranges["right_mid"])

        if self.config.tendon_ecc_right_m is not None:
            tendon_ecc_right = self._sample_float_range(self.config.tendon_ecc_right_m)
        elif tendon_ranges["right"] is None:
            tendon_ecc_right = tendon_ecc_left
        else:
            tendon_ecc_right = self._sample_float_range(tendon_ranges["right"])

        return {
            "left_span_length_m": left_span_length,
            "right_span_length_m": right_span_length,

            "left_beam_divisions": left_beam_divisions,
            "right_beam_divisions": right_beam_divisions,

            "beam_height_m": self.config.beam_height_m.min,
            "beam_width_m": self.config.beam_width_m.min,

            "udl_kn_per_m": round(
                self.rng.uniform(
                    self.config.udl_kn_per_m.min,
                    self.config.udl_kn_per_m.max,
                ),
                2,
            ),

            "n_tendons": self.config.n_tendons.min,

            "tendon_force_kn": self.config.tendon_force_kn.min,
            "tendon_area_mm2": self.config.tendon_area_mm2.min,

            "tendon_shape_type": tendon_shape_type.name,

            "tendon_ecc_left_m": tendon_ecc_left,
            "tendon_ecc_left_span_mid_m": tendon_ecc_left_mid,
            "tendon_ecc_mid_support_m": tendon_ecc_support,
            "tendon_ecc_right_span_mid_m": tendon_ecc_right_mid,
            "tendon_ecc_right_m": tendon_ecc_right,
        }
    

    
    def build_model(self, sampled: dict) -> dict:
        left_span = sampled["left_span_length_m"]
        right_span = sampled["right_span_length_m"]
        total_span = left_span + right_span

        udl_kn_per_m = sampled["udl_kn_per_m"]
        total_divisions = sampled["left_beam_divisions"] + sampled["right_beam_divisions"]

        self._create_concrete_material()
        self._create_tendon_material()
        self._create_section(sampled)

        beam_ids = self._create_beam_elements(total_span, total_divisions)

        left_nodes = [1]
        middle_nodes = [sampled["left_beam_divisions"] + 1]
        right_nodes = [total_divisions + 1]

        all_nodes = list(range(1, total_divisions + 2))

        support_nodes = {
            "left": left_nodes,
            "middle": middle_nodes,
            "right": right_nodes,
        }

        if not left_nodes:
            raise ValueError("No left support nodes found at x=0")
        if not middle_nodes:
            raise ValueError(f"No middle support nodes found at x={left_span}")
        if not right_nodes:
            raise ValueError(f"No right support nodes found at x={total_span}")

        Boundary.Support(left_nodes, self.config.left_support)
        Boundary.Support(middle_nodes, self.config.middle_support)
        Boundary.Support(right_nodes, self.config.right_support)

        self._apply_basic_loads(beam_ids, udl_kn_per_m)
        self._apply_prestress(sampled, beam_ids)

        left_mid_nodes = self._get_nodes_at_x(left_span / 2.0)
        right_mid_nodes = self._get_nodes_at_x(left_span + right_span / 2.0)

        return {
            "left_span_length_m": left_span,
            "right_span_length_m": right_span,
            "total_span_length_m": total_span,

            "beam_height_m": sampled["beam_height_m"],
            "beam_width_m": sampled["beam_width_m"],

            "left_nodes": left_nodes,
            "middle_nodes": middle_nodes,
            "right_nodes": right_nodes,

            "left_mid_nodes": left_mid_nodes,
            "right_mid_nodes": right_mid_nodes,

            "all_nodes": all_nodes,
            "support_nodes": support_nodes,

            "mid_nodes": left_mid_nodes,

            "beam_ids": beam_ids,

            "udl_case_result_name": f"{self.config.udl_case}(ST)",
            "self_weight_result_name": f"{self.config.self_weight_case}(ST)",
            "prestress_case_result_name": f"{self.config.prestress_case}(ST)",

            "n_tendons": sampled["n_tendons"],
            "tendon_force_kn": sampled["tendon_force_kn"],
            "tendon_area_mm2": sampled["tendon_area_mm2"],
            "total_tendon_force_kn": sampled["n_tendons"] * sampled["tendon_force_kn"],
            "total_tendon_area_mm2": sampled["n_tendons"] * sampled["tendon_area_mm2"],

            "tendon_shape_type": sampled["tendon_shape_type"],

            "tendon_ecc_left_m": sampled["tendon_ecc_left_m"],
            "tendon_ecc_left_span_mid_m": sampled["tendon_ecc_left_span_mid_m"],
            "tendon_ecc_mid_support_m": sampled["tendon_ecc_mid_support_m"],
            "tendon_ecc_right_span_mid_m": sampled["tendon_ecc_right_span_mid_m"],
            "tendon_ecc_right_m": sampled["tendon_ecc_right_m"],
        }

    def _create_concrete_material(self) -> None:
        Material.CONC(
            self.config.concrete_material_name,
            self.config.concrete_material_code,
            self.config.concrete_material_grade,
        )

    def _create_tendon_material(self) -> None:
        Material.STEEL(
            self.config.tendon_material_name,
            self.config.tendon_material_code,
            self.config.tendon_material_grade,
            id=self.config.tendon_material_id,
        )

    def _create_section(self, sampled: dict) -> None:
        b = sampled["beam_width_m"]
        h = sampled["beam_height_m"]

        if self.config.outer_polygon is not None:
            outer_polygon = self.config.outer_polygon
        else:
            outer_polygon = self._build_rect_outer_polygon(b, h)

        Section.PSC.Value(
            Name=self.config.section_name,
            OuterPolygon=outer_polygon,
            InnerPolygon=self.config.inner_polygons,
            Offset=Offset.CC(),
            useShear=True,
            use7Dof=False,
            id=self.config.section_id,
        )

    def _build_rect_outer_polygon(self, b: float, h: float) -> list[tuple[float, float]]:
        return [
            (-b / 2.0,  h / 2.0),
            ( b / 2.0,  h / 2.0),
            ( b / 2.0, -h / 2.0),
            (-b / 2.0, -h / 2.0),
        ]

    def _create_beam_elements(self, total_span_length: float, divisions: int) -> list[int]:
        Element.Beam.SDL(
            [0, 0, 0],
            [1, 0, 0],
            total_span_length,
            n=divisions,
            sect=self.config.section_id,
        )

        return list(range(1, divisions + 1))

    def _apply_basic_loads(self, beam_ids: list[int], udl_kn_per_m: float) -> None:
        Load.SW(self.config.self_weight_case)

        Load.Beam(
            beam_ids,
            self.config.udl_case,
            "",
            direction="GZ",
            D=[0, 1],
            P=[-udl_kn_per_m, -udl_kn_per_m],
        )

    def _apply_prestress(self, sampled: dict, beam_ids: list[int]) -> None:
        left_span = sampled["left_span_length_m"]
        right_span = sampled["right_span_length_m"]
        total_span = left_span + right_span

        n_tendons = sampled["n_tendons"]
        tendon_force_kn = sampled["tendon_force_kn"]
        tendon_area_mm2 = sampled["tendon_area_mm2"]

        total_tendon_force_kn = n_tendons * tendon_force_kn
        total_tendon_area_mm2 = tendon_area_mm2*0.000001 # convert
        tendon_duct_diameter = 0.1 # 100mm duct diameter

        tendon_prop_id = 1
        tendon_prop_name = "TD_PROP_1"
        tendon_profile_name = "TD_PROFILE_1"

        Tendon.Property(
            name = tendon_prop_name,
            type = 2,
            id = tendon_prop_id,
            matID = self.config.tendon_material_id,
            tdn_area = total_tendon_area_mm2,
            duct_dia = tendon_duct_diameter,
            relaxation = Tendon.Relaxation.Null(1800, 1500),
        )
        Tendon.Property.create()

        prof_xy = [
            [0.0, 0.0],
            [total_span, 0.0],
        ]

        prof_xz = [
            [0.0, sampled["tendon_ecc_left_m"]],
            [left_span / 2.0, sampled["tendon_ecc_left_span_mid_m"]],
            [left_span, sampled["tendon_ecc_mid_support_m"]],
            [left_span + right_span / 2.0, sampled["tendon_ecc_right_span_mid_m"]],
            [total_span, sampled["tendon_ecc_right_m"]],
        ]

        Tendon.Profile(
            name = tendon_profile_name,
            tdn_prop = tendon_prop_id,
            tdn_group = 0,
            elem = beam_ids,
            inp_type = "2D",
            curve_type = "SPLINE",
            ref_axis="ELEMENT",
            prof_xyR=prof_xy,
            prof_xzR=prof_xz,
        )
        Tendon.Profile.create()

        Tendon.Prestress(
            tendon_profile_name,
            self.config.prestress_case,
            "",
            "FORCE",
            "BOTH",
            total_tendon_force_kn,
            total_tendon_force_kn,
            0,
        )
        Tendon.Prestress.create()

    def _get_nodes_at_x(self, x: float) -> list[int]:
        return sorted(Model.Select.Box([x, 0, 0], [x, 0, 0], "NODE_ID"))