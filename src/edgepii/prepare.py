import re
import json
import hashlib
from pathlib import Path
from collections import Counter
from .core import validate, text_key

ROOT = Path(__file__).resolve().parents[2]


def read_jsonl(path):
    with Path(path).open() as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def capid_record(raw, uid, mapping, audit):
    text = raw["context"]
    spans = []
    for value, annotation in raw["piis"].items():
        if not value:
            raise ValueError("empty CAPID annotation")
        hits = list(re.finditer(re.escape(value), text))
        if not hits:
            raise ValueError("CAPID annotation absent from context")
        # A string annotation has no occurrence ID. Retain all exact occurrences
        # and count this assumption. No fuzzy matching or inferred labels.
        if len(hits) > 1:
            audit["repeated_annotation_strings"] += 1
        relevance = int(annotation["relevance"])
        if relevance not in (0, 1):
            raise ValueError("nonbinary relevance")
        for hit in hits:
            spans.append(dict(start=hit.start(), end=hit.end(), value=value, label=mapping[annotation["type"]], native_label=annotation["type"], relevance=relevance))
    return validate(dict(id=uid, source="capid", text=text, question=raw["question"], spans=sorted(spans, key=lambda s: s["start"])))


def ai_record(raw, uid, mapping):
    if raw["language"] != "en":
        raise ValueError("non-English row")
    spans = [dict(s, native_label=s["label"], label=mapping[s["label"]]) for s in raw["privacy_mask"]]
    return validate(dict(id=uid, source="ai4privacy", text=raw["source_text"], question="", spans=sorted(spans, key=lambda s: s["start"])))


def bucket(text, seed=42):
    return (int(hashlib.sha256(f"{seed}:{text_key(text)}".encode()).hexdigest()[:16], 16)/ 2**64)


def prepare():
    # Load the PII ER Classes
    groups = json.loads((ROOT / "labels.json").read_text())
    mapping = {native: target for target, natives in groups.items() for native in natives}

    if sum(map(len, groups.values())) != len(mapping):
        raise ValueError("ambiguous label mapping")
    
    audit = Counter()
    excluded = []
    sets = {}

    for source, split, path in [("ai4privacy", "all", "ai4privacy/english_pii_43k.jsonl"), *[("capid", s, f"capid/data/{s}.jsonl") for s in ("train", "test", "reddit")]]:
        records = []
        seen = {}

        for i, raw in enumerate(read_jsonl(ROOT / "data/raw" / path)):
            uid = f"{source}-{split}-{i}"
            audit[f"{source}_{split}_raw"] += 1

            try:
                r = ai_record(raw, uid, mapping) if source == "ai4privacy" else capid_record(raw, uid, mapping, audit)
                key = text_key(r["text"])
                if key in seen:
                    if r["question"] == seen[key]["question"] and r["spans"] == seen[key]["spans"]:
                        raise ValueError("exact duplicate")
                    
                    if source == "ai4privacy":
                        raise ValueError("conflicting duplicate text")
                    
                seen[key] = r
                records.append(r)

            except (ValueError, KeyError, TypeError) as e:
                excluded.append(dict(id=uid, reason=str(e)))
                audit[f"{source}_{split}_excluded"] += 1
        sets[f"{source}_{split}"] = records

    held = {text_key(r["text"]) for s in ("capid_test", "capid_reddit") for r in sets[s]}

    captrain = []
    for r in sets.pop("capid_train"):
        if text_key(r["text"]) in held:
            excluded.append(dict(id=r["id"], reason="context overlaps official held-out set"))
            audit["capid_train_overlap_removed"] += 1
        else:
            captrain.append(r)

    sets["capid_train"] = [r for r in captrain if bucket(r["text"]) >= 0.1]
    sets["capid_validation"] = [r for r in captrain if bucket(r["text"]) < 0.1]

    for split in ("train", "validation", "test"):
        sets[f"ai4privacy_{split}"] = []

    for r in sets.pop("ai4privacy_all"):
        if text_key(r["text"]) in held:
            excluded.append(dict(id=r["id"], reason="AI4Privacy overlaps CAPID held-out"))
            continue

        u = bucket(r["text"])
        split = "test" if u < 0.1 else "validation" if u < 0.2 else "train"
        sets[f"ai4privacy_{split}"].append(r)

    fingerprints = {}
    for name, records in sets.items():
        records.sort(key=lambda r: hashlib.sha256(("42:" + r["id"]).encode()).hexdigest())
        path = ROOT / "data/processed" / f"{name}.jsonl"
        write_jsonl(path, records)

        audit[name + "_retained"] = len(records)
        fingerprints[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    labels = ["O"] + [p + k for k in sorted(groups) for p in ("B-", "I-")]

    (ROOT / "data/processed/labels.json").write_text(json.dumps(labels, indent=2) + "\n")
    write_jsonl(ROOT / "data/processed/exclusions.jsonl", excluded)

    report = dict(counts=dict(audit), sha256=fingerprints, labels=groups,
        native_label_counts={
            name: dict(Counter(s["native_label"] for r in rows for s in r["spans"]))
            for name, rows in sets.items()
        },
        policy="Exact character spans; repeated CAPID strings expand to all exact occurrences; malformed/overlapping records excluded. Official holdouts remain separate; metrics describe retained subsets.",
    )

    output_file = ROOT / "results/data_audit.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2) + "\n")
    
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    prepare()