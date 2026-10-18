import pytest
from elasticsearch import Elasticsearch

from phonetic_search.analyzers import INDEXES


@pytest.fixture(scope="module")
def client():
    client = Elasticsearch(["http://localhost:9200"])
    if not client.ping():
        pytest.skip("Elasticsearch não está no ar; rode 'just up'")
    return client


@pytest.fixture(scope="module")
def indexed(client):
    # sem esta guarda, um cluster recém-subido faria os testes falharem em vez de
    # pularem.
    if not client.indices.exists(index="b1_standard"):
        pytest.skip("índices ausentes; rode 'just all'")
    return client


def test_cluster_e_versao_7_3_0(client):
    assert client.info()["version"]["number"] == "7.3.0"


def test_os_dois_plugins_estao_instalados(client):
    installed = {p["component"] for p in client.cat.plugins(format="json")}
    assert "analysis-phonetic" in installed
    assert "analysis-metaphone-ptbr" in installed


def test_br_metaphone_difere_do_metaphone_ingles(client):
    def analyze(token_filter):
        body = {"tokenizer": "standard", "filter": [token_filter], "text": "assunção"}
        return client.indices.analyze(body=body)["tokens"][0]["token"]

    ptbr = analyze("br_metaphone")
    english = analyze({"type": "phonetic", "encoder": "metaphone"})
    assert ptbr != english, f"esperava codificações distintas, ambas deram {ptbr}"


def test_todos_os_indices_existem_e_tem_documentos(indexed):
    # data/02_dataset.jsonl tem 853 registros.
    for index in INDEXES:
        assert indexed.indices.exists(index=index), index
        assert indexed.count(index=index)["count"] > 800


def test_grafia_moderna_encontra_historica_no_indice_fonetico(indexed):
    # o termo vai isolado, sem 'rua' nem 'santa', para o efeito vir do algoritmo
    # e não de palavras comuns entre os documentos.
    body = {"query": {"match": {"name": "efigenia"}}, "size": 5}

    phonetic = indexed.search(index="p3_dmetaphone", body=body)
    names = [h["_source"]["name"] for h in phonetic["hits"]["hits"]]
    assert any("ephigenia" in n for n in names), f"não recuperou: {names}"

    standard = indexed.search(index="b1_standard", body=body)
    names = [h["_source"]["name"] for h in standard["hits"]["hits"]]
    assert not any("ephigenia" in n for n in names), f"o índice padrão não deveria achar ephigenia: {names}"
