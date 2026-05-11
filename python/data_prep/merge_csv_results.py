from pathlib import Path
import csv
import shutil
from datetime import datetime


SOURCE_DIR = Path(
    r"D:\Doktorat\Midas_nauka\MidasBulkRunner\midas-bulk-runner\models_data\results_to_merge"
)


def detect_delimiter(path: Path) -> str:
    with open(path, "r", encoding="utf-8", newline="") as f:
        sample = f.read(4096)

    try:
        return csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";"]).delimiter
    except csv.Error:
        return ","


def read_header(path: Path) -> tuple[list[str], str]:
    delimiter = detect_delimiter(path)

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = next(reader, None)

    return header or [], delimiter


def iter_data_rows(path: Path, delimiter: str):
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        next(reader, None)

        for row in reader:
            if row:
                yield row


def find_csv_files(source_dir: Path, output_path: Path) -> list[Path]:
    return sorted(
        file
        for file in source_dir.glob("*.csv")
        if file.is_file()
        and file.resolve() != output_path.resolve()
    )


def merge_csv_files() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Folder does not exist: {SOURCE_DIR}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = SOURCE_DIR / f"results_merged_{timestamp}.csv"
    archive_dir = SOURCE_DIR / f"merged_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=False)

    csv_files = find_csv_files(SOURCE_DIR, output_path)

    if not csv_files:
        print("No CSV files found.")
        archive_dir.rmdir()
        return

    base_header = None
    merged_files: list[Path] = []
    skipped_files: list[Path] = []
    written_rows = 0

    with open(output_path, "w", encoding="utf-8", newline="") as out_f:
        writer = None

        for path in csv_files:
            header, delimiter = read_header(path)

            if not header:
                print(f"SKIP: empty or invalid CSV: {path.name}")
                skipped_files.append(path)
                continue

            if base_header is None:
                base_header = header
                writer = csv.writer(out_f, delimiter=",")
                writer.writerow(base_header)
                print(f"BASE: {path.name}")

            elif header != base_header:
                print(f"SKIP: different column layout: {path.name}")
                print(f"      expected columns: {len(base_header)}, got: {len(header)}")
                skipped_files.append(path)
                continue

            rows_in_file = 0

            for row in iter_data_rows(path, delimiter):
                writer.writerow(row)
                rows_in_file += 1

            merged_files.append(path)
            written_rows += rows_in_file

            print(f"MERGED: {path.name} | rows: {rows_in_file}")

    for path in merged_files:
        target_path = archive_dir / path.name
        shutil.move(str(path), str(target_path))

    print("\nDONE")
    print(f"Output: {output_path}")
    print(f"Moved merged source files to: {archive_dir}")
    print(f"Merged files: {len(merged_files)}")
    print(f"Skipped files: {len(skipped_files)}")
    print(f"Rows written: {written_rows}")

    if skipped_files:
        print("\nSkipped files were left in source folder:")
        for path in skipped_files:
            print(f"- {path.name}")


if __name__ == "__main__":
    merge_csv_files()