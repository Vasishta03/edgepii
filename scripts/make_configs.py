import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

base = dict(
    task='detection',
    dataset='ai4privacy', 
    seed=42, 
    threads=4, 
    device='cpu', 
    max_length=128, 
    stride=32,
    batch_size=2, 
    gradient_accumulation=4, 
    epochs=3, 
    learning_rate=5e-5,
    weight_decay=.01,
    validation_size=64
    )


def save(c):
    (ROOT/'configs' / f"{c['run_id']}.json").write_text(json.dumps(c, indent=2)+'\n')


for model in ['minilm', 'distilbert', 'bert']:
    
    save(dict(base, run_id=f'{model}-pilot-512-s42', model=model, train_size=512, phase='pilot'))

    for size in [5000, 10000, 25000, 34801]:
        for seed in [42, 43, 44]:
            save(dict(base, run_id=f'{model}-detection-{size}-s{seed}', model=model, train_size=size, seed=seed, phase='research', data_dir='data/research', max_length=256, stride=64, validation_size=None))
    
    save(dict(base, run_id=f'{model}-capid-pilot-s42', model=model, dataset='capid', train_size=128,
         phase='pilot', initialize_from=f'artifacts/runs/{model}-pilot-512-s42/checkpoint'))
    
    save(dict(base, run_id=f'{model}-relevance-pilot-s42', model=model, dataset='capid',
         task='relevance', train_size=128, phase='pilot', max_length=256, stride=64))


save(dict(base, run_id='minilm-pilot-128-s42',
     model='minilm', train_size=128, phase='pilot'))

for model in ['minilm', 'distilbert', 'bert']:
    for seed in [42, 43, 44]:

     save(dict(base, run_id=f'{model}-capid-full-s{seed}', model=model, dataset='capid', train_size=1813, seed=seed, phase='research',
             data_dir='data/research', max_length=256, stride=64, validation_size=None, initialize_from=f'artifacts/runs/{model}-detection-34801-s{seed}/checkpoint'))
     
     save(dict(base, run_id=f'{model}-relevance-full-s{seed}', model=model, dataset='capid', task='relevance', train_size=1813,
             seed=seed, phase='research', data_dir='data/research', max_length=256, stride=64, validation_size=None))
