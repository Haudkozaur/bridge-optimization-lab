from random import Random

from midas_civil import Boundary, Element, Load, Material, Model, Section, Tendon, Offset

from experiment.experiment_config import Model_Type, SingleSpanPostTensionedBeamConfig


class SingleSpanPostTensionedBeam:
    def __init__(self, config: SingleSpanPostTensionedBeamConfig, rng: Random):
        self.config = config
        self.rng = rng

    def sample_parameters(self) -> dict:
        beam_divisions = self.rng.randint(
            self.config.beam_divisions.min,
            self.config.beam_divisions.max,
        )

        if beam_divisions % 2 != 0:
            beam_divisions += 1

        return {
            "model_type": Model_Type.SINGLE_SPAN_POST_TENSIONED_BEAM,

            "span_length_m": round(
                self.rng.uniform(
                    self.config.span_length_m.min,
                    self.config.span_length_m.max,
                ),
                1,
            ),

            "beam_height_m": round(
                self.rng.uniform(
                    self.config.beam_height_m.min,
                    self.config.beam_height_m.max,
                ),
                2,
            ),

            "beam_width_m": round(
                self.rng.uniform(
                    self.config.beam_width_m.min,
                    self.config.beam_width_m.max,
                ),
                2,
            ),

            "udl_kn_per_m": round(
                self.rng.uniform(
                    self.config.udl_kn_per_m.min,
                    self.config.udl_kn_per_m.max,
                ),
                1,
            ),

            "ts_left_force_kn": round(
                self.rng.uniform(
                    self.config.ts_left_force_kn.min,
                    self.config.ts_left_force_kn.max,
                ),
                1,
            ),

            "ts_right_force_kn": round(
                self.rng.uniform(
                    self.config.ts_right_force_kn.min,
                    self.config.ts_right_force_kn.max,
                ),
                1,
            ),
            "ts_spacing_m": round(
                self.rng.uniform(
                    self.config.ts_spacing_m.min,
                    self.config.ts_spacing_m.max,
                ),
                1,
            ),

            "beam_divisions": beam_divisions,

            "n_tendons": self.rng.randint(
                self.config.n_tendons.min,
                self.config.n_tendons.max,
            ),

            "tendon_force_kn": round(
                self.rng.uniform(
                    self.config.tendon_force_kn.min,
                    self.config.tendon_force_kn.max,
                ),
                1,
            ),

            "tendon_ecc_start_m": round(
                self.rng.uniform(
                    self.config.tendon_ecc_start_m.min,
                    self.config.tendon_ecc_start_m.max,
                ),
                2,
            ),

            "tendon_ecc_mid_m": round(
                self.rng.uniform(
                    self.config.tendon_ecc_mid_m.min,
                    self.config.tendon_ecc_mid_m.max,
                ),
                2,
            ),

            "tendon_ecc_end_m": round(
                self.rng.uniform(
                    self.config.tendon_ecc_end_m.min,
                    self.config.tendon_ecc_end_m.max,
                ),
                2,
            ),

            "tendon_area_mm2": round(
                self.rng.uniform(
                    self.config.tendon_area_mm2.min,
                    self.config.tendon_area_mm2.max,
                ),
                1,
            ),

            "tendon_profile_type": self.config.tendon_profile_type,
        }
    def build_model(self, sampled: dict) -> dict:
        span_length = sampled["span_length_m"]
        udl_kn_per_m = sampled["udl_kn_per_m"]
        beam_divisions = sampled["beam_divisions"]

        self._create_concrete_material()
        self._create_tendon_material()
        self._create_section(sampled)

        beam_ids = self._create_beam_elements(span_length, beam_divisions)

        left_nodes = self._get_nodes_at_x(0.0)
        right_nodes = self._get_nodes_at_x(span_length)

        if not left_nodes:
            raise ValueError("No left support nodes found at x=0")
        if not right_nodes:
            raise ValueError(f"No right support nodes found at x={span_length}")

        Boundary.Support(left_nodes, self.config.left_support)
        Boundary.Support(right_nodes, self.config.right_support)

        self._apply_basic_loads(beam_ids, udl_kn_per_m)
        left_ts_nodes, right_ts_nodes = self._apply_ts_loads(sampled)
        self._apply_prestress(sampled, beam_ids)

        mid_x = span_length / 2.0
        mid_nodes = self._get_nodes_at_x(mid_x)

        if not mid_nodes:
            raise ValueError(f"No mid-span node found at x={mid_x}")

        return {
            "span_length_m": span_length,
            "beam_height_m": sampled["beam_height_m"],
            "beam_width_m": sampled["beam_width_m"],
            "left_nodes": left_nodes,
            "right_nodes": right_nodes,
            "mid_nodes": mid_nodes,
            "beam_ids": beam_ids,
            "udl_case_result_name": f"{self.config.udl_case}(ST)",
            "self_weight_result_name": f"{self.config.self_weight_case}(ST)",
            "ts_case_result_name": f"{self.config.ts_case}(ST)",
            "ts_left_force_kn": sampled["ts_left_force_kn"],
            "ts_right_force_kn": sampled["ts_right_force_kn"],
            "left_ts_nodes": left_ts_nodes,
            "right_ts_nodes": right_ts_nodes,
            "ts_spacing_m": sampled["ts_spacing_m"],
            "prestress_case_result_name": f"{self.config.prestress_case}(ST)",
            "n_tendons": sampled["n_tendons"],
            "tendon_force_kn": sampled["tendon_force_kn"],
            "tendon_area_mm2": sampled["tendon_area_mm2"],
            "total_tendon_force_kn": sampled["n_tendons"] * sampled["tendon_force_kn"],
            "total_tendon_area_mm2": sampled["n_tendons"] * sampled["tendon_area_mm2"],
            "tendon_ecc_start_m": sampled["tendon_ecc_start_m"],
            "tendon_ecc_mid_m": sampled["tendon_ecc_mid_m"],
            "tendon_ecc_end_m": sampled["tendon_ecc_end_m"],
            "tendon_profile_type": sampled["tendon_profile_type"],
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

    # def _create_section(self, sampled: dict) -> None:
    #     _ = sampled

    #     Section.DB(
    #         self.config.section_name,
    #         self.config.section_shape,
    #         self.config.section_db,
    #         self.config.section_db_name,
    #         id=self.config.section_id,
    #     )
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

    def _create_beam_elements(self, span_length: float, divisions: int) -> list[int]:
        Element.Beam.SDL(
            [0, 0, 0],
            [1, 0, 0],
            span_length,
            n=divisions,
            sect=self.config.section_id,
        )

        all_beam_ids_in_box = sorted(
            Model.Select.Box([0, 0, 0], [span_length, 0, 0], "ELEM_ID")
        )
        

        if len(all_beam_ids_in_box) < divisions:
            raise ValueError(
                f"Expected at least {divisions} beam elements in selection box, "
                f"got {len(all_beam_ids_in_box)}"
            )

        beam_ids = all_beam_ids_in_box[-divisions:]
        
        return beam_ids

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

    def _apply_ts_loads(self, sampled: dict) -> tuple[list[int], list[int]]:
        div = sampled["beam_divisions"]

        left_ts_node = div // 2
        right_ts_node = div // 2 + 2

        Load.Nodal(
            [left_ts_node],
            self.config.ts_case,
            "",
            FZ=-sampled["ts_left_force_kn"],
        )

        Load.Nodal(
            [right_ts_node],
            self.config.ts_case,
            "",
            FZ=-sampled["ts_right_force_kn"],
        )

        return [left_ts_node], [right_ts_node]

    

    def _apply_prestress(self, sampled: dict, beam_ids: list[int]) -> None:
        span_length = sampled["span_length_m"]

        n_tendons = sampled["n_tendons"]
        tendon_force_kn = sampled["tendon_force_kn"]
        tendon_area_mm2 = sampled["tendon_area_mm2"]

        total_tendon_force_kn = n_tendons * tendon_force_kn
        total_tendon_area_mm2 = n_tendons * tendon_area_mm2

        ecc_start = sampled["tendon_ecc_start_m"]
        if self.config.symetric:
            ecc_end = sampled["tendon_ecc_start_m"]
        else:
            ecc_end = sampled["tendon_ecc_end_m"]
        print(self.config.symetric, ecc_start, ecc_end)
        ecc_mid = sampled["tendon_ecc_mid_m"]
        profile_type = sampled["tendon_profile_type"]

        if profile_type != "parabolic":
            raise ValueError("For now only 'parabolic' tendon_profile_type is supported")

        tendon_prop_name = "TD_PROP_1"
        tendon_profile_name = "TD_PROFILE_1"

        Tendon.Property(
            tendon_prop_name,
            2,
            self.config.tendon_material_id,
            total_tendon_area_mm2,
            0.10,
            Tendon.Relaxation.Null(1800, 1500),
        )
        Tendon.Property.create()

        prof_xy = [
            [0.0, 0.0],
            [span_length, 0.0],
        ]

        prof_xz = [
            [0.0, ecc_start],
            [span_length / 2.0, ecc_mid],
            [span_length, ecc_end],
        ]

        Tendon.Profile(
            tendon_profile_name,
            1,
            0,
            beam_ids,
            "2D",
            "SPLINE",
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
            "BEGIN",
            total_tendon_force_kn,
            0.0,
            0,
        )
        Tendon.Prestress.create()

    def _get_nodes_at_x(self, x: float) -> list[int]:
        return sorted(Model.Select.Box([x, 0, 0], [x, 0, 0], "NODE_ID"))