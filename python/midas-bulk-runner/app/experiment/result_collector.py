# from midas_civil import Result

# from experiment.experiment_config import ExperimentConfig


# class ResultCollector:
#     def __init__(self, config: ExperimentConfig):
#         self.config = config

#     def collect(self, model_meta: dict) -> dict:
#         result_names = self.config.results_to_save
#         out = {}

#         sw_lc = model_meta["self_weight_result_name"]
#         udl_lc = model_meta["udl_case_result_name"]
#         ts_lc = model_meta.get("ts_case_result_name")
#         ps_lc = model_meta.get("prestress_case_result_name")

#         # =========================
#         # MIDSPAN DEFLECTIONS
#         # =========================
#         if "mid_deflection_sw" in result_names:
#             out["mid_deflection_sw"] = self._get_mid_deflection_dz(
#                 mid_nodes=model_meta["mid_nodes"],
#                 loadcase=sw_lc,
#             )

#         if "mid_deflection_udl" in result_names:
#             out["mid_deflection_udl"] = self._get_mid_deflection_dz(
#                 mid_nodes=model_meta["mid_nodes"],
#                 loadcase=udl_lc,
#             )

#         if "mid_deflection_ts" in result_names:
#             out["mid_deflection_ts"] = (
#                 self._get_mid_deflection_dz(
#                     mid_nodes=model_meta["mid_nodes"],
#                     loadcase=ts_lc,
#                 )
#                 if ts_lc is not None
#                 else None
#             )

#         if "mid_deflection_ps" in result_names:
#             out["mid_deflection_ps"] = (
#                 self._get_mid_deflection_dz(
#                     mid_nodes=model_meta["mid_nodes"],
#                     loadcase=ps_lc,
#                 )
#                 if ps_lc is not None
#                 else None
#             )

#         if "mid_deflection_dz" in result_names or "mid_deflection_total" in result_names:
#             values = [
#                 self._get_mid_deflection_dz(
#                     mid_nodes=model_meta["mid_nodes"],
#                     loadcase=sw_lc,
#                 ),
#                 self._get_mid_deflection_dz(
#                     mid_nodes=model_meta["mid_nodes"],
#                     loadcase=udl_lc,
#                 ),
#             ]

#             if ts_lc is not None:
#                 values.append(
#                     self._get_mid_deflection_dz(
#                         mid_nodes=model_meta["mid_nodes"],
#                         loadcase=ts_lc,
#                     )
#                 )

#             if ps_lc is not None:
#                 values.append(
#                     self._get_mid_deflection_dz(
#                         mid_nodes=model_meta["mid_nodes"],
#                         loadcase=ps_lc,
#                     )
#                 )

#             total_deflection = self._sum_not_none(values)

#             if "mid_deflection_dz" in result_names:
#                 out["mid_deflection_dz"] = total_deflection

#             if "mid_deflection_total" in result_names:
#                 out["mid_deflection_total"] = total_deflection

#         # =========================
#         # LEFT SUPPORT REACTIONS
#         # =========================
#         if "left_reaction_sw" in result_names:
#             out["left_reaction_sw"] = self._get_support_reaction_fz(
#                 support_nodes=model_meta["left_nodes"],
#                 loadcase=sw_lc,
#             )

#         if "left_reaction_udl" in result_names:
#             out["left_reaction_udl"] = self._get_support_reaction_fz(
#                 support_nodes=model_meta["left_nodes"],
#                 loadcase=udl_lc,
#             )

#         if "left_reaction_ts" in result_names:
#             out["left_reaction_ts"] = (
#                 self._get_support_reaction_fz(
#                     support_nodes=model_meta["left_nodes"],
#                     loadcase=ts_lc,
#                 )
#                 if ts_lc is not None
#                 else None
#             )

#         if "left_reaction_ps" in result_names:
#             out["left_reaction_ps"] = (
#                 self._get_support_reaction_fz(
#                     support_nodes=model_meta["left_nodes"],
#                     loadcase=ps_lc,
#                 )
#                 if ps_lc is not None
#                 else None
#             )

