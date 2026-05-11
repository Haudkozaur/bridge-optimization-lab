# import csv
# import os
# import re


# class CsvWriter:
#     def __init__(self, output_path: str):
#         self.output_path = output_path
#         self.fieldnames = None

#     def write_row(self, row: dict) -> None:
#         output_dir = os.path.dirname(self.output_path)
#         if output_dir:
#             os.makedirs(output_dir, exist_ok=True)

#         flat_row = self._flatten_dict(row)

#         if not os.path.exists(self.output_path):
#             self.fieldnames = self._build_ordered_fieldnames([flat_row])
#             self._write_all_rows([flat_row], self.fieldnames)
#             return

#         existing_rows, existing_fieldnames = self._read_existing_csv()

#         all_rows = existing_rows + [flat_row]

#         all_keys = set(existing_fieldnames)
#         all_keys.update(flat_row.keys())

#         self.fieldnames = self._build_ordered_fieldnames_from_keys(all_keys)

#         self._write_all_rows(all_rows, self.fieldnames)

#     def write(self, rows: list[dict]) -> None:
#         for row in rows:
#             self.write_row(row)

#     def _read_existing_csv(self) -> tuple[list[dict], list[str]]:
#         if not os.path.exists(self.output_path):
#             return [], []

#         with open(self.output_path, "r", newline="", encoding="utf-8") as f:
#             reader = csv.DictReader(f)
#             fieldnames = reader.fieldnames or []
#             rows = list(reader)

#         return rows, fieldnames

#     def _write_all_rows(self, rows: list[dict], fieldnames: list[str]) -> None:
#         temp_path = self.output_path + ".tmp"

#         with open(temp_path, "w", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(
#                 f,
#                 fieldnames=fieldnames,
#                 extrasaction="ignore",
#             )
#             writer.writeheader()
#             writer.writerows(rows)

#         os.replace(temp_path, self.output_path)

#     def _flatten_dict(self, data: dict, prefix: str = "") -> dict:
#         out = {}

#         for key, value in data.items():
#             new_key = f"{prefix}_{key}" if prefix else str(key)

#             if isinstance(value, dict):
#                 if all(isinstance(k, int) for k in value.keys()):
#                     for node_id in sorted(value.keys()):
#                         node_val = value[node_id]
#                         node_key = f"{new_key}_{node_id}"

#                         if isinstance(node_val, dict):
#                             for side, v in node_val.items():
#                                 out[f"{node_key}_{side}"] = v
#                         else:
#                             out[node_key] = node_val
#                 else:
#                     out.update(self._flatten_dict(value, new_key))
#             else:
#                 out[new_key] = value

#         return out

#     def _build_ordered_fieldnames(self, rows: list[dict]) -> list[str]:
#         all_keys = set()

#         for row in rows:
#             all_keys.update(row.keys())

#         return self._build_ordered_fieldnames_from_keys(all_keys)

#     def _build_ordered_fieldnames_from_keys(self, all_keys: set[str]) -> list[str]:
#         inputs = []

#         deflections_sw = []
#         deflections_udl = []
#         deflections_ps = []
#         deflections_ts = []
#         deflections_total = []

#         moments_sw = []
#         moments_udl = []
#         moments_ps = []
#         moments_ts = []
#         moments_total = []

#         reactions_sw = []
#         reactions_udl = []
#         reactions_ps = []
#         reactions_ts = []
#         reactions_total = []

#         status = []
#         others = []

#         for key in all_keys:
#             if key.startswith("deflections_dz_sw_"):
#                 deflections_sw.append(key)
#             elif key.startswith("deflections_dz_udl_"):
#                 deflections_udl.append(key)
#             elif key.startswith("deflections_dz_ps_"):
#                 deflections_ps.append(key)
#             elif key.startswith("deflections_dz_ts_"):
#                 deflections_ts.append(key)
#             elif key.startswith("deflections_dz_total_"):
#                 deflections_total.append(key)

#             elif key.startswith("moments_my_sw_"):
#                 moments_sw.append(key)
#             elif key.startswith("moments_my_udl_"):
#                 moments_udl.append(key)
#             elif key.startswith("moments_my_ps_"):
#                 moments_ps.append(key)
#             elif key.startswith("moments_my_ts_"):
#                 moments_ts.append(key)
#             elif key.startswith("moments_my_total_"):
#                 moments_total.append(key)

#             elif key.startswith("reactions_fz_sw_"):
#                 reactions_sw.append(key)
#             elif key.startswith("reactions_fz_udl_"):
#                 reactions_udl.append(key)
#             elif key.startswith("reactions_fz_ps_"):
#                 reactions_ps.append(key)
#             elif key.startswith("reactions_fz_ts_"):
#                 reactions_ts.append(key)
#             elif key.startswith("reactions_fz_total_"):
#                 reactions_total.append(key)

