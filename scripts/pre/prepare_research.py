from edgepii.prepare import read_jsonl, write_jsonl
import sys
import json
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT/'src'))

source = ROOT/'data/processed'
dest = ROOT/'data/research'

dest.mkdir(parents=True, exist_ok=True)
audit = json.loads((ROOT/'results/template_audit.json').read_text())
removed = {k: set(v['affected_training_ids']) for k, v in audit.items()}

manifest = {}
counts = {}
for dataset in ['ai4privacy', 'capid']:
    for split in ['train', 'validation', 'test']+(['reddit'] if dataset == 'capid' else []):
        key = f'{dataset}_{split}'
        rows = read_jsonl(source/f'{key}.jsonl')
        if split == 'train':
            rows = [r for r in rows if r['id'] not in removed[dataset]]
        path = dest/f'{key}.jsonl'
        write_jsonl(path, rows)
        counts[key] = len(rows)
        manifest[key] = hashlib.sha256(path.read_bytes()).hexdigest()

(dest/'labels.json').write_bytes((source/'labels.json').read_bytes())

report = dict(version='research-v2',
            source='pilot-v1 retained unchanged at data/processed',
            removed_training_ids={k: sorted(v) for k, v in removed.items()},
            counts=counts, sha256=manifest,
            limitation='Removes exact delexicalized template overlap with held-out splits; semantic near-duplicates remain unaudited.'
            )

(ROOT/'results/research_data_audit.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report['counts'], indent=2))
