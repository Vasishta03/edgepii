import hashlib
import json
import pathlib
import urllib.request
import os

ROOT = pathlib.Path(__file__).resolve().parents[2]

SOURCES = {
    'capid': ('e14c93de9c72c2a0f1ecf32c5655b60402754131', 'https://api.github.com/repos/MariaPonomarenko38/CAPID/contents/', ['data/train.jsonl', 'data/test.jsonl', 'data/reddit.jsonl']),
    'ai4privacy': ('7c22e6816b8fc24b7781e9f4e22016c698842dd0', 'https://huggingface.co/datasets/ai4privacy/pii-masking-200k/resolve/{revision}/', ['summary.json', 'pii_class_counts.json', 'english_pii_43k.jsonl'])}


def main():
    prior = ROOT/'data/manifest.json'
    expected = {r['path']: r['sha256'] for r in json.loads(prior.read_text())} if prior.exists() else {}
    records = []

    for name, (revision, base, files) in SOURCES.items():
        for filename in files:
            dest = ROOT/'data/raw'/name/filename
            dest.parent.mkdir(parents=True, exist_ok=True)

            url = base.format(revision=revision)+filename
            if name == 'capid':
                url += '?ref='+revision
            
            key = str(dest.relative_to(ROOT))
            if dest.exists() and key in expected and hashlib.sha256(dest.read_bytes()).hexdigest() != expected[key]:
                raise ValueError('Existing file checksum mismatch: '+key)
            
            if not dest.exists():
                temp = dest.with_suffix(dest.suffix+f'.partial.{os.getpid()}')
                with urllib.request.urlopen(urllib.request.Request(url, headers={'Accept': 'application/vnd.github.raw+json'}), timeout=60) as response, temp.open('wb') as out:
                    while chunk := response.read(1024*1024):
                        out.write(chunk)
                temp.replace(dest)

            records.append(dict(source=name, revision=revision, url=url, path=str(dest.relative_to(
                ROOT)), bytes=dest.stat().st_size, sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
            print(name, filename, dest.stat().st_size, flush=True)

    (ROOT/'data/manifest.json').write_text(json.dumps(records, indent=2)+'\n')


if __name__ == '__main__':
    main()