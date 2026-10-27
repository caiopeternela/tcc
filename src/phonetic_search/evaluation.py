import csv
import json
from collections import defaultdict

from phonetic_search.metrics import f1_at_k, mrr_at_k, ndcg_at_k, precision_at_k, recall_at_k, success_at_1

METRIC_NAMES = ["p_at_5", "r_at_5", "f1_at_5", "ndcg_at_5", "success_at_1", "mrr_at_10"]

HEADER = ["config_id", "band", "n_queries"] + METRIC_NAMES


def relevance_map(dataset_path: str) -> dict[str, set[str]]:
    """nome histórico → ids dos documentos que têm esse nome.

    uma via partida em vários segmentos vira vários documentos relevantes para a
    mesma consulta, por isso a relevância é por 'name_group' e não por 'id'.
    """
    groups: dict[str, set[str]] = defaultdict(set)
    with open(dataset_path, encoding="utf-8") as fh:
        for row in fh:
            document = json.loads(row)
            groups[document["name_group"]].add(document["id"])
    return dict(groups)


def _bands(ground_truth_path: str) -> dict[str, str]:
    with open(ground_truth_path, encoding="utf-8", newline="") as fh:
        return {row["historical"]: row["band"] for row in csv.DictReader(fh)}


def _group_logs(logs_path: str) -> dict[tuple, list[str]]:
    by_rank: dict[tuple, list[tuple[int, str]]] = defaultdict(list)
    with open(logs_path, encoding="utf-8") as fh:
        for row in fh:
            hit = json.loads(row)
            key = (hit["config_id"], hit["query"], hit["target"])
            by_rank[key].append((hit["rank"], hit["doc_id"]))

    return {key: [doc for _, doc in sorted(hits)] for key, hits in by_rank.items()}


def per_query(
    logs_path: str, dataset_path: str, ground_truth_path: str
) -> dict[tuple[str, str, str], dict[str, float]]:
    """(config_id, band, nome histórico) → as métricas daquela consulta.

    o bootstrap de 'significance' precisa do valor por consulta, que é o mesmo
    que 'evaluate' agrega.
    """
    relevance = relevance_map(dataset_path)
    band_of = _bands(ground_truth_path)

    rows: dict[tuple[str, str, str], dict[str, float]] = {}
    for (config_id, _query, target), retrieved in _group_logs(logs_path).items():
        relevant = relevance.get(target, set())
        rows[(config_id, band_of[target], target)] = {
            "p_at_5": precision_at_k(retrieved, relevant, 5),
            "r_at_5": recall_at_k(retrieved, relevant, 5),
            "f1_at_5": f1_at_k(retrieved, relevant, 5),
            "ndcg_at_5": ndcg_at_k(retrieved, relevant, 5),
            "success_at_1": success_at_1(retrieved, relevant),
            # vai até 10 porque os logs guardam dez posições: com o corte em 5
            # um acerto na sexta ficaria igual a um acerto que não veio.
            "mrr_at_10": mrr_at_k(retrieved, relevant, 10),
        }
    return rows


def evaluate(logs_path: str, dataset_path: str, ground_truth_path: str, output: str) -> int:
    """agrega as métricas por (config_id, band).

    a métrica de um grupo é a média simples das métricas das suas consultas, e não
    a métrica do conjunto de hits do grupo todo.
    """
    accumulated: dict[tuple, list[dict[str, float]]] = defaultdict(list)
    for (config_id, band, _target), metrics in per_query(logs_path, dataset_path, ground_truth_path).items():
        accumulated[(config_id, band)].append(metrics)

    with open(output, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)

        for (config_id, band), queries in sorted(accumulated.items()):
            means = [f"{sum(q[name] for q in queries) / len(queries):.4f}" for name in METRIC_NAMES]
            writer.writerow([config_id, band, len(queries)] + means)

    return len(accumulated)


if __name__ == "__main__":
    n = evaluate(
        "data/04_logs.jsonl",
        "data/02_dataset.jsonl",
        "data/03_ground_truth.csv",
        "data/05_metrics.csv",
    )
    print(f"{n} linhas de métrica em data/05_metrics.csv")
