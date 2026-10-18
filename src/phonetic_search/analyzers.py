ANALYZER = "street_name"


def _body(filters: list) -> dict:
    *named, last = filters
    custom = {}

    # um encoder fonético chega como dicionário e precisa de nome próprio para o
    # analyzer poder referenciá-lo.
    if isinstance(last, dict):
        custom["phonetic"] = last
        named.append("phonetic")
    else:
        named.append(last)

    return {
        "settings": {
            # com mais de um shard o Elasticsearch calcula o IDF do BM25 por
            # shard, e os scores passam a variar conforme a distribuição dos
            # documentos entre eles. num experimento comparativo isso torna os
            # resultados irreproduzíveis.
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "filter": custom,
                "analyzer": {ANALYZER: {"tokenizer": "standard", "filter": named}},
            },
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "name": {"type": "text", "analyzer": ANALYZER},
                "name_group": {"type": "keyword"},
            }
        },
    }


def _phonetic(encoder: str, **extra) -> dict:
    return {"type": "phonetic", "encoder": encoder, **extra}


BASE = ["lowercase", "asciifolding"]

INDEXES: dict[str, dict] = {
    "b1_standard": _body(["lowercase"]),
    "b2_ascii": _body(BASE),
    "p1_soundex": _body(BASE + [_phonetic("soundex")]),
    "p2_metaphone": _body(BASE + [_phonetic("metaphone")]),
    "p3_dmetaphone": _body(BASE + [_phonetic("doublemetaphone")]),
    "p4_cologne": _body(BASE + [_phonetic("koelnerphonetik")]),
    "p5_caverphone": _body(BASE + [_phonetic("caverphone2")]),
    "p6_beidermorse": _body(BASE + [_phonetic("beidermorse", languageset=["portuguese"], rule_type="approx")]),
    # único índice sem asciifolding. a intenção era preservar o til, que Jordão e
    # Rosa (2012) descrevem como marcador de nasalização do algoritmo. medindo com
    # a API _analyze, o plugin normaliza os diacríticos sozinho e devolve o mesmo
    # código com e sem til, então a assimetria não altera resultado.
    "p7_metaphone_ptbr": _body(["lowercase", "br_metaphone"]),
}
