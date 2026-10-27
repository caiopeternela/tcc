import math

import pytest

from phonetic_search.metrics import (
    f1_at_k,
    mrr_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    success_at_1,
)

# cenário A: 5 recuperados, 1 relevante ("c"), na 3a posição.
A_REC = ["a", "b", "c", "d", "e"]
A_REL = {"c"}

# cenário B: 5 recuperados, 2 relevantes ("a" e "c"), nas posições 1 e 3.
B_REC = ["a", "b", "c", "d", "e"]
B_REL = {"a", "c"}


def test_precision_at_5_cenario_a():
    assert precision_at_k(A_REC, A_REL, 5) == pytest.approx(0.2)


def test_recall_at_5_cenario_a():
    assert recall_at_k(A_REC, A_REL, 5) == pytest.approx(1.0)


def test_f1_at_5_cenario_a():
    # 2 * (0.2 * 1.0) / (0.2 + 1.0) = 0.4 / 1.2
    assert f1_at_k(A_REC, A_REL, 5) == pytest.approx(0.4 / 1.2)


def test_ndcg_at_5_cenario_a():
    # DCG  = 1/log2(3+1) = 1/2 = 0.5
    # IDCG = 1/log2(1+1) = 1/1 = 1.0
    assert ndcg_at_k(A_REC, A_REL, 5) == pytest.approx(0.5)


def test_precision_at_5_cenario_b():
    assert precision_at_k(B_REC, B_REL, 5) == pytest.approx(0.4)


def test_ndcg_at_5_cenario_b():
    # DCG  = 1/log2(2) + 1/log2(4) = 1.0 + 0.5 = 1.5
    # IDCG = 1/log2(2) + 1/log2(3) = 1.0 + 0.63093 = 1.63093
    dcg = 1.0 + 0.5
    idcg = 1.0 + 1 / math.log2(3)
    assert ndcg_at_k(B_REC, B_REL, 5) == pytest.approx(dcg / idcg)


def test_lista_vazia_da_zero_em_tudo():
    assert precision_at_k([], A_REL, 5) == 0.0
    assert recall_at_k([], A_REL, 5) == 0.0
    assert f1_at_k([], A_REL, 5) == 0.0
    assert ndcg_at_k([], A_REL, 5) == 0.0


def test_sem_relevantes_da_zero_sem_dividir_por_zero():
    assert recall_at_k(A_REC, set(), 5) == 0.0
    assert ndcg_at_k(A_REC, set(), 5) == 0.0


def test_k_maior_que_a_lista_nao_estoura():
    assert precision_at_k(A_REC, A_REL, 100) == pytest.approx(1 / 100)
    assert recall_at_k(A_REC, A_REL, 100) == pytest.approx(1.0)


def test_success_at_1_cenario_a():
    # o relevante está na 3a posição, logo não veio em primeiro
    assert success_at_1(A_REC, A_REL) == 0.0


def test_success_at_1_cenario_b():
    assert success_at_1(B_REC, B_REL) == 1.0


def test_mrr_usa_a_posicao_do_primeiro_relevante():
    assert mrr_at_k(A_REC, A_REL, 5) == pytest.approx(1 / 3)
    assert mrr_at_k(B_REC, B_REL, 5) == pytest.approx(1.0)


def test_mrr_enxerga_alem_do_corte_de_cinco():
    # esta é a razão de o pipeline usar k=10: com o corte em 5 um acerto na 7a
    # posição ficaria indistinguível de um acerto que não veio.
    retrieved = ["a", "b", "c", "d", "e", "f", "alvo"]
    assert mrr_at_k(retrieved, {"alvo"}, 5) == 0.0
    assert mrr_at_k(retrieved, {"alvo"}, 10) == pytest.approx(1 / 7)


def test_success_e_mrr_sem_relevantes_dao_zero():
    assert success_at_1(A_REC, set()) == 0.0
    assert mrr_at_k(A_REC, set(), 10) == 0.0
