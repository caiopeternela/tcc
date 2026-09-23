import json
import os

import pytest

from pauliceia.extract import DEFAULT_DUMP_PATH, extract

# ordem real das colunas no dump de produção.
COLUMNS = "geom, name, id_street, obs, first_year, last_year, perimeter, id, version, changeset_id"


def _minimal_dump(tmp_path, data_rows):
    header = f"-- PostgreSQL database dump\n\nCOPY public.streets_pilot_area ({COLUMNS}) FROM stdin;\n"
    body = "".join(row + "\n" for row in data_rows)
    footer = "\\.\n\n\nCOPY public.outra_tabela (a, b) FROM stdin;\nlixo\tque\tnao\timporta\n\\.\n"

    path = tmp_path / "dump.sql"
    path.write_text(header + body + footer, encoding="utf-8")
    return str(path)


def _read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(row) for row in fh if row.strip()]


def test_extrai_campos_na_ordem_certa_ignorando_geom(tmp_path):
    # geom (col 1) é um hex WKB gigante: aqui só um placeholder curto.
    row = "DEADBEEF01\trua bella cintra\t42\tobs texto\t1930\t1940\t\\N\t7\t\\N\t\\N"
    output = tmp_path / "output.jsonl"

    n = extract(_minimal_dump(tmp_path, [row]), str(output))

    assert n == 1
    assert _read_jsonl(output) == [{"id": "7", "name": "rua bella cintra", "obs": "obs texto"}]


def test_geom_nunca_aparece_na_saida(tmp_path):
    row = "CAFEBABE1234567890\trua x\t1\t\\N\t\\N\t\\N\t\\N\t1\t\\N\t\\N"
    output = tmp_path / "output.jsonl"

    extract(_minimal_dump(tmp_path, [row]), str(output))

    assert "CAFEBABE" not in output.read_text(encoding="utf-8")


def test_null_vira_string_vazia(tmp_path):
    row = "\\N\trua sem obs\t2\t\\N\t\\N\t\\N\t\\N\t2\t\\N\t\\N"
    output = tmp_path / "output.jsonl"

    extract(_minimal_dump(tmp_path, [row]), str(output))

    assert _read_jsonl(output)[0]["obs"] == ""


def test_desescapa_tab_newline_e_barra_invertida(tmp_path):
    row = "\\N\trua com\\ttab e quebra\\nde row e barra \\\\ invertida\t3\t\\N\t\\N\t\\N\t\\N\t3\t\\N\t\\N"
    output = tmp_path / "output.jsonl"

    extract(_minimal_dump(tmp_path, [row]), str(output))

    assert _read_jsonl(output)[0]["name"] == "rua com\ttab e quebra\nde row e barra \\ invertida"


def test_para_no_terminador_e_ignora_outras_tabelas(tmp_path):
    rows = [
        "\\N\trua a\t1\t\\N\t\\N\t\\N\t\\N\t1\t\\N\t\\N",
        "\\N\trua b\t2\t\\N\t\\N\t\\N\t\\N\t2\t\\N\t\\N",
    ]
    output = tmp_path / "output.jsonl"

    n = extract(_minimal_dump(tmp_path, rows), str(output))

    assert n == 2
    records = _read_jsonl(output)
    assert {r["name"] for r in records} == {"rua a", "rua b"}
    assert "lixo" not in json.dumps(records)


def test_le_o_dump_real_da_pauliceia(tmp_path):
    # valores medidos à mão no dump de produção: 873 linhas de dados, 5 com nome
    # vazio ou NULL, 850 nomes distintos não vazios comparando em minúsculas.
    if not os.path.exists(DEFAULT_DUMP_PATH):
        pytest.skip("dump de produção não disponível neste ambiente")

    output = tmp_path / "raw.jsonl"
    n = extract(DEFAULT_DUMP_PATH, str(output))
    records = _read_jsonl(output)

    assert n == len(records) == 873
    assert len([r for r in records if not r["name"].strip()]) == 5
    assert len({r["name"].strip().lower() for r in records if r["name"].strip()}) == 850
