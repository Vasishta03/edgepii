"""Generate exact seed-43/44 replications of the seed-42 pilot chain."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT/'configs'
MODELS = ('minilm', 'distilbert', 'bert')
SEEDS = (43, 44)


def write_exact(path, payload):
    text = json.dumps(payload, indent=2)+'\n'
    if path.exists() and path.read_text() != text:
        raise RuntimeError(f'refusing to replace different config: {path}')
    path.write_text(text)
    print(path.relative_to(ROOT))


for seed in SEEDS:
    for model in MODELS:
        for stem in (
            f'{model}-pilot-512-s42',
            f'{model}-capid-pilot-s42',
            f'{model}-relevance-balanced-pilot-s42',
        ):
            source = CONFIGS/f'{stem}.json'
            config = json.loads(source.read_text())
            run_id = stem.replace('-s42', f'-s{seed}')
            config['seed'] = seed
            config['run_id'] = run_id
            if '-capid-pilot-' in stem:
                config['initialize_from'] = f'artifacts/runs/{model}-pilot-512-s{seed}/checkpoint'
            write_exact(CONFIGS/f'{run_id}.json', config)
