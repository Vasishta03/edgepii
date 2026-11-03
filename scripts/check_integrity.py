"""Verify recorded raw data/model bytes and frozen processed split hashes."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
count=0
for filename in ['data/manifest.json','artifacts/model_manifest.json']:
 for r in json.loads((ROOT/filename).read_text()):
  path=ROOT/r['path']
  if hashlib.sha256(path.read_bytes()).hexdigest()!=r['sha256']:raise SystemExit(f'Checksum mismatch: {path}')
  count+=1
for split,digest in json.loads((ROOT/'results/data_audit.json').read_text())['sha256'].items():
 path=ROOT/'data/processed'/f'{split}.jsonl'
 if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise SystemExit(f'Split changed: {split}')
 count+=1
print(f'Verified {count} source/model/split checksums')

research=ROOT/'results/research_data_audit.json'
if research.exists():
 for split,digest in json.loads(research.read_text())['sha256'].items():
  if hashlib.sha256((ROOT/'data/research'/f'{split}.jsonl').read_bytes()).hexdigest()!=digest:raise SystemExit(f'Research split changed: {split}')
 print('Verified research-v2 split checksums')
