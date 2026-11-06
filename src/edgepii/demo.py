import json
import torch
import argparse
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForTokenClassification, AutoModelForSequenceClassification

from .experiment import ROOT, seed_all
from .modeling import detect, relevant_probability
from .core import redact


class LocalFilter:
    def __init__(self, detector, relevance=None, threads=4):
        seed_all(42, threads)

        def settings(path):
            cfg = Path(path).parent / "config.json" if path else None
            return json.loads(cfg.read_text()) if cfg and cfg.exists() else {}

        dc, rc = settings(detector), settings(relevance)
        self.detection_length = dc.get("max_length", 128)
        self.detection_stride = dc.get("stride", 32)
        self.relevance_length = rc.get("max_length", 256)

        self.detector = AutoModelForTokenClassification.from_pretrained(str(detector), local_files_only=True).eval()
        self.dt = AutoTokenizer.from_pretrained(str(detector), local_files_only=True)

        self.relevance = AutoModelForSequenceClassification.from_pretrained(str(relevance), local_files_only=True).eval() if relevance else None
        self.rt = AutoTokenizer.from_pretrained(str(relevance), local_files_only=True) if relevance else None

    def filter(self, text, policy="mask-all", threshold=0.9):

        if policy not in ("mask-all", "context-aware"):
            raise ValueError("unknown policy")
        
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be in [0,1]")
        
        if policy == "context-aware" and not self.relevance:
            raise ValueError("context-aware policy requires relevance checkpoint and question")
        
        record = dict(text=text, question=text)
        spans = detect(record, self.detector, self.dt, self.detection_length, self.detection_stride, "cpu")

        mask = []
        for s in spans:
            keep = False
            if policy == "context-aware":
                try:
                    s["relevance_probability"] = relevant_probability(record, s, self.relevance, self.rt, self.relevance_length, "cpu")
                    keep = s["relevance_probability"] >= threshold
                except ValueError:
                    s["relevance_probability"] = None

            s["masked"] = not keep
            if not keep:
                mask.append(s)
        return dict(text=redact(text, mask, labels=True), spans=spans, policy=policy)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--detector", required=True)
    p.add_argument("--relevance")
    p.add_argument("--text", required=True)
    p.add_argument("--policy", choices=["mask-all", "context-aware"], default="mask-all")
    p.add_argument("--threshold", type=float, default=0.9)

    a = p.parse_args()
    f = LocalFilter(a.detector, a.relevance)
    print(json.dumps(f.filter(a.text, a.policy, a.threshold), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()