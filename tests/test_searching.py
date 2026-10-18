import csv
import json

from phonetic_search.analyzers import INDEXES
from phonetic_search.searching import build_query, run_searches


class FakeClient:
    def __init__(self, hits_by_query=None):
        self.hits_by_query = hits_by_query or {}

    def search(self, index, body):
        text = body["query"]["match"]["name"]["query"]
        return {"hits": {"hits": self.hits_by_query.get(text, [])}}


def _hit(doc_id, name, score):
    return {"_source": {"id": doc_id, "name": name}, "_score": score}


def _ground_truth(tmp_path, pairs):
    path = tmp_path / "ground_truth.csv"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["modern", "historical"])
        writer.writeheader()
        for modern, historical in pairs:
            writer.writerow({"modern": modern, "historical": historical})
    return str(path)


def _read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(row) for row in fh]


def test_query_padrao_usa_match_com_operador_or():
    query = build_query("rua bela cintra")["query"]["match"]["name"]
    assert query["query"] == "rua bela cintra"
    assert query["operator"] == "or"
    assert "fuzziness" not in query


def test_query_pede_dez_resultados():
    # as métricas são @5, mas o log guarda o top-10 como registro da busca.
    assert build_query("x")["size"] == 10


def test_busca_le_as_colunas_do_gabarito(tmp_path):
    ground_truth = _ground_truth(tmp_path, [("rua bela cintra", "rua bella cyntra")])
    output = tmp_path / "logs.jsonl"
    client = FakeClient({"rua bela cintra": [_hit("d1", "rua bella cyntra", 1.0)]})

    run_searches(client, ground_truth, str(output))

    rows = _read_jsonl(output)
    assert len(rows) == len(INDEXES)
    assert all(row["query"] == "rua bela cintra" for row in rows)
    assert all(row["target"] == "rua bella cyntra" for row in rows)


def test_zero_hits_fica_distinguivel_de_acerto(tmp_path):
    ground_truth = _ground_truth(tmp_path, [("rua inexistente", "rua fantasma")])
    output = tmp_path / "logs.jsonl"

    run_searches(FakeClient(), ground_truth, str(output))

    rows = _read_jsonl(output)
    assert len(rows) == len(INDEXES)
    for row in rows:
        assert row["rank"] is None
        assert row["doc_id"] is None


def test_retorna_o_total_de_linhas_escritas(tmp_path):
    ground_truth = _ground_truth(tmp_path, [("q1", "a1"), ("q2", "a2")])
    output = tmp_path / "logs.jsonl"
    client = FakeClient({"q1": [_hit("d1", "n1", 1.0), _hit("d2", "n2", 0.5)]})

    total = run_searches(client, ground_truth, str(output))

    # por configuração: 2 hits de q1 + 1 linha de zero-hit de q2 = 3
    assert total == len(_read_jsonl(output)) == 3 * len(INDEXES)
