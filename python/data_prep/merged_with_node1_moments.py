import csv
from pathlib import Path


INPUT_FILES = [
    Path(r"D:\Doktorat\bridge-optimization-lab\python\model_outputs\models_data\midas_run_20260515_105022\midas_output.csv"),
    Path(r"D:\Doktorat\bridge-optimization-lab\python\model_outputs\models_data\solver_run_20260515_104212\solver_output.csv"),
]

PRESTRESS_FORCE_KN = 660.0


def to_float(value):
    if value is None or value == "":
        return None
    return float(value)


def add_column_after(fieldnames, new_column, after_column):
    if new_column in fieldnames:
        return fieldnames

    if after_column in fieldnames:
        index = fieldnames.index(after_column) + 1
        fieldnames.insert(index, new_column)
    else:
        fieldnames.append(new_column)

    return fieldnames


def build_output_fieldnames(input_fieldnames, max_node_id: int):
    fieldnames = list(input_fieldnames)

    # Node 1
    fieldnames = add_column_after(fieldnames, "moments_my_sw_1", "deflections_dz_total_41")
    fieldnames = add_column_after(fieldnames, "moments_my_udl_1", "moments_my_sw_41")
    fieldnames = add_column_after(fieldnames, "moments_my_ps_1", "moments_my_udl_41")
    fieldnames = add_column_after(fieldnames, "moments_my_total_1", "moments_my_ps_41")

    # Last node
    last = max_node_id
    fieldnames = add_column_after(fieldnames, f"moments_my_sw_{last}", f"moments_my_sw_{last - 1}")
    fieldnames = add_column_after(fieldnames, f"moments_my_udl_{last}", f"moments_my_udl_{last - 1}")
    fieldnames = add_column_after(fieldnames, f"moments_my_ps_{last}", f"moments_my_ps_{last - 1}")
    fieldnames = add_column_after(fieldnames, f"moments_my_total_{last}", f"moments_my_total_{last - 1}")

    return fieldnames


def get_max_node_id_from_header(fieldnames):
    max_id = 0

    for col in fieldnames:
        if col.startswith("deflections_dz_total_"):
            try:
                node_id = int(col.split("_")[-1])
                max_id = max(max_id, node_id)
            except ValueError:
                pass

    if max_id == 0:
        raise ValueError("Could not detect max node id from deflections_dz_total_* columns")

    return max_id


def process_file(input_path: Path):
    output_path = input_path.with_name(input_path.stem + "_with_end_moments.csv")

    with input_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        input_fieldnames = reader.fieldnames or []

    max_node_id = get_max_node_id_from_header(input_fieldnames)
    output_fieldnames = build_output_fieldnames(input_fieldnames, max_node_id)

    for row in rows:
        tendon_ecc_left_m = to_float(row.get("tendon_ecc_left_m"))
        tendon_ecc_right_m = to_float(row.get("tendon_ecc_right_m"))

        if tendon_ecc_left_m is None:
            ps_moment_node_1 = ""
        else:
            ps_moment_node_1 = tendon_ecc_left_m * PRESTRESS_FORCE_KN

        if tendon_ecc_right_m is None:
            ps_moment_last_node = ""
        else:
            ps_moment_last_node = tendon_ecc_right_m * PRESTRESS_FORCE_KN

        row["moments_my_sw_1"] = 0.0
        row["moments_my_udl_1"] = 0.0
        row["moments_my_ps_1"] = ps_moment_node_1
        row["moments_my_total_1"] = ps_moment_node_1

        row[f"moments_my_sw_{max_node_id}"] = 0.0
        row[f"moments_my_udl_{max_node_id}"] = 0.0
        row[f"moments_my_ps_{max_node_id}"] = ps_moment_last_node
        row[f"moments_my_total_{max_node_id}"] = ps_moment_last_node

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Input:  {input_path}")
    print(f"Saved:  {output_path}")
    print(f"Rows:   {len(rows)}")
    print()


def main():
    for input_file in INPUT_FILES:
        process_file(input_file)


if __name__ == "__main__":
    main()