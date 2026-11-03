"""Fetch pinned backbone artifacts without writing to global caches."""
import hashlib,json,pathlib,urllib.request,os
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODELS={
 'minilm':('nreimers/MiniLM-L6-H384-uncased','3276f0fac9d818781d7a1327b3ff818fc4e643c0',['README.md','config.json','pytorch_model.bin','special_tokens_map.json','tokenizer_config.json','vocab.txt']),
 'distilbert':('distilbert/distilbert-base-uncased','12040accade4e8a0f71eabdb258fecc2e7e948be',['LICENSE','README.md','config.json','model.safetensors','tokenizer.json','tokenizer_config.json','vocab.txt']),
 'bert':('google-bert/bert-base-uncased','86b5e0934494bd15c9632b12f734a8a67f723594',['LICENSE','README.md','config.json','model.safetensors','tokenizer.json','tokenizer_config.json','vocab.txt'])}
def main():
 prior=ROOT/'artifacts/model_manifest.json'
 expected={r['path']:r['sha256'] for r in json.loads(prior.read_text())} if prior.exists() else {}
 manifest=[]
 for name,(repo,revision,files) in MODELS.items():
  for filename in files:
   dest=ROOT/'artifacts/backbones'/name/filename; dest.parent.mkdir(parents=True,exist_ok=True)
   url=f'https://huggingface.co/{repo}/resolve/{revision}/{filename}'
   key=str(dest.relative_to(ROOT))
   if dest.exists() and key in expected and hashlib.sha256(dest.read_bytes()).hexdigest()!=expected[key]:
    raise ValueError('Existing file checksum mismatch: '+key)
   if not dest.exists():
    tmp=dest.with_suffix(dest.suffix+f'.partial.{os.getpid()}')
    with urllib.request.urlopen(url,timeout=180) as response,tmp.open('wb') as out:
     while chunk:=response.read(1024*1024): out.write(chunk)
    tmp.replace(dest)
   manifest.append(dict(model=name,repository=repo,revision=revision,path=str(dest.relative_to(ROOT)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
   print(name,filename,flush=True)
 (ROOT/'artifacts/model_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__': main()
