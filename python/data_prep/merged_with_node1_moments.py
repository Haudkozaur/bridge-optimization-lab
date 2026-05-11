import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

input_dir = BASE_DIR / "models_data" / "results_to_merge"

INPUT_FILE = next(input_dir.glob("results_merged_*.csv"))
OUTPUT_FILE = input_dir / "results_merged_with_node1_moments.csv"

PRESTRESS_FORCE_KN = 660.0

MOMENT_NODE_1_COLUMNS = [
    "moments_my_sw_1",
    "moments_my_udl_1",
    "moments_my_ps_1",
    "moments_my_total_1",
]


def to_float(value):
    if value is None or value == "":
        return None
    return float(value)


def add_column_after(fieldnames, new_column, after_column):
    if new_column in fieldnames:
        return fieldnames

    if after_column not in fieldnames:
        fieldnames.append(new_column)
        return fieldnames

    index = fieldnames.index(after_column) + 1
    fieldnames.insert(index, new_column)
    return fieldnames


def build_output_fieldnames(input_fieldnames):
    fieldnames = list(input_fieldnames)

    # Wstawiamy *_1 przed istniejące moments_my_*_2,
    # żeby układ kolumn był naturalny: 1, 2, 3...
    fieldnames = add_column_after(
        fieldnames,
        "moments_my_sw_1",
        "deflections_dz_total_41",
    )

    fieldnames = add_column_after(
        fieldnames,
        "moments_my_udl_1",
        "moments_my_sw_41",
    )

    fieldnames = add_column_after(
        fieldnames,
        "moments_my_ps_1",
        "moments_my_udl_41",
    )

    fieldnames = add_column_after(
        fieldnames,
        "moments_my_total_1",
        "moments_my_ps_41",
    )

    return fieldnames


def main():
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)

    with input_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        input_fieldnames = reader.fieldnames or []

    output_fieldnames = build_output_fieldnames(input_fieldnames)

    for row in rows:
        tendon_ecc_left_m = to_float(row.get("tendon_ecc_left_m"))

        if tendon_ecc_left_m is None:
            ps_moment_node_1 = ""
        else:
            ps_moment_node_1 = tendon_ecc_left_m * PRESTRESS_FORCE_KN

        row["moments_my_sw_1"] = 0.0
        row["moments_my_udl_1"] = 0.0
        row["moments_my_ps_1"] = ps_moment_node_1
        row["moments_my_total_1"] = ps_moment_node_1

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Input:  {input_path}")
    print(f"Saved:  {output_path}")
    print(f"Rows:   {len(rows)}")


if __name__ == "__main__":
    main()