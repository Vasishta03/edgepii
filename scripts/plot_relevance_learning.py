"""Plot relevance validation curves from completed run histories only."""
import json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'.cache/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

COLORS={'minilm':'#0072B2','distilbert':'#D55E00','bert':'#009E73'}
LABELS={'minilm':'MiniLM','distilbert':'DistilBERT','bert':'BERT-base'}


def completed_history(run_id):
    run=ROOT/'artifacts/runs'/run_id
    metadata=run/'metadata.json';history=run/'history.json'
    if not metadata.exists() or not history.exists():return None
    if json.loads(metadata.read_text()).get('status')!='completed':return None
    return json.loads(history.read_text())


fig,ax=plt.subplots(figsize=(7.2,4.4))
plotted=0
for model in ('minilm','distilbert','bert'):
    for suffix,style,label_suffix in (
        ('relevance-pilot-s42','--','original'),
        ('relevance-balanced-pilot-s42','-','balanced repair'),
    ):
        history=completed_history(f'{model}-{suffix}')
        if not history:continue
        ax.plot(
            [row['epoch'] for row in history],
            [row['validation']['macro_f1'] for row in history],
            style,marker='o',color=COLORS[model],
            label=f'{LABELS[model]}: {label_suffix}',
        )
        plotted+=1
if not plotted:raise SystemExit('No completed relevance histories found')
ax.set(
    xlabel='Epoch',ylabel='Validation macro F1',ylim=(0,1),
    title='Exploratory relevance pilots (128 CAPID training documents, seed 42)',
)
ax.grid(alpha=.25);ax.legend(fontsize=8,ncol=2);fig.tight_layout()
out=ROOT/'figures/relevance_learning_curves'
fig.savefig(out.with_suffix('.png'),dpi=180)
fig.savefig(out.with_suffix('.pdf'))
print(out.with_suffix('.png'))
