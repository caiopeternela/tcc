import math


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not retrieved:
        return 0.0
    return sum(1 for doc in retrieved[:k] if doc in relevant) / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not retrieved or not relevant:
        return 0.0
    return sum(1 for doc in retrieved[:k] if doc in relevant) / len(relevant)


def f1_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    p = precision_at_k(retrieved, relevant, k)
    r = recall_at_k(retrieved, relevant, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not retrieved or not relevant:
        return 0.0

    dcg = sum(1 / math.log2(position + 1) for position, doc in enumerate(retrieved[:k], start=1) if doc in relevant)
    # no caso ideal não cabem mais relevantes do que k posições, nem mais do que
    # existem no gabarito.
    ideal = min(k, len(relevant))
    idcg = sum(1 / math.log2(position + 1) for position in range(1, ideal + 1))

    return dcg / idcg


def success_at_1(retrieved: list[str], relevant: set[str]) -> float:
    return 1.0 if retrieved and retrieved[0] in relevant else 0.0


def mrr_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    for position, doc in enumerate(retrieved[:k], start=1):
        if doc in relevant:
            return 1 / position
    return 0.0
