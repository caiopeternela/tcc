import csv
import json
import os

from elasticsearch import Elasticsearch

from phonetic_search.analyzers import INDEXES

SIZE = 10


def build_query(text: str) -> dict:
    return {
        "query": {"match": {"name": {"query": text, "operator": "or"}}},
        "size": SIZE,
    }


def run_searches(client, ground_truth_path: str, output: str) -> int:
    with open(ground_truth_path, encoding="utf-8", newline="") as fh:
        pairs = [(row["modern"], row["historical"]) for row in csv.DictReader(fh)]

    total = 0

    with open(output, "a", encoding="utf-8") as fh:
        for config_id in INDEXES:
            zero_hits = 0
            for i, (query, target) in enumerate(pairs, start=1):
                response = client.search(index=config_id, body=build_query(query))
                hits = response["hits"]["hits"]

                base_record = {
                    "config_id": config_id,
                    "query": query,
                    "target": target,
                }

                if not hits:
                    # falha de recuperação. fica registrada com os campos em None
                    # para ser distinguível de um acerto e de uma consulta que nunca
                    # rodou.
                    zero_hits += 1
                    fh.write(
                        json.dumps(
                            {
                                **base_record,
                                "doc_id": None,
                                "doc_name": None,
                                "rank": None,
                                "score": None,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    total += 1
                else:
                    for rank, hit in enumerate(hits, start=1):
                        fh.write(
                            json.dumps(
                                {
                                    **base_record,
                                    "doc_id": hit["_source"]["id"],
                                    "doc_name": hit["_source"]["name"],
                                    "rank": rank,
                                    "score": hit["_score"],
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                        total += 1

                if i % 200 == 0 or i == len(pairs):
                    print(f"  [{config_id}] {i}/{len(pairs)} consultas")

            print(f"[{config_id}] concluído: {len(pairs)} consultas, {zero_hits} sem resultado")

    return total


if __name__ == "__main__":
    client = Elasticsearch(["http://localhost:9200"])
    output = "data/04_logs.jsonl"

    # grava num temporário e só substitui o arquivo final no fim: uma falha no
    # meio deixaria o arquivo versionado truncado.
    partial = output + ".partial"
    if os.path.exists(partial):
        os.remove(partial)

    n = run_searches(client, "data/03_ground_truth.csv", partial)
    os.replace(partial, output)
    print(f"{n} linhas de log gravadas em {output}")
