"""EdgePII: local, reproducible PII detection experiments."""
import os
from pathlib import Path
_root=Path(__file__).resolve().parents[2]
for _key,_sub in [('HF_HOME','hf'),('TORCH_HOME','torch'),('MPLCONFIGDIR','matplotlib'),('XDG_CACHE_HOME','xdg')]:
    os.environ.setdefault(_key,str(_root/'.cache'/_sub))
os.environ.setdefault('HF_HUB_OFFLINE','1')
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