#             elif key in ("analysis_status", "error_message"):
#                 status.append(key)

#             elif self._is_input_key(key):
#                 inputs.append(key)

#             else:
#                 others.append(key)

#         return (
#             sorted(inputs, key=self._natural_key)
#             + sorted(deflections_sw, key=self._natural_key)
#             + sorted(deflections_udl, key=self._natural_key)
#             + sorted(deflections_ps, key=self._natural_key)
#             + sorted(deflections_ts, key=self._natural_key)
#             + sorted(deflections_total, key=self._natural_key)
#             + sorted(moments_sw, key=self._natural_key)
#             + sorted(moments_udl, key=self._natural_key)
#             + sorted(moments_ps, key=self._natural_key)
#             + sorted(moments_ts, key=self._natural_key)
#             + sorted(moments_total, key=self._natural_key)
#             + sorted(reactions_sw, key=self._natural_key)
#             + sorted(reactions_udl, key=self._natural_key)
#             + sorted(reactions_ps, key=self._natural_key)
#             + sorted(reactions_ts, key=self._natural_key)
#             + sorted(reactions_total, key=self._natural_key)
#             + sorted(status, key=self._natural_key)
#             + sorted(others, key=self._natural_key)
#         )

#     def _natural_key(self, value: str):
#         return [
#             int(part) if part.isdigit() else part
#             for part in re.split(r"(\d+)", value)
#         ]

#     def _is_input_key(self, key: str) -> bool:
#         return key.startswith(
#             (
#                 "model_index",
#                 "model_type",
#                 "left_span",
#                 "right_span",
#                 "total_span",
#                 "span",
#                 "beam",
#                 "udl",
#                 "n_tendons",
#                 "tendon",
#                 "concrete",
#                 "section",
#             )
#         )
import csv
import os


class CsvWriter:
    MAX_NODES = 41

    INPUT_COLUMNS = [
        "beam_height_m",
        "beam_width_m",
        "left_span_length_m",
        "model_index",
        "n_tendons",
        "right_span_length_m",
        "tendon_area_mm2",
        "tendon_ecc_left_m",
        "tendon_ecc_left_span_mid_m",
        "tendon_ecc_mid_support_m",
        "tendon_ecc_right_m",
        "tendon_ecc_right_span_mid_m",
        "tendon_force_kn",
        "tendon_shape_type",
        "udl_kn_per_m",
    ]

    DEFLECTION_CASES = ["sw", "udl", "ps", "total"]
    MOMENT_CASES = ["sw", "udl", "ps", "total"]
    REACTION_CASES = ["sw", "udl", "ps", "total"]
    SUPPORTS = ["left", "middle", "right"]

    STATUS_COLUMNS = [
        "analysis_status",
        "error_message",
        "left_beam_divisions",
        "right_beam_divisions",
    ]

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.fieldnames = self._build_fixed_fieldnames()

    def write_row(self, row: dict) -> None:
        output_dir = os.path.dirname(self.output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        flat_row = self._flatten_dict(row)
        fixed_row = {field: flat_row.get(field, "") for field in self.fieldnames}

        file_exists = os.path.exists(self.output_path)
        file_is_empty = (not file_exists) or os.path.getsize(self.output_path) == 0

        with open(self.output_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self.fieldnames,
                extrasaction="ignore",
            )

            if file_is_empty:
                writer.writeheader()

            writer.writerow(fixed_row)

    def write(self, rows: list[dict]) -> None:
        for row in rows:
            self.write_row(row)

    def _build_fixed_fieldnames(self) -> list[str]:
        fieldnames = []
        fieldnames.extend(self.INPUT_COLUMNS)

        for case in self.DEFLECTION_CASES:
            for node_id in range(1, self.MAX_NODES + 1):
                fieldnames.append(f"deflections_dz_{case}_{node_id}")

        for case in self.MOMENT_CASES:
            for node_id in range(2, self.MAX_NODES + 1):
                fieldnames.append(f"moments_my_{case}_{node_id}")

        for case in self.REACTION_CASES:
            for support in self.SUPPORTS:
                fieldnames.append(f"reactions_fz_{case}_{support}")

        fieldnames.extend(self.STATUS_COLUMNS)
        return fieldnames

    def _flatten_dict(self, data: dict, prefix: str = "") -> dict:
        out = {}

        for key, value in data.items():
            new_key = f"{prefix}_{key}" if prefix else str(key)

            if isinstance(value, dict):
                if all(isinstance(k, int) for k in value.keys()):
                    for node_id in sorted(value.keys()):
                        node_val = value[node_id]
                        node_key = f"{new_key}_{node_id}"

                        if isinstance(node_val, dict):
                            for side, v in node_val.items():
                                out[f"{node_key}_{side}"] = v
                        else:
                            out[node_key] = node_val
                else:
                    out.update(self._flatten_dict(value, new_key))
            else:
                out[new_key] = value

        return out