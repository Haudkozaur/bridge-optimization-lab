from midas_civil import Result

from configs.midas_run_config import MidasRunConfig


class ResultCollector:
    def __init__(self, config: MidasRunConfig):
        self.config = config

    def collect(self, model_meta: dict) -> dict:
        out = {}

        loadcases = {
            "sw": model_meta.get("self_weight_result_name"),
            "udl": model_meta.get("udl_case_result_name"),
            # "ts": model_meta.get("ts_case_result_name"),
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
            parts=["PartI", "PartJ"],
            components=["all"],
        )

        if df is None or df.height == 0:
            return {}

        elem_to_index = {
            elem_id: index
            for index, elem_id in enumerate(beam_ids)
        }

        values_by_node = {}

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

            value = self._get_first_existing_value(
                row,
                ["Moment-y", "My", "MY", "Moment-y(kN*m)", "My(kN*m)"],
            )

            if value is None:
                continue

            beam_index = elem_to_index[elem_id]

            if part in ("PartI", "I") or part.startswith("I"):
                node_id = beam_index + 1
            elif part in ("PartJ", "J") or part.startswith("J"):
                node_id = beam_index + 2
            else:
                continue

            values_by_node.setdefault(node_id, [])
            values_by_node[node_id].append(float(value))

        out = {}

        for node_id, values in values_by_node.items():
            if not values:
                continue

            out[node_id] = float(sum(values) / len(values))

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