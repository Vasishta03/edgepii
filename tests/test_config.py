import json
import pytest
from edgepii.prepare import ROOT

def test_invalid_run_budget_rejected():
    pytest.importorskip('torch')
    from edgepii.experiment import validate_config
    cfg=json.loads((ROOT/'configs/minilm-pilot-512-s42.json').read_text())
    validate_config(cfg)
    for key in ['epochs','train_size','batch_size','gradient_accumulation','threads']:
        with pytest.raises(ValueError):validate_config(dict(cfg,**{key:0}))
    with pytest.raises(ValueError):validate_config(dict(cfg,stride=cfg['max_length']))
    with pytest.raises(ValueError):validate_config(dict(cfg,class_weighting='mystery'))
    with pytest.raises(ValueError):validate_config(dict(cfg,class_weighting='balanced'))


def test_balanced_relevance_weights_use_training_labels_only():
    torch=pytest.importorskip('torch')
    from edgepii.experiment import relevance_class_weights
    features=[{'labels':0},{'labels':0},{'labels':0},{'labels':1}]
    weights,counts=relevance_class_weights(features,'balanced','cpu')
    assert counts=={0:3,1:1}
    assert torch.allclose(weights,torch.tensor([2/3,2.0]))
    unweighted,_=relevance_class_weights(features,'none','cpu')
    assert unweighted is None
    with pytest.raises(ValueError):relevance_class_weights([{'labels':0}],'balanced','cpu')