#         if "left_reaction_fz" in result_names or "left_reaction_total" in result_names:
#             values = [
#                 self._get_support_reaction_fz(
#                     support_nodes=model_meta["left_nodes"],
#                     loadcase=sw_lc,
#                 ),
#                 self._get_support_reaction_fz(
#                     support_nodes=model_meta["left_nodes"],
#                     loadcase=udl_lc,
#                 ),
#             ]

#             if ts_lc is not None:
#                 values.append(
#                     self._get_support_reaction_fz(
#                         support_nodes=model_meta["left_nodes"],
#                         loadcase=ts_lc,
#                     )
#                 )

#             if ps_lc is not None:
#                 values.append(
#                     self._get_support_reaction_fz(
#                         support_nodes=model_meta["left_nodes"],
#                         loadcase=ps_lc,
#                     )
#                 )

#             total_left_reaction = self._sum_not_none(values)

#             if "left_reaction_fz" in result_names:
#                 out["left_reaction_fz"] = total_left_reaction

#             if "left_reaction_total" in result_names:
#                 out["left_reaction_total"] = total_left_reaction

#         # =========================
#         # RIGHT SUPPORT REACTIONS
#         # =========================
#         if "right_reaction_sw" in result_names:
#             out["right_reaction_sw"] = self._get_support_reaction_fz(
#                 support_nodes=model_meta["right_nodes"],
#                 loadcase=sw_lc,
#             )

#         if "right_reaction_udl" in result_names:
#             out["right_reaction_udl"] = self._get_support_reaction_fz(
#                 support_nodes=model_meta["right_nodes"],
#                 loadcase=udl_lc,
#             )

#         if "right_reaction_ts" in result_names:
#             out["right_reaction_ts"] = (
#                 self._get_support_reaction_fz(
#                     support_nodes=model_meta["right_nodes"],
#                     loadcase=ts_lc,
#                 )
#                 if ts_lc is not None
#                 else None
#             )

#         if "right_reaction_ps" in result_names:
#             out["right_reaction_ps"] = (
#                 self._get_support_reaction_fz(
#                     support_nodes=model_meta["right_nodes"],
#                     loadcase=ps_lc,
#                 )
#                 if ps_lc is not None
#                 else None
#             )

#         if "right_reaction_fz" in result_names or "right_reaction_total" in result_names:
#             values = [
#                 self._get_support_reaction_fz(
#                     support_nodes=model_meta["right_nodes"],
#                     loadcase=sw_lc,
#                 ),
#                 self._get_support_reaction_fz(
#                     support_nodes=model_meta["right_nodes"],
#                     loadcase=udl_lc,
#                 ),
#             ]

#             if ts_lc is not None:
#                 values.append(
#                     self._get_support_reaction_fz(
#                         support_nodes=model_meta["right_nodes"],
#                         loadcase=ts_lc,
#                     )
#                 )

#             if ps_lc is not None:
#                 values.append(
#                     self._get_support_reaction_fz(
#                         support_nodes=model_meta["right_nodes"],
#                         loadcase=ps_lc,
#                     )
#                 )

#             total_right_reaction = self._sum_not_none(values)

#             if "right_reaction_fz" in result_names:
#                 out["right_reaction_fz"] = total_right_reaction

#             if "right_reaction_total" in result_names:
#                 out["right_reaction_total"] = total_right_reaction

#         # =========================
#         # TOTAL SUPPORT REACTION
#         # useful equilibrium check
#         # =========================
#         if (
#             "support_reaction_total_sw" in result_names
#             or "support_reaction_total_udl" in result_names
#             or "support_reaction_total_ts" in result_names
#             or "support_reaction_total_ps" in result_names
#             or "support_reaction_total_fz" in result_names
#         ):
#             left_sw = self._get_support_reaction_fz(model_meta["left_nodes"], sw_lc)
#             right_sw = self._get_support_reaction_fz(model_meta["right_nodes"], sw_lc)

#             left_udl = self._get_support_reaction_fz(model_meta["left_nodes"], udl_lc)
#             right_udl = self._get_support_reaction_fz(model_meta["right_nodes"], udl_lc)

#             total_sw = self._sum_not_none([left_sw, right_sw])
#             total_udl = self._sum_not_none([left_udl, right_udl])

