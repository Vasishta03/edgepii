import pytest
from edgepii.statistics import paired_bootstrap

def test_paired_identical_predictions_zero_difference():
    g=[{'id':'a','spans':[dict(start=0,end=2,label='NAME')]}]
    p={'a':g[0]['spans']}
    r=paired_bootstrap(g,p,p,repeats=20)
    assert r['difference_f1']==0 and r['ci95']==[0,0]

def test_id_mismatch_rejected():
    with pytest.raises(ValueError):paired_bootstrap([{'id':'a','spans':[]}],{}, {},repeats=20)
