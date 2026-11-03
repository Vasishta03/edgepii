"""Capture reproducibility context without credentials or environment dumps."""
import json,platform,subprocess,sys,os
from pathlib import Path
import torch,psutil,transformers
ROOT=Path(__file__).resolve().parents[1]
r=dict(python=sys.version,platform=platform.platform(),cpu_model=next((line.split(':',1)[1].strip() for line in open('/proc/cpuinfo') if line.startswith('model name')),'unknown'),logical_cpus=os.cpu_count(),physical_cpus=psutil.cpu_count(logical=False),ram_total_bytes=psutil.virtual_memory().total,torch=torch.__version__,transformers=transformers.__version__,cuda_available=torch.cuda.is_available(),cuda_devices=[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],thread_environment={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS']})
(ROOT/'results/environment.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
