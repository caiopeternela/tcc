import json
import re

STREET_TYPES = (
    "rua",
    "avenida",
    "travessa",
    "largo",
    "praça",
    "praca",
    "alameda",
    "ladeira",
    "becco",
    "beco",
    "viaducto",
    "viaduto",
    "villa",
    "vila",
    "jardim",
)

UNOFFICIAL_ABBREV = re.compile(r"n\.o", re.IGNORECASE)
UNOFFICIAL = re.compile(r"n[aã]o\s+oficial$", re.IGNORECASE)

NA_MARKER = re.compile(r"\s*\(n\.a\)$", re.IGNORECASE)
SIDE_SUFFIX = re.compile(r"\s+(impar|par)$", re.IGNORECASE)
MODERN_NAME_NOTE = re.compile(r"\s*\(atual\s+[^)]+\)$", re.IGNORECASE)


def normalize_group(name: str) -> str:
    return " ".join(name.lower().split())


def _strip_side_suffix(name: str) -> str:
    without_suffix = SIDE_SUFFIX.sub("", name).strip()
    if without_suffix == name.strip():
        return name

    words = without_suffix.split()
    if len(words) == 1 and words[0].lower() in STREET_TYPES:
        return name

    return without_suffix


def clean_name(name: str) -> str:
    name = _strip_side_suffix(name)
    name = MODERN_NAME_NOTE.sub("", name).strip()
    return NA_MARKER.sub("", name).strip()


def rejection_reason(name: str) -> str | None:
    """espera um nome já passado por 'clean_name'."""
    if not name:
        return "nome_vazio"

    if UNOFFICIAL_ABBREV.search(name) or UNOFFICIAL.fullmatch(name):
        return "placeholder"

    return None


def clean(source: str, output: str, rejected: str) -> tuple[int, int]:
    n_accepted = n_rejected = 0

    with (
        open(source, encoding="utf-8") as fh_in,
        open(output, "w", encoding="utf-8") as fh_ok,
        open(rejected, "w", encoding="utf-8") as fh_bad,
    ):
        for row in fh_in:
            record = json.loads(row)
            record["name"] = clean_name(record.get("name", ""))
            reason = rejection_reason(record["name"])

            if reason:
                record["rejection_reason"] = reason
                fh_bad.write(json.dumps(record, ensure_ascii=False) + "\n")
                n_rejected += 1
            else:
                record["name_group"] = normalize_group(record["name"])
                fh_ok.write(json.dumps(record, ensure_ascii=False) + "\n")
                n_accepted += 1

    return n_accepted, n_rejected


if __name__ == "__main__":
    ok, bad = clean(
        "data/01_raw.jsonl",
        "data/02_dataset.jsonl",
        "data/02_rejected.jsonl",
    )
    print(f"aceitos: {ok}   rejeitados: {bad}")
