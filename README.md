# Avaliação de Algoritmos Fonéticos na Recuperação de Informação de Logradouros Históricos Brasileiros

O experimento compara 7 algoritmos fonéticos do Elasticsearch 7.3.0 e 2 configurações
de controle, sobre 853 logradouros da área piloto da
[Pauliceia 2.0](https://pauliceia.unifesp.br/). As nove configurações respondem às mesmas
835 consultas, medidas por Precision@5, Recall@5, F1@5, NDCG@5, Success@1 e MRR@10 contra
um gabarito curado.

## O resultado

NDCG@5 por configuração e faixa do gabarito:

| configuração | inalterada (446) | lexical (321) | mecânica (68) |
|---|---|---|---|
| `b1_standard` | 1.0000 | 0.5243 | 0.5807 |
| `b2_ascii` | 1.0000 | 0.8158 | 0.5807 |
| `p1_soundex` | 0.9859 | 0.9511 | 0.9580 |
| `p2_metaphone` | 0.9934 | 0.9206 | 0.7989 |
| `p3_dmetaphone` | 0.9892 | 0.9282 | 0.9570 |
| `p4_cologne` | 0.9812 | 0.9440 | 0.9507 |
| `p5_caverphone` | 0.9854 | 0.9459 | 0.9559 |
| `p6_beidermorse` | 1.0000 | 0.9265 | 0.8883 |
| `p7_metaphone_ptbr` | 0.9967 | 0.9383 | 0.9541 |

Na faixa mecânica, onde a grafia mudou por regra (`ph` para `f`, `th` para `t`, `ll`
para `l`), os controles ficam em 0.5807 e os algoritmos fonéticos chegam a 0.9580.

O gabarito não separa os melhores algoritmos entre si: as diferenças entre os cinco
primeiros da faixa mecânica, e entre os quatro primeiros da lexical, têm intervalo de
confiança de 95% que contém o zero. No agregado o `p7_metaphone_ptbr` lidera as três métricas sensíveis à
posição no ranking, e essa vantagem vem da faixa inalterada, onde ele colide menos.

## Como rodar

Precisa de [uv](https://docs.astral.sh/uv/) e [just](https://just.systems). `just`
sozinho lista os comandos.

```bash
just install
just test
```

Para conferir os resultados publicados não precisa de Docker nem do dump: as buscas
estão versionadas em `data/04_logs.jsonl` e tudo sai delas.

```bash
just results        # métricas, tabelas e gráfico
just significance   # intervalos de confiança das diferenças
```

Depois de rodar os dois, `git diff` tem que sair vazio, o que confirma que os números
publicados se reproduzem.

Para refazer o experimento do zero, com Docker:

```bash
just all    # sobe o Elasticsearch, indexa, busca e avalia
just down
```

## Estrutura

```
src/phonetic_search/   serve qualquer base
  analyzers.py         as 9 configurações do Elasticsearch
  indexing.py          cria os índices e carrega a base
  searching.py         roda o mesmo protocolo de busca em cada configuração
  metrics.py           as 6 métricas
  evaluation.py        junta os logs com o gabarito e calcula as métricas
  significance.py      bootstrap pareado sobre as diferenças por consulta
  reporting.py         tabelas LaTeX e gráfico

src/pauliceia/         só este acervo
  extract.py           lê o dump SQL da Pauliceia
  clean.py             rejeita registro inválido e limpa anotação
  orthography.py       as regras das reformas ortográficas
  draft.py             monta o rascunho do gabarito
```

> **Observação:** o Elasticsearch está fixado no 7.3.0, a versão mais recente para a
> qual existe compilação do plugin `elasticsearch-analysis-metaphone_ptBR`.
