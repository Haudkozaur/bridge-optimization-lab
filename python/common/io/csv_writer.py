import csv
import os

from common.io.csv_schema import flatten_dict, build_fieldnames


class CsvWriter:
    INPUT_COLUMNS = [
        "model_index",
        "model_type",
        "tendon_shape_type",

        "left_span_length_m",
        "left_beam_divisions",
        "right_span_length_m",
        "right_beam_divisions",

        "beam_height_m",
        "beam_width_m",
        "udl_kn_per_m",

        "n_tendons",
        "tendon_force_kn",
        "tendon_area_mm2",

        "tendon_ecc_left_m",
        "tendon_ecc_left_span_mid_m",
        "tendon_ecc_mid_support_m",
        "tendon_ecc_right_span_mid_m",
        "tendon_ecc_right_m",
    ]

    LOAD_CASES = ["sw", "udl", "ps", "ts", "total"]
    SUPPORTS = ["left", "middle", "right"]

    STATUS_COLUMNS = [
        "analysis_status",
        "error_message",
    ]

    def __init__(
        self,
        output_path: str,
        max_node_id: int | None = None,
        input_columns: list[str] | None = None,
    ):
        self.output_path = output_path
        self.max_node_id = max_node_id
        self.input_columns = input_columns or self.INPUT_COLUMNS
        self.fieldnames = self._build_fixed_fieldnames() if max_node_id is not None else None

    def write_row(self, row: dict) -> None:
        if self.max_node_id is None:
            self.write_rows([row])
            return

        output_dir = os.path.dirname(self.output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        flat_row = flatten_dict(row)

        fixed_row = {
            field: flat_row.get(field, "")
            for field in self.fieldnames
        }

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

    def write_rows(
        self,
        rows: list[dict],
        preferred_order: list[str] | None = None,
    ) -> None:
        if not rows:
            return

        output_dir = os.path.dirname(self.output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        flat_rows = [flatten_dict(row) for row in rows]

        if self.max_node_id is not None:
            fieldnames = self.fieldnames
            flat_rows = [
                {field: row.get(field, "") for field in fieldnames}
                for row in flat_rows
            ]
        else:
            fieldnames = build_fieldnames(flat_rows, preferred_order)

        with open(self.output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(flat_rows)

    def _build_fixed_fieldnames(self) -> list[str]:
        fieldnames = []
        fieldnames.extend(self.input_columns)

        for case in self.LOAD_CASES:
            for node_id in range(1, self.max_node_id + 1):
                fieldnames.append(f"deflections_dz_{case}_{node_id}")

        for case in self.LOAD_CASES:
            for node_id in range(1, self.max_node_id + 1):
                fieldnames.append(f"moments_my_{case}_{node_id}")

        for case in self.LOAD_CASES:
            for support in self.SUPPORTS:
                fieldnames.append(f"reactions_fz_{case}_{support}")

        fieldnames.extend(self.STATUS_COLUMNS)

        return fieldnames