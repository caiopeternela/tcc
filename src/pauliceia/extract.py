import json
import re

# 'geom' não serve à busca, 'id_street' repete o 'id' e 'first_year'/'last_year' valem
# 1930 e 1940 em quase todos os registros.
KEPT_FIELDS = ("id", "name", "obs")

DEFAULT_DUMP_PATH = "../backup_dev/backup_dev.sql"
DEFAULT_OUTPUT = "data/01_raw.jsonl"
TABLE = "public.streets_pilot_area"

# escapes do formato texto do COPY:
# https://www.postgresql.org/docs/current/sql-copy.html#SQL-COPY-TEXT-FORMAT
# as sequências octal (\123) e hexadecimal (\x1f) ficam de fora porque o pg_dump
# nunca as emite. qualquer outro escape vira o próprio caractere.
ESCAPES = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\"}
ESCAPED = re.compile(r"\\(.)")


def _unescape(value: str) -> str:
    return ESCAPED.sub(lambda m: ESCAPES.get(m[1], m[1]), value)


def _read_copy_block(dump_path: str) -> tuple[list[str], list[str]]:
    prefix = f"COPY {TABLE} ("
    columns: list[str] | None = None
    rows: list[str] = []
    in_block = False

    with open(dump_path, encoding="utf-8") as fh:
        for line in fh:
            if not in_block:
                if line.startswith(prefix):
                    declaration = line[line.index("(") + 1 : line.index(")")]
                    columns = [c.strip() for c in declaration.split(",")]
                    in_block = True
                continue

            row = line.rstrip("\n")
            if row == "\\.":
                break
            rows.append(row)

    if columns is None:
        raise ValueError(f"bloco COPY de {TABLE} não encontrado em {dump_path}")

    return columns, rows


def extract(dump_path: str = DEFAULT_DUMP_PATH, output: str = DEFAULT_OUTPUT) -> int:
    columns, rows = _read_copy_block(dump_path)
    position = {name: i for i, name in enumerate(columns)}

    n = 0
    with open(output, "w", encoding="utf-8") as fh:
        for row in rows:
            fields = row.split("\t")
            record = {}
            for key in KEPT_FIELDS:
                raw = fields[position[key]]
                record[key] = "" if raw == "\\N" else _unescape(raw)
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            n += 1

    return n


if __name__ == "__main__":
    n = extract()
    print(f"{n} registros extraídos para {DEFAULT_OUTPUT}")
