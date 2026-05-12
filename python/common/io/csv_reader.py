import csv


class CsvReader:
    def __init__(self, input_path: str):
        self.input_path = input_path

    def read_rows(self) -> list[dict]:
        with open(self.input_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [self._normalize_row(row) for row in reader]

    def iter_rows(self):
        with open(self.input_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield self._normalize_row(row)

    def _normalize_row(self, row: dict) -> dict:
        return {
            key: self._parse_value(value)
            for key, value in row.items()
        }

    def _parse_value(self, value: str):
        if value == "":
            return None

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            return value