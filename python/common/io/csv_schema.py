import re


def flatten_dict(data: dict, prefix: str = "") -> dict:
    out = {}

    for key, value in data.items():
        new_key = f"{prefix}_{key}" if prefix else str(key)

        if isinstance(value, dict):
            out.update(flatten_dict(value, new_key))
        else:
            out[new_key] = value

    return out


def natural_key(value: str):
    return [
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", value)
    ]


def build_fieldnames(
    rows: list[dict],
    preferred_order: list[str] | None = None,
) -> list[str]:
    keys = set()

    for row in rows:
        keys.update(row.keys())

    preferred_order = preferred_order or []

    ordered = [
        key for key in preferred_order
        if key in keys
    ]

    remaining = sorted(
        keys - set(ordered),
        key=natural_key,
    )

    return ordered + remaining