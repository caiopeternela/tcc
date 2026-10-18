import json
from typing import cast

from elasticsearch import Elasticsearch, helpers

from phonetic_search.analyzers import INDEXES

REQUIRED_PLUGINS = {"analysis-phonetic", "analysis-metaphone-ptbr"}


def check_plugins(client: Elasticsearch) -> None:
    # o type stub declara cat.plugins() devolvendo str, mas com format="json" ele
    # devolve uma lista de dicionários em tempo de execução.
    plugins = cast(list[dict], client.cat.plugins(format="json"))
    installed = {p["component"] for p in plugins}
    missing = REQUIRED_PLUGINS - installed
    if missing:
        raise RuntimeError(f"plugins ausentes no cluster: {sorted(missing)}. Rode 'just up'.")


def load_dataset(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(row) for row in fh]


def create_and_load(client: Elasticsearch, dataset_path: str) -> dict[str, int]:
    check_plugins(client)
    documents = load_dataset(dataset_path)
    counts = {}

    for index, body in INDEXES.items():
        client.indices.delete(index=index, ignore=[404])
        client.indices.create(index=index, body=body)

        actions = [
            {
                "_index": index,
                "_id": d["id"],
                "_source": {
                    "id": d["id"],
                    "name": d["name"],
                    "name_group": d["name_group"],
                },
            }
            for d in documents
        ]
        helpers.bulk(client, actions)
        client.indices.refresh(index=index)
        counts[index] = client.count(index=index)["count"]

    return counts


if __name__ == "__main__":
    client = Elasticsearch(["http://localhost:9200"])
    for index, n in create_and_load(client, "data/02_dataset.jsonl").items():
        print(f"{index:<22} {n} documentos")
