import pytest
from pathlib import Path

def test_windowing_keeps_late_entities():
    torch=pytest.importorskip('torch');pytest.importorskip('transformers')
    from transformers import AutoTokenizer
    from edgepii.prepare import ROOT
    from edgepii.modeling import detection_features,relevance_feature
    path=ROOT/'artifacts/backbones/minilm'
    if not (path/'vocab.txt').exists():pytest.skip('download backbone first')
    t=AutoTokenizer.from_pretrained(path,local_files_only=True)
    text='hello '*300+'Alice';span=dict(start=len(text)-5,end=len(text),label='NAME',relevance=1)
    r=dict(text=text,question='Who is named?',spans=[span])
    f=detection_features(r,t,{'O':0,'B-NAME':1,'I-NAME':2},64,16)
    assert len(f)>1 and any(1 in x['labels'] for x in f[1:])
    rel=relevance_feature(r,span,t,128)
    assert len(rel['input_ids'])<=128 and rel['labels']==1
    assert 'alice' in t.decode(rel['input_ids']).lower()


def test_sliding_inference_recovers_tail_entity():
    torch=pytest.importorskip('torch');pytest.importorskip('transformers')
    from types import SimpleNamespace
    from transformers import AutoTokenizer
    from edgepii.prepare import ROOT
    from edgepii.modeling import detect
    path=ROOT/'artifacts/backbones/minilm'
    if not (path/'vocab.txt').exists():pytest.skip('download backbone first')
    tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True)
    alice=tokenizer.convert_tokens_to_ids('alice')
    class FakeDetector:
        config=SimpleNamespace(id2label={0:'O',1:'B-NAME',2:'I-NAME'})
        def __call__(self,input_ids,**kwargs):
            logits=torch.zeros((*input_ids.shape,3));logits[:,:,0]=2
            logits[:,:,1]=(input_ids==alice).float()*5
            return SimpleNamespace(logits=logits)
    text='hello '*300+'Alice'
    spans=detect(dict(text=text),FakeDetector(),tokenizer,64,16,'cpu')
    assert spans==[dict(start=len(text)-5,end=len(text),label='NAME')]
