from phonetic_search.analyzers import ANALYZER, INDEXES

PHONETIC = ("p1_soundex", "p2_metaphone", "p3_dmetaphone", "p4_cologne", "p5_caverphone", "p6_beidermorse")


def _filters(config_id):
    return INDEXES[config_id]["settings"]["analysis"]["analyzer"][ANALYZER]["filter"]


def test_tem_os_sete_foneticos_mais_dois_controles():
    assert len(INDEXES) == 9
    assert len([c for c in INDEXES if c.startswith("p")]) == 7


def test_metaphone_ptbr_nao_tem_asciifolding():
    assert "asciifolding" not in _filters("p7_metaphone_ptbr")
    assert "br_metaphone" in _filters("p7_metaphone_ptbr")


def test_demais_foneticos_tem_asciifolding():
    for config_id in PHONETIC:
        assert "asciifolding" in _filters(config_id), config_id


def test_todo_indice_tem_um_shard_so():
    for config_id, body in INDEXES.items():
        assert body["settings"]["number_of_shards"] == 1, config_id
