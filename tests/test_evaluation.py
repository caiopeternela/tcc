import csv
import json

from phonetic_search.evaluation import evaluate, relevance_map
from phonetic_search.metrics import precision_at_k, recall_at_k


def _write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")


def _write_csv(path, fieldnames, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_agrupa_segmentos_da_mesma_via(tmp_path):
    dataset = tmp_path / "dataset.jsonl"
    _write_jsonl(
        dataset,
        [
            {"id": "1", "name": "avenida tamanduatehy", "name_group": "avenida tamanduatehy"},
            {"id": "2", "name": "avenida tamanduatehy", "name_group": "avenida tamanduatehy"},
            {"id": "3", "name": "rua xingu", "name_group": "rua xingu"},
        ],
    )

    groups = relevance_map(str(dataset))

    assert groups["avenida tamanduatehy"] == {"1", "2"}
    assert groups["rua xingu"] == {"3"}


def _fixture(tmp_path):
    """'rua b' está partida em dois documentos e 'rua a' não, uma faixa para
    cada, uma busca por via.
    """
    dataset = tmp_path / "dataset.jsonl"
    _write_jsonl(
        dataset,
        [
            {"id": "1", "name": "Rua A", "name_group": "rua a"},
            {"id": "2", "name": "Rua B", "name_group": "rua b"},
            {"id": "3", "name": "Rua B velha", "name_group": "rua b"},
        ],
    )

    ground_truth = tmp_path / "ground_truth.csv"
    _write_csv(
        ground_truth,
        ["historical", "modern", "band", "applied_rules"],
        [
            {"historical": "rua a", "modern": "rua a", "band": "unchanged", "applied_rules": ""},
            {"historical": "rua b", "modern": "rua b", "band": "mechanical", "applied_rules": "ph;th"},
        ],
    )

    logs = tmp_path / "logs.jsonl"
    _write_jsonl(
        logs,
        [
            # query "rua a" -> target "rua a": doc 1 (relevante) no topo
            {
                "config_id": "cfg",
                "query": "rua a",
                "target": "rua a",
                "doc_id": "1",
                "doc_name": "Rua A",
                "rank": 1,
                "score": 1.0,
            },
            {
                "config_id": "cfg",
                "query": "rua a",
                "target": "rua a",
                "doc_id": "2",
                "doc_name": "Rua B",
                "rank": 2,
                "score": 0.5,
            },
            # query "rua b" -> target "rua b": relevantes {2,3}, mas só o 2 (rank 2) veio
            {
                "config_id": "cfg",
                "query": "rua b",
                "target": "rua b",
                "doc_id": "1",
                "doc_name": "Rua A",
                "rank": 1,
                "score": 1.0,
            },
            {
                "config_id": "cfg",
                "query": "rua b",
                "target": "rua b",
                "doc_id": "2",
                "doc_name": "Rua B",
                "rank": 2,
                "score": 0.5,
            },
        ],
    )
    return dataset, ground_truth, logs


def test_agrega_por_config_e_band(tmp_path):
    dataset, ground_truth, logs = _fixture(tmp_path)
    output = tmp_path / "metrics.csv"

    n = evaluate(str(logs), str(dataset), str(ground_truth), str(output))

    with open(output, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    assert n == len(rows)
    by_key = {(row["config_id"], row["band"]): row for row in rows}

    unchanged = by_key[("cfg", "unchanged")]
    assert unchanged["n_queries"] == "1"
    assert float(unchanged["p_at_5"]) == precision_at_k(["1", "2"], {"1"}, 5)

    # relevantes = {"2","3"}, os dois segmentos da mesma via
    mechanical = by_key[("cfg", "mechanical")]
    assert mechanical["n_queries"] == "1"
    assert float(mechanical["r_at_5"]) == recall_at_k(["1", "2"], {"2", "3"}, 5)
