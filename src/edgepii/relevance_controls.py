"""Gold-span relevance controls: majority, type-only, and question ablations."""

import argparse, json, random, statistics
from collections import Counter, defaultdict
from sklearn.metrics import accuracy_score, f1_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from .experiment import ROOT, seed_all
from .prepare import read_jsonl
from .modeling import relevant_probability


def metrics(gold, pred):
    return dict(
        accuracy=float(accuracy_score(gold, pred)),
        macro_f1=float(
            f1_score(gold, pred, labels=[0, 1], average="macro", zero_division=0)
        ),
    )


def question_sensitivity(normal, permuted, threshold=0.5):
    if not normal or len(normal) != len(permuted):
        raise ValueError("paired nonempty probabilities required")
    differences = [abs(a - b) for a, b in zip(normal, permuted)]
    flips = sum((a >= threshold) != (b >= threshold) for a, b in zip(normal, permuted))
    return dict(
        mean_absolute_probability_change=float(statistics.mean(differences)),
        median_absolute_probability_change=float(statistics.median(differences)),
        decision_flip_rate=flips / len(normal),
        threshold=threshold,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--limit", type=int, default=64)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    seed_all(42, 4)
    train = read_jsonl(ROOT / "data/processed/capid_train.jsonl")
    test = read_jsonl(ROOT / "data/processed/capid_test.jsonl")[: a.limit]
    counts = defaultdict(Counter)
    global_counts = Counter()
    for r in train:
        for s in r["spans"]:
            counts[s["label"]][s["relevance"]] += 1
            global_counts[s["relevance"]] += 1
    # Ties go to irrelevant; control uses all train labels, giving it an advantage
    # over the small neural pilot. It must not use validation/test labels.
    majority = int(global_counts[1] > global_counts[0])
    by_type = {k: int(v[1] > v[0]) for k, v in counts.items()}
    tokenizer = AutoTokenizer.from_pretrained(a.checkpoint, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        a.checkpoint, local_files_only=True
    ).eval()
    conditions = ["normal_question", "no_question", "permuted_question"]
    gold = []
    preds = {k: [] for k in ["majority", "gold_type_only", *conditions]}
    probs = {k: [] for k in conditions}
    # Rotate questions: deterministic, different context; no new gold annotation.
    for i, r in enumerate(test):
        altered = dict(r, question=test[(i + 1) % len(test)]["question"])
        no_question = dict(r, question="")
        for s in r["spans"]:
            gold.append(s["relevance"])
            preds["majority"].append(majority)
            preds["gold_type_only"].append(by_type.get(s["label"], majority))
            values = {
                "normal_question": relevant_probability(
                    r, s, model, tokenizer, 256, "cpu"
                ),
                "no_question": relevant_probability(
                    no_question, s, model, tokenizer, 256, "cpu"
                ),
                "permuted_question": relevant_probability(
                    altered, s, model, tokenizer, 256, "cpu"
                ),
            }
            for condition, value in values.items():
                probs[condition].append(value)
                preds[condition].append(int(value >= 0.5))
    result = dict(
        documents=len(test),
        entities=len(gold),
        type_control_training_documents=len(train),
        metrics={k: metrics(gold, v) for k, v in preds.items()},
        question_sensitivity={
            "removed": question_sensitivity(
                probs["normal_question"], probs["no_question"]
            ),
            "permuted": question_sensitivity(
                probs["normal_question"], probs["permuted_question"]
            ),
        },
        note="Gold spans/types are oracle controls. Removing the question is a valid degraded-input ablation scored against the original labels. Question permutation is only a sensitivity diagnostic: it uses original labels, not newly annotated counterfactual labels. Probability change and decision flips measure model dependence on the question.",
    )
    (ROOT / a.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
