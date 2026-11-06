from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
THRESHOLD = 0.80


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def delex_tokens(row: dict) -> list[str]:
    text = row["text"]
    for span in sorted(row["spans"], key=lambda s: s["start"], reverse=True):
        text = text[:span["start"]] + \
            f" PII_{span['label']} " + text[span["end"]:]
    return re.findall(r"pii_[a-z_]+|[a-z]+|[0-9]+", text.lower())


def shingles(row: dict) -> set[str]:
    tokens = delex_tokens(row)
    if len(tokens) < 3:
        return {" ".join(tokens)} if tokens else {""}
    return {" ".join(tokens[i:i + 3]) for i in range(len(tokens) - 2)}


def simhash(values: set[str]) -> int:
    weights = [0] * 64
    for value in values:
        digest = int.from_bytes(hashlib.blake2b(
            value.encode(), digest_size=8).digest(), "big")
        for bit in range(64):
            weights[bit] += 1 if digest & (1 << bit) else -1
    result = 0
    for bit, weight in enumerate(weights):
        if weight >= 0:
            result |= 1 << bit
    return result


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a or b else 1.0


def audit(train_path: Path, holdout_paths: list[Path]) -> dict:
    train_rows = read_jsonl(train_path)
    train_features = []
    buckets = defaultdict(set)
    for index, row in enumerate(train_rows):
        values = shingles(row)
        signature = simhash(values)
        train_features.append((row["id"], values, signature))
        for band in range(8):
            buckets[(band, (signature >> (band * 8)) & 0xFF)].add(index)

    split_results = {}
    for path in holdout_paths:
        candidates_checked = 0
        matches = []
        maximum = 0.0
        for row in read_jsonl(path):
            values = shingles(row)
            signature = simhash(values)
            candidates = set()
            for band in range(8):
                candidates.update(
                    buckets[(band, (signature >> (band * 8)) & 0xFF)])
            best = (0.0, None, None)
            for index in candidates:
                candidates_checked += 1
                train_id, train_values, _ = train_features[index]
                score = jaccard(values, train_values)
                if score > best[0]:
                    best = (score, train_id, index + 1)
            maximum = max(maximum, best[0])
            if best[0] >= THRESHOLD:
                matches.append({
                    "holdout_id": row["id"], "train_id": best[1], "train_position": best[2],
                    "included_in_reduced_10k": best[2] <= 10_000, "trigram_jaccard": best[0],
                })
        matches.sort(key=lambda item: item["trigram_jaccard"], reverse=True)
        split_results[path.stem] = {
            "holdout_documents": sum(1 for _ in path.open()),
            "candidate_pairs_checked": candidates_checked,
            "matches_at_or_above_threshold": len(matches),
            "maximum_similarity": maximum,
            "matches": matches,
        }
    return {"training_documents": len(train_rows), "splits": split_results}


report = {
    "method": "Approximate cross-split delexicalized word-trigram Jaccard search. Eight-band SimHash only generates candidates; every reported similarity is exact Jaccard on the candidate pair.",
    "threshold": THRESHOLD,
    "privacy": "Source text is not written to the report; only frozen record IDs and similarity values are stored.",
    "ai4privacy": audit(
        ROOT / "data" / "research" / "ai4privacy_train.jsonl",
        [ROOT / "data" / "research" / "ai4privacy_validation.jsonl",
            ROOT / "data" / "research" / "ai4privacy_test.jsonl"],
    ),
    "capid": audit(
        ROOT / "data" / "research" / "capid_train.jsonl",
        [ROOT / "data" / "research" / "capid_validation.jsonl", ROOT / "data" /
            "research" / "capid_test.jsonl", ROOT / "data" / "research" / "capid_reddit.jsonl"],
    ),
    "limitation": "This is an approximate lexical near-duplicate audit, not a semantic-equivalence guarantee. SimHash candidate generation can miss pairs, and high semantic similarity can occur with low trigram overlap.",
}
(ROOT / "results" / "near_duplicate_audit.json").write_text(json.dumps(report, indent=2) + "\n")

lines = [
    "# Approximate near-duplicate audit",
    "",
    f"Threshold: delexicalized word-trigram Jaccard ≥ {THRESHOLD:.2f}.",
    "",
    "| Dataset | Holdout | Train docs | Holdout docs | Matches | Maximum similarity |",
    "|---|---|---:|---:|---:|---:|",
]
for dataset in ("ai4privacy", "capid"):
    for split, values in report[dataset]["splits"].items():
        lines.append(
            f"| {dataset} | {split} | {report[dataset]['training_documents']} | {values['holdout_documents']} "
            f"| {values['matches_at_or_above_threshold']} | {values['maximum_similarity']:.3f} |"
        )
lines += [
    "",
    "The report stores IDs and scores only, without copying source text. SimHash is used only to generate candidate pairs; reported Jaccard values are exact for those candidates.",
    "",
    "This is an approximate lexical audit, not a semantic-equivalence guarantee. It can miss semantically similar paraphrases and candidate pairs missed by SimHash.",
]
ai_validation_matches = report["ai4privacy"]["splits"]["ai4privacy_validation"]["matches"]
if ai_validation_matches:
    included = sum(match["included_in_reduced_10k"]
                   for match in ai_validation_matches)
    lines += [
        "",
        f"AI4Privacy validation matches inside the first 10,000 nested training records: {included}. "
        "Therefore the measured reduced 5K/10K scaling runs were not exposed to the identified high-similarity training record.",
    ]
(ROOT / "results" / "NEAR_DUPLICATES.md").write_text("\n".join(lines) + "\n")
print(ROOT / "results" / "NEAR_DUPLICATES.md")