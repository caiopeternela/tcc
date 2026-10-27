import csv
import os

METRICS = ["p_at_5", "r_at_5", "f1_at_5", "ndcg_at_5", "success_at_1", "mrr_at_10"]
RANKING_COLUMNS = ["config_id"] + METRICS
# a coluna 'band' ficaria igual nas nove linhas de uma tabela por faixa.
BAND_COLUMNS = ["config_id", "n_queries"] + METRICS

BANDS = ("unchanged", "lexical", "mechanical")

OVERALL_RANKING_NOTE = (
    r"% Atenção: média ponderada sobre as 3 faixas."
    " Dominada pela faixa inalterada (446 das 835 consultas, 53%, onde a"
    " consulta é igual ao documento e todas as configurações passam de 0,98)."
    " O resultado que discrimina os algoritmos está nas tabelas por faixa"
    " (band_lexical.tex, band_mechanical.tex), não aqui."
)

LABELS = {
    "config_id": "configuração",
    "band": "faixa",
    "n_queries": "consultas",
    "p_at_5": "P@5",
    "r_at_5": "R@5",
    "f1_at_5": "F1@5",
    "ndcg_at_5": "NDCG@5",
    "success_at_1": "Success@1",
    "mrr_at_10": "MRR@10",
    "unchanged": "inalterada",
    "lexical": "lexical",
    "mechanical": "mecânica",
}


def _cell(value: str) -> str:
    # o underscore precisa ser escapado: sem isso o LaTeX trata 'p_at_5' como
    # subscrito e a compilação quebra.
    if value.count(".") == 1 and value.replace(".", "").isdigit():
        return value.replace(".", ",")
    return LABELS.get(value, value).replace("_", r"\_")


def _read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def latex_table(rows: list[dict], columns: list[str]) -> str:
    alignment = "l" + "r" * (len(columns) - 1)
    parts = [
        r"\begin{tabular}{" + alignment + "}",
        r"\hline",
        " & ".join(_cell(c) for c in columns) + r" \\",
        r"\hline",
    ]
    for row in rows:
        parts.append(" & ".join(_cell(row.get(c, "")) for c in columns) + r" \\")
    parts += [r"\hline", r"\end{tabular}"]
    return "\n".join(parts)


def overall_ranking(metrics: list[dict]) -> list[dict]:
    """média das três faixas ponderada por 'n_queries'. ver OVERALL_RANKING_NOTE."""
    by_config: dict[str, list[dict]] = {}
    for row in metrics:
        by_config.setdefault(row["config_id"], []).append(row)

    rows = []
    for config_id, bands in by_config.items():
        n_total = sum(int(row["n_queries"]) for row in bands)
        row = {"config_id": config_id}
        for column in METRICS:
            weighted = sum(float(b[column]) * int(b["n_queries"]) for b in bands)
            row[column] = f"{weighted / n_total:.4f}"
        rows.append(row)

    rows.sort(key=lambda row: float(row["ndcg_at_5"]), reverse=True)
    return rows


def band_table(metrics: list[dict], band: str) -> list[dict]:
    rows = [{c: row[c] for c in BAND_COLUMNS} for row in metrics if row["band"] == band]
    rows.sort(key=lambda row: float(row["ndcg_at_5"]), reverse=True)
    return rows


def generate(metrics_path: str, out_dir: str) -> list[str]:
    os.makedirs(f"{out_dir}/tables", exist_ok=True)
    metrics = _read_csv(metrics_path)

    tables = {
        "overall_ranking.tex": OVERALL_RANKING_NOTE + "\n" + latex_table(overall_ranking(metrics), RANKING_COLUMNS),
    }
    for band in BANDS:
        tables[f"band_{band}.tex"] = latex_table(band_table(metrics, band), BAND_COLUMNS)

    written = []
    for name, tex in tables.items():
        path = f"{out_dir}/tables/{name}"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(tex)
        written.append(path)
    return written


BAND_COLOR = {
    "unchanged": "#2a78d6",
    "lexical": "#eb6834",
    "mechanical": "#1baf7a",
}

BAND_HATCH = {"unchanged": "", "lexical": "//", "mechanical": "xx"}

# primeiro os dois controles, depois os sete algoritmos fonéticos. não é ordenada
# por desempenho, para o eixo x não sugerir um vencedor.
CONFIG_ORDER = [
    "b1_standard",
    "b2_ascii",
    "p1_soundex",
    "p2_metaphone",
    "p3_dmetaphone",
    "p4_cologne",
    "p5_caverphone",
    "p6_beidermorse",
    "p7_metaphone_ptbr",
]


def ndcg_chart(metrics: list[dict], pdf_path: str) -> str:
    import matplotlib

    matplotlib.use("pdf")
    import matplotlib.pyplot as plt

    ndcg = {(row["config_id"], row["band"]): float(row["ndcg_at_5"]) for row in metrics}

    plt.rcParams["font.family"] = "sans-serif"
    fig, ax = plt.subplots(figsize=(11, 5.5))

    bar_width = 0.8 / len(BANDS)
    groups = range(len(CONFIG_ORDER))

    for i, band in enumerate(BANDS):
        heights = [ndcg.get((c, band), 0.0) for c in CONFIG_ORDER]
        offset = (i - (len(BANDS) - 1) / 2) * bar_width
        xs = [g + offset for g in groups]
        ax.bar(
            xs,
            heights,
            width=bar_width * 0.92,
            color=BAND_COLOR[band],
            hatch=BAND_HATCH[band],
            edgecolor="#0b0b0b",
            linewidth=0.6,
            label=LABELS[band],
        )
        # só a faixa mecânica recebe rótulo: é onde a grafia histórica de fato
        # mudou e onde as configurações se separam.
        if band == "mechanical":
            for x, height in zip(xs, heights, strict=True):
                ax.annotate(
                    f"{height:.2f}".replace(".", ","),
                    (x, height),
                    textcoords="offset points",
                    xytext=(0, 3),
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    color="#0b0b0b",
                )

    ax.set_ylim(0, 1.12)
    ax.set_ylabel("NDCG@5")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}".replace(".", ","))
    ax.set_xticks(list(groups))
    ax.set_xticklabels(
        CONFIG_ORDER,
        fontsize=8,
        rotation=30,
        ha="right",
        rotation_mode="anchor",
    )
    ax.yaxis.grid(True, color="#e1e0d9", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    # dentro do gráfico a legenda cai sobre as barras baixas dos controles na
    # faixa mecânica, em qualquer canto que se escolha.
    ax.legend(
        title="faixa",
        frameon=False,
        ncol=3,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
    )

    # sem zerar o CreationDate o PDF muda a cada execução e a CI não consegue conferi-lo.
    fig.savefig(pdf_path, bbox_inches="tight", metadata={"CreationDate": None})
    plt.close(fig)
    return pdf_path


if __name__ == "__main__":
    for path in generate("data/05_metrics.csv", "out"):
        print(f"gerado: {path}")

    os.makedirs("out/charts", exist_ok=True)
    chart = ndcg_chart(_read_csv("data/05_metrics.csv"), "out/charts/ndcg_by_config_and_band.pdf")
    print(f"gerado: {chart}")
