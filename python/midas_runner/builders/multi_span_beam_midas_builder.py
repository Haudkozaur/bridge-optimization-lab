from random import Random

from midas_civil import Boundary, Element, Load, Material, Model, Section, Tendon, Offset

from model_inputs.configs.experiment_inputs_config import MultiSpanBeamConfig


class MultiSpanBeamMidasBuilder:
    def __init__(self, config: MultiSpanBeamConfig, rng: Random):
        self.config = config
        self.rng = rng

    def build_model(self, sampled: dict) -> dict:
        span_lengths = self._parse_float_list(sampled["span_lengths_m"])
        beam_divisions = self._parse_int_list(sampled["beam_divisions"])
        tendon_ecc = self._parse_float_list(sampled["tendon_ecc_control_points_m"])

        n_spans = int(sampled["n_spans"])

        if len(span_lengths) != n_spans:
            raise ValueError(f"n_spans={n_spans}, but got {len(span_lengths)} span lengths")

        if len(beam_divisions) != n_spans:
            raise ValueError(f"n_spans={n_spans}, but got {len(beam_divisions)} beam divisions")

        expected_ecc_count = 4 * n_spans + 1
        if len(tendon_ecc) != expected_ecc_count:
            raise ValueError(
                f"Expected {expected_ecc_count} tendon eccentricity points, "
                f"but got {len(tendon_ecc)}"
            )

        total_span = sum(span_lengths)
        total_divisions = sum(beam_divisions)

        udl_kn_per_m = sampled["udl_kn_per_m"]

        self._create_concrete_material()
        self._create_tendon_material()
        self._create_section(sampled)

        beam_ids = self._create_beam_elements(total_span, total_divisions)

        support_x = self._build_support_x(span_lengths)

        left_nodes = [1]
        internal_nodes = [
            sum(beam_divisions[:i]) + 1
            for i in range(1, n_spans)
        ]
        right_nodes = [total_divisions + 1]

        all_nodes = list(range(1, total_divisions + 2))

        support_nodes = {"left": left_nodes}

        for i, node in enumerate(internal_nodes, start=1):
            support_nodes[f"internal_{i}"] = [node]

        support_nodes["right"] = right_nodes

        Boundary.Support(left_nodes, self.config.left_support)
        Boundary.Support(internal_nodes, self.config.internal_support)
        Boundary.Support(right_nodes, self.config.right_support)

        self._apply_basic_loads(beam_ids, udl_kn_per_m)
        self._apply_prestress(
            sampled=sampled,
            beam_ids=beam_ids,
            span_lengths=span_lengths,
            tendon_ecc=tendon_ecc,
        )

        mid_span_nodes = self._get_mid_span_nodes(span_lengths)

        return {
            "n_spans": n_spans,
            "span_lengths_m": span_lengths,
            "total_span_length_m": total_span,
            "beam_divisions": beam_divisions,
            "total_divisions": total_divisions,

            "beam_height_m": sampled["beam_height_m"],
            "beam_width_m": sampled["beam_width_m"],

            "support_x": support_x,
            "left_nodes": left_nodes,
            "internal_nodes": internal_nodes,
            "right_nodes": right_nodes,
            "support_nodes": support_nodes,
            "all_nodes": all_nodes,
            "mid_span_nodes": mid_span_nodes,

            "beam_ids": beam_ids,

            "udl_case_result_name": f"{self.config.udl_case}(ST)",
            "self_weight_result_name": f"{self.config.self_weight_case}(ST)",
            "prestress_case_result_name": f"{self.config.prestress_case}(ST)",

            "n_tendons": sampled["n_tendons"],
            "tendon_force_kn": sampled["tendon_force_kn"],
            "tendon_area_mm2": sampled["tendon_area_mm2"],
            "total_tendon_force_kn": sampled["n_tendons"] * sampled["tendon_force_kn"],
            "total_tendon_area_mm2": sampled["n_tendons"] * sampled["tendon_area_mm2"],

            "tendon_control_points_per_span": sampled["tendon_control_points_per_span"],
            "tendon_ecc_control_points_m": tendon_ecc,
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

    def _apply_prestress(
        self,
        sampled: dict,
        beam_ids: list[int],
        span_lengths: list[float],
        tendon_ecc: list[float],
    ) -> None:
        n_tendons = sampled["n_tendons"]
        tendon_force_kn = sampled["tendon_force_kn"]
        tendon_area_mm2 = sampled["tendon_area_mm2"]

        total_tendon_force_kn = n_tendons * tendon_force_kn
        total_tendon_area_m2 = n_tendons * tendon_area_mm2 * 1.0e-6

        tendon_duct_diameter = 0.1

        tendon_prop_id = 1
        tendon_prop_name = "TD_PROP_1"
        tendon_profile_name = "TD_PROFILE_1"

        Tendon.Property(
            name=tendon_prop_name,
            type=2,
            id=tendon_prop_id,
            matID=self.config.tendon_material_id,
            tdn_area=total_tendon_area_m2,
            duct_dia=tendon_duct_diameter,
            relaxation=Tendon.Relaxation.Null(1800, 1500),
        )
        Tendon.Property.create()

        total_span = sum(span_lengths)

        prof_xy = [
            [0.0, 0.0],
            [total_span, 0.0],
        ]

        tendon_x = self._build_tendon_x(span_lengths)

        prof_xz = [
            [float(x), float(e)]
            for x, e in zip(tendon_x, tendon_ecc)
        ]

        Tendon.Profile(
            name=tendon_profile_name,
            tdn_prop=tendon_prop_id,
            tdn_group=0,
            elem=beam_ids,
            inp_type="2D",
            curve_type="SPLINE",
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

    def _build_support_x(self, span_lengths: list[float]) -> list[float]:
        support_x = [0.0]
        current_x = 0.0

        for span_length in span_lengths:
            current_x += span_length
            support_x.append(current_x)

        return support_x

    def _build_tendon_x(self, span_lengths: list[float]) -> list[float]:
        points = []
        current_x = 0.0

        for i, span_length in enumerate(span_lengths):
            x0 = current_x
            x1 = current_x + span_length

            local_points = [
                x0,
                x0 + 0.25 * span_length,
                x0 + 0.50 * span_length,
                x0 + 0.75 * span_length,
                x1,
            ]

            if i == 0:
                points.extend(local_points)
            else:
                points.extend(local_points[1:])

            current_x = x1

        return points

    def _get_mid_span_nodes(self, span_lengths: list[float]) -> dict[int, list[int]]:
        mid_nodes = {}

        current_x = 0.0

        for i, span_length in enumerate(span_lengths, start=1):
            mid_x = current_x + 0.5 * span_length
            mid_nodes[i] = self._get_nodes_at_x(mid_x)
            current_x += span_length

        return mid_nodes

    def _get_nodes_at_x(self, x: float) -> list[int]:
        return sorted(Model.Select.Box([x, 0, 0], [x, 0, 0], "NODE_ID"))

    def _parse_float_list(self, value) -> list[float]:
        return [
            float(part)
            for part in str(value).split(";")
            if part.strip()
        ]

    def _parse_int_list(self, value) -> list[int]:
        return [
            int(float(part))
            for part in str(value).split(";")
            if part.strip()
        ]