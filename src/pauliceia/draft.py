import csv
import json

from pauliceia.orthography import modernize

COLUMNS = ["historical", "modern", "band", "applied_rules"]


def generate(dataset: str, output: str) -> dict[str, int]:
    names = set()
    with open(dataset, encoding="utf-8") as fh:
        for row in fh:
            names.add(json.loads(row)["name_group"])

    counts = {"mechanical": 0, "unchanged": 0}

    with open(output, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()

        for name in sorted(names):
            modern, applied = modernize(name)
            band = "mechanical" if applied else "unchanged"
            counts[band] += 1
            writer.writerow(
                {
                    "historical": name,
                    "modern": modern,
                    "band": band,
                    "applied_rules": ";".join(applied),
                }
            )

    return counts


if __name__ == "__main__":
    print(generate("data/02_dataset.jsonl", "data/03_ground_truth_draft.csv"))
