import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

input_dir = BASE_DIR / "models_data" / "results_to_merge"

INPUT_FILE = input_dir / "results_merged_with_node1_moments.csv"
OUTPUT_FILE = input_dir / "results_ml_ready.csv"

LOAD_CASES = ["sw", "udl", "ps", "total"]
RESULT_TYPES = ["deflections_dz", "moments_my"]


def to_float(value):
    if value is None or value == "":
        return None
    return float(value)


def get_node_value(row, prefix, node_id):
    key = f"{prefix}_{node_id}"
    return to_float(row.get(key))


def collect_span_values(row, prefix, node_ids):
    values = []

    for node_id in node_ids:
        value = get_node_value(row, prefix, node_id)
        if value is not None:
            values.append((node_id, value))

    return values


def extract_extremes(values):
    if not values:
        return {
            "min": None,
            "min_node": None,
            "max": None,
            "max_node": None,
            "abs_max": None,
            "abs_max_node": None,
        }

    min_node, min_val = min(values, key=lambda x: x[1])
    max_node, max_val = max(values, key=lambda x: x[1])
    abs_node, abs_val = max(values, key=lambda x: abs(x[1]))

    return {
        "min": min_val,
        "min_node": min_node,
        "max": max_val,
        "max_node": max_node,
        "abs_max": abs_val,
        "abs_max_node": abs_node,
    }


def add_extremes(output_row, row, result_type, load_case, side_name, node_ids):
    prefix = f"{result_type}_{load_case}"
    values = collect_span_values(row, prefix, node_ids)
    extremes = extract_extremes(values)

    base = f"{prefix}_{side_name}"

    output_row[f"{base}_min"] = extremes["min"]
    output_row[f"{base}_min_node"] = extremes["min_node"]
    output_row[f"{base}_max"] = extremes["max"]
    output_row[f"{base}_max_node"] = extremes["max_node"]
    output_row[f"{base}_abs_max"] = extremes["abs_max"]
    output_row[f"{base}_abs_max_node"] = extremes["abs_max_node"]


def main():
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)

    with input_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    output_rows = []

    for row in rows:
        if row.get("analysis_status") != "OK":
            continue

        left_divisions = int(float(row["left_beam_divisions"]))
        right_divisions = int(float(row["right_beam_divisions"]))

        left_support_node = 1
        middle_node = left_divisions + 1
        right_support_node = left_divisions + right_divisions + 1

        left_span_nodes = list(range(1, middle_node))
        right_span_nodes = list(range(middle_node + 1, right_support_node+1))

        output_row = {}

        input_columns = [
            "beam_height_m",
            "beam_width_m",
            "left_span_length_m",
            "right_span_length_m",
            "model_index",
            "n_tendons",
            "tendon_area_mm2",
            "tendon_ecc_left_m",
            "tendon_ecc_left_span_mid_m",
            "tendon_ecc_mid_support_m",
            "tendon_ecc_right_span_mid_m",
            "tendon_ecc_right_m",
            "tendon_force_kn",
            "tendon_shape_type",
            "udl_kn_per_m",
            "left_beam_divisions",
            "right_beam_divisions",
        ]

        for col in input_columns:
            output_row[col] = row.get(col)

        output_row["left_support_node"] = left_support_node
        output_row["middle_support_node"] = middle_node
        output_row["right_support_node"] = right_support_node

        # reakcje
        for load_case in LOAD_CASES:
            for support in ["left", "middle", "right"]:
                col = f"reactions_fz_{load_case}_{support}"
                output_row[col] = row.get(col)

        # wyniki nodowe redukowane do ekstremów + wartości podporowe
        for result_type in RESULT_TYPES:
            for load_case in LOAD_CASES:
                prefix = f"{result_type}_{load_case}"

                if result_type == "moments_my":
                    output_row[f"{prefix}_left_support"] = get_node_value(
                        row,
                        prefix,
                        left_support_node,
                    )

                add_extremes(
                    output_row,
                    row,
                    result_type,
                    load_case,
                    "left_span",
                    left_span_nodes,
                )

                output_row[f"{prefix}_middle_support"] = get_node_value(
                    row,
                    prefix,
                    middle_node,
                )

                add_extremes(
                    output_row,
                    row,
                    result_type,
                    load_case,
                    "right_span",
                    right_span_nodes,
                )

                if result_type == "moments_my":
                    output_row[f"{prefix}_right_support"] = get_node_value(
                        row,
                        prefix,
                        right_support_node,
                    )

        output_row["analysis_status"] = row.get("analysis_status")
        output_row["error_message"] = row.get("error_message")

        output_rows.append(output_row)

    if not output_rows:
        print("No valid rows found.")
        return

    fieldnames = list(output_rows[0].keys())

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Input: {input_path}")
    print(f"Saved: {output_path}")
    print(f"Rows:  {len(output_rows)}")


if __name__ == "__main__":
    main()