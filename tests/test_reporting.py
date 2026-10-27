from phonetic_search.reporting import METRICS, band_table, latex_table, overall_ranking


def _metrics_row(config_id, band, n_queries, ndcg):
    row = {"config_id": config_id, "band": band, "n_queries": str(n_queries)}
    row.update(dict.fromkeys(METRICS, "0.0000"))
    row["ndcg_at_5"] = f"{ndcg:.4f}"
    return row


def test_gera_tabular_com_cabecalho_e_linhas():
    rows = [
        {"config_id": "b1_standard", "p_at_5": "0.1200", "ndcg_at_5": "0.1500"},
        {"config_id": "p3_dmetaphone", "p_at_5": "0.7400", "ndcg_at_5": "0.8100"},
    ]
    tex = latex_table(rows, ["config_id", "p_at_5", "ndcg_at_5"])

    assert "\\begin{tabular}" in tex
    assert "\\end{tabular}" in tex
    assert "0,7400" in tex


def test_escapa_underscore_no_cabecalho_e_nos_valores():
    # coluna sem rótulo em LABELS sai crua, e o underscore precisa ser escapado
    tex = latex_table([{"col_sem_rotulo": "x_y"}], ["col_sem_rotulo"])
    assert "col\\_sem\\_rotulo" in tex
    assert "x\\_y" in tex


def test_cabecalho_e_valores_usam_os_rotulos_em_portugues():
    tex = latex_table([{"band": "mechanical"}], ["band"])
    assert "faixa" in tex and "mecânica" in tex


def test_ranking_geral_pondera_por_n_queries_e_ordena_por_ndcg_desc():
    # alfa: inalterada (n=8, ndcg=1.0) + mecanica (n=2, ndcg=0.0) -> 0.8
    # beta: inalterada (n=8, ndcg=0.9) + mecanica (n=2, ndcg=0.9) -> 0.9,
    #       primeiro no ranking mesmo tendo a pior faixa inalterada
    rows = overall_ranking(
        [
            _metrics_row("alfa", "unchanged", 8, 1.0),
            _metrics_row("alfa", "mechanical", 2, 0.0),
            _metrics_row("beta", "unchanged", 8, 0.9),
            _metrics_row("beta", "mechanical", 2, 0.9),
        ]
    )

    assert [row["config_id"] for row in rows] == ["beta", "alfa"]
    assert float(rows[0]["ndcg_at_5"]) == 0.9
    assert float(rows[1]["ndcg_at_5"]) == 0.8


def test_band_table_filtra_a_faixa_pedida_e_ordena_por_ndcg():
    rows = band_table(
        [
            _metrics_row("alfa", "mechanical", 2, 0.5),
            _metrics_row("beta", "mechanical", 2, 0.9),
            _metrics_row("alfa", "lexical", 5, 0.7),
            _metrics_row("gama", "mechanical", 9, 1.0),
        ],
        "mechanical",
    )

    assert [row["config_id"] for row in rows] == ["gama", "beta", "alfa"]
    # a faixa não sai como coluna: seria o mesmo valor em todas as linhas.
    assert "band" not in rows[0]
