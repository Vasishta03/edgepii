from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


MODELS = ("minilm", "distilbert", "bert")
STAGES = (
    "01_baselines",
    "02_learning_curves",
    "03_hyperparameters",
    "04_seed_checks",
    "05_relevance_initialization",
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Experiment:
    stage: str
    comparison: str
    config: dict
    source_run_id: str = ""

    @property
    def run_id(self) -> str:
        return self.config["run_id"]


def make_plan(args: argparse.Namespace) -> list[Experiment]:
    if not (
        0 < args.capid_small < args.capid_medium < args.capid_train_size
        and 0 < args.ai4privacy_small < args.ai4privacy_medium < args.ai4privacy_train_size
    ):
        raise ValueError("Each dataset's small, medium and full sizes must increase")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", args.run_prefix):
        raise ValueError("run-prefix must contain only lowercase letters, numbers, _ or -")
    if args.epochs < 1 or args.effective_batch_size < 1:
        raise ValueError("epochs and effective-batch-size must be positive")

    batches = {128: args.short_batch_size, 256: args.batch_size, 384: args.long_batch_size}
    if any(batch < 1 or args.effective_batch_size % batch for batch in batches.values()):
        raise ValueError("Each batch size must be positive and divide effective-batch-size")

    size_sets = {
        "ai4privacy": ((args.ai4privacy_small, str(args.ai4privacy_small)),
                       (args.ai4privacy_medium, str(args.ai4privacy_medium)),
                       (args.ai4privacy_train_size, "full")),
        "capid": ((args.capid_small, str(args.capid_small)),
                  (args.capid_medium, str(args.capid_medium)),
                  (args.capid_train_size, "full")),
    }
    ai4 = size_sets["ai4privacy"]
    capid = size_sets["capid"]
    plan: list[Experiment] = []

    def rid(model: str, family: str, size_tag: str, *, seed: int = 42,
            source_tag: str = "", length: int = 256,
            lr: float = 3e-5) -> str:
        name = f"{args.run_prefix}-{model}-{family}-{size_tag}"
        if source_tag:
            name += f"-from-ai4-{source_tag}"
        if length != 256:
            name += f"-l{length}"
        if lr != 3e-5:
            name += f"-lr{format(lr, '.0e').replace('-', 'm')}"
        return f"{name}-s{seed}"

    def add(stage: str, comparison: str, *, model: str, task: str,
            dataset: str, size: int, size_tag: str, seed: int = 42,
            length: int = 256, lr: float = 3e-5, source_tag: str = "",
            source_run_id: str = "", relevance_init: str = "") -> str:
        if relevance_init:
            family = f"capid-rel-from-{relevance_init}"
        else:
            family = f"{'ai4' if dataset == 'ai4privacy' else 'capid'}-{'det' if task == 'detection' else 'rel'}"
        run_id = rid(model, family, size_tag, seed=seed, source_tag=source_tag,
                     length=length, lr=lr)
        config = dict(
            task=task,
            dataset=dataset,
            seed=seed,
            threads=4,
            device="cuda",
            max_length=length,
            stride=length // 4,
            batch_size=batches[length],
            gradient_accumulation=args.effective_batch_size // batches[length],
            epochs=args.epochs,
            learning_rate=lr,
            weight_decay=0.01,
            validation_size=None,
            run_id=run_id,
            model=model,
            train_size=size,
            phase="research",
            data_dir="data/research",
        )
        if source_run_id:
            config["initialize_from"] = f"artifacts/runs/{source_run_id}/checkpoint"
        plan.append(Experiment(stage, comparison, config, source_run_id))
        return run_id

    def ai4_run(model: str, source: tuple[int, str]) -> str:
        return rid(model, "ai4-det", source[1])

    def capid_det(model: str, target: tuple[int, str], *,
                  source: tuple[int, str] | None = None, stage: str,
                  comparison: str, seed: int = 42, length: int = 256,
                  lr: float = 3e-5) -> str:
        return add(
            stage, comparison, model=model, task="detection", dataset="capid",
            size=target[0], size_tag=target[1], seed=seed, length=length, lr=lr,
            source_tag=source[1] if source else "",
            source_run_id=ai4_run(model, source) if source else "",
        )

    def capid_rel(model: str, target: tuple[int, str], *, stage: str,
                  comparison: str, seed: int = 42, length: int = 256,
                  lr: float = 3e-5, source_run_id: str = "",
                  relevance_init: str = "") -> str:
        return add(
            stage, comparison, model=model, task="relevance", dataset="capid",
            size=target[0], size_tag=target[1], seed=seed, length=length, lr=lr,
            source_run_id=source_run_id, relevance_init=relevance_init,
        )

    # 01: Same settings and full data across models; transfer needs AI4 source.
    for model in MODELS:
        capid_det(model, capid[2], stage=STAGES[0], comparison="detection_model")
        capid_rel(model, capid[2], stage=STAGES[0], comparison="relevance_model")
        add(STAGES[0], "ai4privacy_detection_baseline", model=model,
            task="detection", dataset="ai4privacy", size=ai4[2][0],
            size_tag="full")
        capid_det(model, capid[2], source=ai4[2], stage=STAGES[0],
                  comparison="detection_transfer_vs_capid_only")

    # 02: One-dimensional size curves, not a costly source x target grid.
    for model in MODELS:
        for source in ai4[:2]:
            add(STAGES[1], "ai4privacy_source_size", model=model,
                task="detection", dataset="ai4privacy", size=source[0],
                size_tag=source[1])
            capid_det(model, capid[2], source=source, stage=STAGES[1],
                      comparison="ai4privacy_source_size_after_transfer")
        for target in capid[:2]:
            capid_det(model, target, stage=STAGES[1],
                      comparison="capid_detection_training_size")
            capid_rel(model, target, stage=STAGES[1],
                      comparison="capid_relevance_training_size")
            capid_det(model, target, source=ai4[2], stage=STAGES[1],
                      comparison="capid_size_after_ai4privacy_transfer")

    # 03: Control for optimizer and input-length choice on each full-data path.
    for model in MODELS:
        for family in ("capid_detection", "transferred_detection", "relevance"):
            for lr in (2e-5, 5e-5):
                comparison = f"{family}_learning_rate"
                if family == "relevance":
                    capid_rel(model, capid[2], stage=STAGES[2],
                              comparison=comparison, lr=lr)
                else:
                    capid_det(model, capid[2],
                              source=ai4[2] if family == "transferred_detection" else None,
                              stage=STAGES[2], comparison=comparison, lr=lr)
            for length in (128, 384):
                comparison = f"{family}_context_length"
                if family == "relevance":
                    capid_rel(model, capid[2], stage=STAGES[2],
                              comparison=comparison, length=length)
                else:
                    capid_det(model, capid[2],
                              source=ai4[2] if family == "transferred_detection" else None,
                              stage=STAGES[2], comparison=comparison, length=length)

    # 04: Replicate full-data baselines, retaining the same AI4 source for
    # transfer; these seeds vary CAPID fine-tuning, not source pretraining.
    for model in MODELS:
        for seed in (43, 44):
            capid_det(model, capid[2], stage=STAGES[3],
                      comparison="detection_seed_stability", seed=seed)
            capid_det(model, capid[2], source=ai4[2], stage=STAGES[3],
                      comparison="transfer_seed_stability", seed=seed)
            capid_rel(model, capid[2], stage=STAGES[3],
                      comparison="relevance_seed_stability", seed=seed)

    # 05: Optional to execute, generated for completeness. Requires the
    # trainer to initialize a NEW relevance head on the detection encoder.
    for model in MODELS:
        direct = rid(model, "capid-det", "full")
        transfer = rid(model, "capid-det", "full", source_tag="full")
        capid_rel(model, capid[2], stage=STAGES[4],
                  comparison="relevance_from_detection_encoder",
                  source_run_id=direct, relevance_init="capid-det")
        capid_rel(model, capid[2], stage=STAGES[4],
                  comparison="relevance_from_ai4privacy_encoder",
                  source_run_id=transfer, relevance_init="ai4-det")

    ids = [item.run_id for item in plan]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate run IDs in experiment plan")
    positions = {run_id: index for index, run_id in enumerate(ids)}
    for index, item in enumerate(plan):
        if item.source_run_id not in positions and item.source_run_id:
            raise ValueError(f"Missing prerequisite for {item.run_id}")
        if item.source_run_id and positions[item.source_run_id] >= index:
            raise ValueError(f"Prerequisite comes after {item.run_id}")
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--run-prefix", default="v2")
    parser.add_argument("--epochs", type=int, default=15, help="Maximum epochs; your existing early stopping may stop earlier")
    parser.add_argument("--batch-size", type=int, default=8, help="Per-device batch at length 256")
    parser.add_argument("--short-batch-size", type=int, default=16, help="Per-device batch at length 128")
    parser.add_argument("--long-batch-size", type=int, default=4, help="Per-device batch at length 384")
    parser.add_argument("--effective-batch-size", type=int, default=16, help="Per-device effective batch after gradient accumulation")
    parser.add_argument("--capid-small", type=int, default=256)
    parser.add_argument("--capid-medium", type=int, default=906)
    parser.add_argument("--capid-train-size", type=int, default=1813)
    parser.add_argument("--ai4privacy-small", type=int, default=5000)
    parser.add_argument("--ai4privacy-medium", type=int, default=15000)
    parser.add_argument("--ai4privacy-train-size", type=int, default=34801)
    args = parser.parse_args()

    plan = make_plan(args)
    root = args.project_root.resolve()
    folder = Path("configs") / f"edgepii_experiments_{args.run_prefix}"
    config_dir = root / folder
    config_dir.mkdir(parents=True, exist_ok=True)

    # Preflight every path before writing any config on a changed rerun.
    for item in plan:
        path = config_dir / f"{item.run_id}.json"
        content = json.dumps(item.config, indent=2) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") != content:
            raise FileExistsError(f"Config already exists with different contents: {path}. "
                                  "Choose a new --run-prefix.")
    for item in plan:
        path = config_dir / f"{item.run_id}.json"
        content = json.dumps(item.config, indent=2) + "\n"
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    def write_order(name: str, subset: list[Experiment]) -> Path:
        path = config_dir / f"run_order_{name}.txt"
        path.write_text("".join(f"{folder.as_posix()}/{item.run_id}.json\n"
                                for item in subset), encoding="utf-8")
        return path

    for stage in STAGES:
        items = [item for item in plan if item.stage == stage]
        write_order(stage, items)
        print(f"{stage}: {len(items)} configs")
    first_pass = write_order(
        "first_pass", [item for item in plan if item.stage in STAGES[:2]]
    )
    all_order = write_order("all", plan)

    plan_file = config_dir / "experiment_plan.csv"
    with plan_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "order", "stage", "comparison", "run_id", "task", "model",
            "dataset", "train_size", "seed", "max_length", "batch_size",
            "gradient_accumulation", "epochs", "learning_rate", "source_run_id",
        ))
        writer.writeheader()
        for order, item in enumerate(plan, start=1):
            writer.writerow(dict(order=order, stage=item.stage,
                                 comparison=item.comparison, run_id=item.run_id,
                                 task=item.config["task"], model=item.config["model"],
                                 dataset=item.config["dataset"],
                                 train_size=item.config["train_size"],
                                 seed=item.config["seed"],
                                 max_length=item.config["max_length"],
                                 batch_size=item.config["batch_size"],
                                 gradient_accumulation=item.config["gradient_accumulation"],
                                 epochs=item.config["epochs"],
                                 learning_rate=item.config["learning_rate"],
                                 source_run_id=item.source_run_id))

    print(f"Total: {len(plan)} configs")
    print(f"Model and data comparisons: {first_pass}")
    print(f"Full run order: {all_order}")
    print(f"Comparison plan: {plan_file}")


if __name__ == "__main__":
    main()