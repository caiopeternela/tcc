import csv
from collections import defaultdict
from itertools import combinations

import numpy as np

from phonetic_search.evaluation import per_query

HEADER = [
    "metric",
    "band",
    "config_a",
    "config_b",
    "n_queries",
    "diff",
    "ci_low",
    "ci_high",
    "wins_a",
    "ties",
    "wins_b",
]

# P@5, R@5 e F1@5 ficam fora porque o teto de 0,2 imposto por um relevante por
# consulta as deixa indistinguíveis entre configurações.
COMPARED = ["ndcg_at_5", "success_at_1", "mrr_at_10"]

RESAMPLES = 10_000
SEED = 42


def paired_bootstrap(differences: list[float]) -> tuple[float, float, float]:
    """média das diferenças e intervalo de 95% pelo método do percentil.

    reamostra a diferença observada em cada consulta, e não o desempenho de cada
    configuração em separado: as duas responderam às mesmas consultas, e
    descartar esse pareamento alargaria o intervalo sem motivo.
    """
    values = np.asarray(differences, dtype=float)
    draws = np.random.default_rng(SEED).integers(0, values.size, size=(RESAMPLES, values.size))
    means = np.sort(values[draws].mean(axis=1))

    return float(values.mean()), float(means[int(0.025 * RESAMPLES)]), float(means[int(0.975 * RESAMPLES)])


def compare(values: dict, targets: list[str], metric: str, band: str, config_a: str, config_b: str) -> dict:
    differences = [values[(config_a, name)][metric] - values[(config_b, name)][metric] for name in targets]
    diff, low, high = paired_bootstrap(differences)

    return {
        "metric": metric,
        "band": band,
        "config_a": config_a,
        "config_b": config_b,
        "n_queries": len(differences),
        "diff": f"{diff:+.4f}",
        "ci_low": f"{low:+.4f}",
        "ci_high": f"{high:+.4f}",
        "wins_a": sum(1 for d in differences if d > 0),
        "ties": sum(1 for d in differences if d == 0),
        "wins_b": sum(1 for d in differences if d < 0),
    }


def generate(logs_path: str, dataset_path: str, ground_truth_path: str, output: str) -> int:
    values = {}
    targets: dict[str, set[str]] = defaultdict(set)

    for (config_id, band, target), metrics in per_query(logs_path, dataset_path, ground_truth_path).items():
        values[(config_id, target)] = metrics
        targets[band].add(target)
        # a faixa 'overall' reúne as outras três, para o agregado do artigo
        # também ter intervalo de confiança.
        targets["overall"].add(target)

    # a ordem das consultas entra no sorteio do bootstrap, então precisa ser fixa.
    ordered = {band: sorted(names) for band, names in targets.items()}
    configs = sorted({config_id for config_id, _target in values})

    rows = [
        compare(values, ordered[band], metric, band, config_a, config_b)
        for metric in COMPARED
        for band in sorted(ordered)
        for config_a, config_b in combinations(configs, 2)
    ]

    with open(output, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    n = generate(
        "data/04_logs.jsonl",
        "data/02_dataset.jsonl",
        "data/03_ground_truth.csv",
        "data/06_bootstrap.csv",
    )
    print(f"{n} comparações em data/06_bootstrap.csv")
