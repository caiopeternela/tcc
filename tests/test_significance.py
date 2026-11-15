import pytest

from phonetic_search.significance import compare, paired_bootstrap


def test_diferenca_constante_nao_tem_incerteza():
    # se o bootstrap reamostrasse as duas configurações em separado em vez da
    # diferença entre elas, este intervalo teria largura.
    assert paired_bootstrap([0.25] * 40) == pytest.approx((0.25, 0.25, 0.25))


def test_conta_vitorias_empates_e_derrotas():
    values = {
        ("a", "rua um"): {"ndcg_at_5": 1.0},
        ("b", "rua um"): {"ndcg_at_5": 0.5},
        ("a", "rua dois"): {"ndcg_at_5": 0.5},
        ("b", "rua dois"): {"ndcg_at_5": 1.0},
        ("a", "rua tres"): {"ndcg_at_5": 1.0},
        ("b", "rua tres"): {"ndcg_at_5": 1.0},
    }

    row = compare(values, ["rua um", "rua dois", "rua tres"], "ndcg_at_5", "mechanical", "a", "b")

    assert row["n_queries"] == 3
    assert (row["wins_a"], row["ties"], row["wins_b"]) == (1, 1, 1)
    assert row["diff"] == "+0.0000"
