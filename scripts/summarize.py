"""Build figures/tables exclusively from measured JSON artifacts."""
import os,pathlib,json,csv
ROOT=pathlib.Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'.cache/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=[]
for path in sorted((ROOT/'results').glob('*-test.json')):
 d=json.loads(path.read_text())
 if 'benchmark' not in d:continue
 cfg=json.loads((ROOT/'artifacts/runs'/d['run_id']/'config.json').read_text())
 rows.append(dict(run_id=d['run_id'],phase=d['phase'],task=cfg['task'],dataset=cfg['dataset'],train_size=cfg['train_size'],test_documents=d['documents'],score=d['metrics']['selection_score'],median_ms=d['benchmark']['median_ms'],p95_ms=d['benchmark']['p95_ms'],peak_rss_mib=d['benchmark']['peak_process_rss_mib']))
if not rows:raise SystemExit('No measured test results available')
with (ROOT/'results/measured_summary.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
main=[r for r in rows if r['dataset']=='ai4privacy' and r['train_size']==512]
if main:
 fig,ax=plt.subplots(figsize=(7,4))
 for r in main:
  ax.scatter(r['p95_ms'],r['score'],s=65);ax.annotate(r['run_id'].split('-')[0],(r['p95_ms'],r['score']),xytext=(5,5),textcoords='offset points')
 ax.set(xlabel='CPU document latency p95 (ms)',ylabel='Strict typed span F1',title='Exploratory pilots: 512 requested documents, seed 42')
 ax.set_ylim(0,1);ax.margins(x=.2);ax.grid(alpha=.25);fig.tight_layout();fig.savefig(ROOT/'figures/pilot_quality_latency.png',dpi=180);fig.savefig(ROOT/'figures/pilot_quality_latency.pdf');plt.close(fig)
lines=['# Measured results','', 'Exploratory pilots only. Different datasets/tasks have different score meanings. No final RQ conclusion.','', '| Run | Test documents | Score | Median ms | p95 ms | RSS MiB |','|---|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f"| {r['run_id']} | {r['test_documents']} | {r['score']:.4f} | {r['median_ms']:.1f} | {r['p95_ms']:.1f} | {r['peak_rss_mib']:.0f} |")
(ROOT/'results/MEASURED.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