#             total_ts = None
#             if ts_lc is not None:
#                 left_ts = self._get_support_reaction_fz(model_meta["left_nodes"], ts_lc)
#                 right_ts = self._get_support_reaction_fz(model_meta["right_nodes"], ts_lc)
#                 total_ts = self._sum_not_none([left_ts, right_ts])

#             total_ps = None
#             if ps_lc is not None:
#                 left_ps = self._get_support_reaction_fz(model_meta["left_nodes"], ps_lc)
#                 right_ps = self._get_support_reaction_fz(model_meta["right_nodes"], ps_lc)
#                 total_ps = self._sum_not_none([left_ps, right_ps])

#             total_all = self._sum_not_none(
#                 [value for value in [total_sw, total_udl, total_ts, total_ps] if value is not None]
#             )

#             if "support_reaction_total_sw" in result_names:
#                 out["support_reaction_total_sw"] = total_sw

#             if "support_reaction_total_udl" in result_names:
#                 out["support_reaction_total_udl"] = total_udl

#             if "support_reaction_total_ts" in result_names:
#                 out["support_reaction_total_ts"] = total_ts

#             if "support_reaction_total_ps" in result_names:
#                 out["support_reaction_total_ps"] = total_ps

#             if "support_reaction_total_fz" in result_names:
#                 out["support_reaction_total_fz"] = total_all

#         # =========================
#         # MIDSPAN MOMENTS
#         # =========================
#         if "mid_moment_sw" in result_names:
#             out["mid_moment_sw"] = self._get_midspan_moment_my(
#                 beam_ids=model_meta["beam_ids"],
#                 loadcase=sw_lc,
#             )

#         if "mid_moment_udl" in result_names:
#             out["mid_moment_udl"] = self._get_midspan_moment_my(
#                 beam_ids=model_meta["beam_ids"],
#                 loadcase=udl_lc,
#             )

#         if "mid_moment_ts" in result_names:
#             out["mid_moment_ts"] = (
#                 self._get_midspan_moment_my(
#                     beam_ids=model_meta["beam_ids"],
#                     loadcase=ts_lc,
#                 )
#                 if ts_lc is not None
#                 else None
#             )

#         if "mid_moment_ps" in result_names:
#             out["mid_moment_ps"] = (
#                 self._get_midspan_moment_my(
#                     beam_ids=model_meta["beam_ids"],
#                     loadcase=ps_lc,
#                 )
#                 if ps_lc is not None
#                 else None
#             )

#         if "mid_moment_total" in result_names:
#             values = [
#                 self._get_midspan_moment_my(
#                     beam_ids=model_meta["beam_ids"],
#                     loadcase=sw_lc,
#                 ),
#                 self._get_midspan_moment_my(
#                     beam_ids=model_meta["beam_ids"],
#                     loadcase=udl_lc,
#                 ),
#             ]

#             if ts_lc is not None:
#                 values.append(
#                     self._get_midspan_moment_my(
#                         beam_ids=model_meta["beam_ids"],
#                         loadcase=ts_lc,
#                     )
#                 )

#             if ps_lc is not None:
#                 values.append(
#                     self._get_midspan_moment_my(
#                         beam_ids=model_meta["beam_ids"],
#                         loadcase=ps_lc,
#                     )
#                 )

#             out["mid_moment_total"] = self._sum_not_none(values)

#         return out

#     def _get_mid_deflection_dz(self, mid_nodes: list[int], loadcase: str):
#         return self._get_single_result_value(
#             table_type="DISPLACEMENTG",
#             keys=mid_nodes,
#             loadcase=loadcase,
#             column_candidates=["DZ"],
#         )

#     def _get_support_reaction_fz(self, support_nodes: list[int], loadcase: str):
#         return self._get_single_result_value(
#             table_type="REACTIONG",
#             keys=support_nodes,
#             loadcase=loadcase,
#             column_candidates=["FZ"],
#         )

#     def _get_single_result_value(
#         self,
#         table_type: str,
#         keys: list[int],
#         loadcase: str,
#         column_candidates: list[str],
#     ):
#         if loadcase is None:
#             return None

#         df = Result.TABLE(
#             table_type,
#             keys=keys,
#             loadcase=[loadcase],
#         )

#         if df is None or df.height == 0:
#             return None

