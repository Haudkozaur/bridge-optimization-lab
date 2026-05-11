from random import Random

from midas_civil import Boundary, Element, Load, Material, Model, Section

from experiment.experiment_config import Model_Type, SingleSpanBeamConfig


class SingleSpanBeam:
    def __init__(self, config: SingleSpanBeamConfig, rng: Random):
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
            "model_type": Model_Type.SINGLE_SPAN_BEAM,
            "span_length_m": round(
                self.rng.uniform(
                    self.config.span_length_m.min,
                    self.config.span_length_m.max,
                ),
                4,
            ),
            "udl_kn_per_m": round(
                self.rng.uniform(
                    self.config.udl_kn_per_m.min,
                    self.config.udl_kn_per_m.max,
                ),
                4,
            ),
            "beam_divisions": beam_divisions,
        }

    def build_model(self, sampled: dict) -> dict:
        L = sampled["span_length_m"]
        w = sampled["udl_kn_per_m"]
        div = sampled["beam_divisions"]

        self._create_material()
        self._create_section()

        beam_ids = self._create_beam_elements(L, div)

        left_nodes = self._get_nodes_at_x(0.0)
        right_nodes = self._get_nodes_at_x(L)

        if not left_nodes:
            raise ValueError("No left support nodes found at x=0")
        if not right_nodes:
            raise ValueError(f"No right support nodes found at x={L}")

        Boundary.Support(left_nodes, self.config.left_support)
        Boundary.Support(right_nodes, self.config.right_support)

        Load.SW(self.config.self_weight_case)

        Load.Beam(
            beam_ids,
            self.config.udl_case,
            "",
            direction="GZ",
            D=[0, 1],
            P=[-w, -w],
        )

        mid_x = L / 2.0
        mid_nodes = self._get_nodes_at_x(mid_x)

        if not mid_nodes:
            raise ValueError(f"No mid-span node found at x={mid_x}")

        return {
            "span_length_m": L,
            "left_nodes": left_nodes,
            "right_nodes": right_nodes,
            "mid_nodes": mid_nodes,
            "beam_ids": beam_ids,
            "udl_case_result_name": f"{self.config.udl_case}(ST)",
            "self_weight_result_name": f"{self.config.self_weight_case}(ST)",
        }

    def _create_material(self) -> None:
        Material.STEEL(
            self.config.material_name,
            self.config.material_code,
            self.config.material_grade,
        )

    def _create_section(self) -> None:
        Section.DB(
            self.config.section_name,
            self.config.section_shape,
            self.config.section_db,
            self.config.section_db_name,
            id=self.config.section_id,
        )

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

    def _get_nodes_at_x(self, x: float) -> list[int]:
        return sorted(Model.Select.Box([x, 0, 0], [x, 0, 0]))