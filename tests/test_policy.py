import pytest

def test_context_filter_masks_on_relevance_input_failure(monkeypatch):
    pytest.importorskip('torch')
    from edgepii import demo
    f=demo.LocalFilter.__new__(demo.LocalFilter)
    f.detector=object();f.dt=object();f.relevance=object();f.rt=object()
    f.detection_length=128;f.detection_stride=32;f.relevance_length=256
    monkeypatch.setattr(demo,'detect',lambda record,*a:[dict(start=0,end=5,label='NAME')] if record['text']=='Alice' else [])
    def fail(*args):raise ValueError('oversized entity')
    monkeypatch.setattr(demo,'relevant_probability',fail)
    result=f.filter('Alice','Who?','context-aware',.9)
    assert result['text']=='[REDACTED]'
    assert result['spans'][0]['relevance_probability'] is None


def test_context_policy_requires_model_and_question():
    pytest.importorskip('torch')
    from edgepii.demo import LocalFilter
    f=LocalFilter.__new__(LocalFilter);f.relevance=None
    with pytest.raises(ValueError):f.filter('Alice','Who?','context-aware')