#         for column_name in column_candidates:
#             if column_name in df.columns:
#                 value = df[column_name][0]
#                 try:
#                     return float(value)
#                 except Exception:
#                     return value

#         return None

#     def _get_midspan_moment_my(self, beam_ids: list[int], loadcase: str):
#         if not beam_ids or loadcase is None:
#             return None

#         left_mid_beam_id = beam_ids[len(beam_ids) // 2 - 1]

#         df = Result.TABLE.BeamForce(
#             keys=[left_mid_beam_id],
#             loadcase=[loadcase],
#             parts=["PartJ"],
#         )

#         if df is None or df.height == 0:
#             return None

#         for column_name in ["Moment-y", "My", "MY"]:
#             if column_name in df.columns:
#                 value = df[column_name][0]
#                 try:
#                     return float(value)
#                 except Exception:
#                     return value

#         return None

#     def _sum_not_none(self, values: list):
#         numeric_values = [v for v in values if v is not None]
#         if not numeric_values:
#             return None
#         return sum(numeric_values)

from midas_civil import Result

from experiment.experiment_config import ExperimentConfig


class ResultCollector:
    def __init__(self, config: ExperimentConfig):
        self.config = config

    def collect(self, model_meta: dict) -> dict:
        out = {}

        loadcases = {
            "sw": model_meta.get("self_weight_result_name"),
            "udl": model_meta.get("udl_case_result_name"),
            "ts": model_meta.get("ts_case_result_name"),
            "ps": model_meta.get("prestress_case_result_name"),
        }

        loadcases = {
            name: loadcase
            for name, loadcase in loadcases.items()
            if loadcase is not None
        }

        all_nodes = model_meta["all_nodes"]
        beam_ids = model_meta["beam_ids"]
        support_nodes = model_meta["support_nodes"]

        deflections_dz = {}
        moments_my = {}
        reactions_fz = {}

        for case_name, loadcase in loadcases.items():
            deflections_dz[case_name] = self._get_deflections_by_node(
                nodes=all_nodes,
                loadcase=loadcase,
            )

            moments_my[case_name] = self._get_moments_my_by_node(
                beam_ids=beam_ids,
                loadcase=loadcase,
            )

            reactions_fz[case_name] = self._get_reactions_by_support(
                support_nodes=support_nodes,
                loadcase=loadcase,
            )

        deflections_dz["total"] = self._sum_node_series(deflections_dz.values())
        moments_my["total"] = self._sum_node_series(moments_my.values())
        reactions_fz["total"] = self._sum_support_series(reactions_fz.values())

        out["deflections_dz"] = deflections_dz
        out["moments_my"] = moments_my
        out["reactions_fz"] = reactions_fz

        return out
    def _get_moments_my_by_node(
        self,
        beam_ids: list[int],
        loadcase: str,
    ) -> dict[int, float]:
        if not beam_ids or loadcase is None:
            return {}

        df = Result.TABLE.BeamForce(
            keys=beam_ids,
            loadcase=[loadcase],
            parts=["PartJ"],
            components=["all"],
        )

        if df is None or df.height == 0:
            return {}

        out = {}

        elem_to_index = {
            elem_id: index
            for index, elem_id in enumerate(beam_ids)
        }

        for row in df.iter_rows(named=True):
            elem_id = self._get_first_existing_value(
                row,
                ["Elem", "ELEM", "Element", "Element No.", "ElementNo"],
            )

            if elem_id is None:
                continue

            elem_id = int(elem_id)

            if elem_id not in elem_to_index:
                continue

            value = self._get_first_existing_value(
                row,
                ["Moment-y", "My", "MY", "Moment-y(kN*m)", "My(kN*m)"],
            )

            if value is None:
                continue

            node_id = elem_to_index[elem_id] + 2
            out[node_id] = float(value)

        return out
    
    def _get_deflections_by_node(
        self,
        nodes: list[int],
        loadcase: str,
    ) -> dict[int, float]:
        if not nodes or loadcase is None:
            return {}

        df = Result.TABLE(
            "DISPLACEMENTG",
            keys=nodes,
            loadcase=[loadcase],
        )

        if df is None or df.height == 0:
            return {}

        out = {}

        for row in df.iter_rows(named=True):
            node_id = self._get_first_existing_value(
                row,
                ["Node", "NODE", "Node No.", "NodeNo"],
            )

            dz = self._get_first_existing_value(
                row,
                ["DZ", "Dz", "dz"],
            )

            if node_id is None or dz is None:
                continue

            out[int(node_id)] = float(dz)

        return out

    def _get_beam_force_component_by_node(
        self,
        beam_ids: list[int],
        loadcase: str,
        component_candidates: list[str],
        use_static_prestress: bool = False,
    ) -> dict[int, dict[str, float]]:
        if not beam_ids or loadcase is None:
            return {}

        if use_static_prestress:
            df = Result.TABLE.BeamForce_StaticPrestress(
                keys=beam_ids,
                loadcase=[loadcase],
                parts=["PartI", "PartJ"],
                components=["all"],
            )
        else:
            df = Result.TABLE.BeamForce(
                keys=beam_ids,
                loadcase=[loadcase],
                parts=["PartI", "PartJ"],
                components=["all"],
            )

        if df is None or df.height == 0:
            print(f"No beam force results for loadcase: {loadcase}")
            return {}

        print(f"Beam force columns for {loadcase}: {df.columns}")

        out = {}

        elem_to_index = {
            elem_id: index
            for index, elem_id in enumerate(beam_ids)
        }

        for beam_index, _ in enumerate(beam_ids):
            out.setdefault(beam_index + 1, {})
            out.setdefault(beam_index + 2, {})

        for row in df.iter_rows(named=True):
            elem_id = self._get_first_existing_value(
                row,
                ["Elem", "ELEM", "Element", "Element No.", "ElementNo"],
            )

            part = self._get_first_existing_value(
                row,
                ["Part", "PART"],
            )

            if elem_id is None or part is None:
                continue

            elem_id = int(elem_id)
            part = str(part)

            if elem_id not in elem_to_index:
                continue

            beam_index = elem_to_index[elem_id]

            value = self._get_first_existing_value(
                row,
                component_candidates,
            )

            if value is None:
                continue

            if part in ("PartI", "I") or part.startswith("I"):
                node_id = beam_index + 1
                side = "from_right"

            elif part in ("PartJ", "J") or part.startswith("J"):
                node_id = beam_index + 2
                side = "from_left"

            else:
                continue

            out.setdefault(node_id, {})
            out[node_id][side] = float(value)

        return out

    def _get_reactions_by_support(
        self,
        support_nodes: dict[str, list[int]],
        loadcase: str,
    ) -> dict[str, float | None]:
        if not support_nodes or loadcase is None:
            return {}

        out = {}

        for support_name, nodes in support_nodes.items():
            if not nodes:
                out[support_name] = None
                continue

            df = Result.TABLE(
                "REACTIONG",
                keys=nodes,
                loadcase=[loadcase],
            )

            if df is None or df.height == 0:
                out[support_name] = None
                continue

            values = []

            for row in df.iter_rows(named=True):
                fz = self._get_first_existing_value(
                    row,
                    ["FZ", "Fz", "fz"],
                )

                if fz is not None:
                    values.append(float(fz))

            out[support_name] = sum(values) if values else None

        return out

    def _sum_node_series(self, series_list) -> dict[int, float]:
        out = {}

        for series in series_list:
            for node_id, value in series.items():
                if value is None:
                    continue

                out[node_id] = out.get(node_id, 0.0) + value

        return out

    def _sum_node_side_series(self, series_list) -> dict[int, dict[str, float]]:
        out = {}

        for series in series_list:
            for node_id, side_values in series.items():
                out.setdefault(node_id, {})

                for side, value in side_values.items():
                    if value is None:
                        continue

                    out[node_id][side] = out[node_id].get(side, 0.0) + value

        return out

    def _sum_support_series(self, series_list) -> dict[str, float]:
        out = {}

        for series in series_list:
            for support_name, value in series.items():
                if value is None:
                    continue

                out[support_name] = out.get(support_name, 0.0) + value

        return out

    def _get_first_existing_value(
        self,
        row: dict,
        column_candidates: list[str],
    ):
        for column_name in column_candidates:
            if column_name in row and row[column_name] is not None:
                return row[column_name]

        return None