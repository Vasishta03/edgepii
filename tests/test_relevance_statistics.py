import pytest
from edgepii.relevance_statistics import paired_relevance_bootstrap


def rows(probabilities):
    return [dict(id='a',start=i,end=i+1,gold=gold,probability=prob) for i,(gold,prob) in enumerate(probabilities)]


def test_identical_relevance_predictions_have_zero_difference():
    predictions=rows([(0,.1),(1,.9)])
    result=paired_relevance_bootstrap(predictions,predictions,repeats=20)
    assert result['difference_macro_f1']==0 and result['ci95']==[0,0]


def test_relevance_comparison_rejects_mismatched_entities():
    with pytest.raises(ValueError):
        paired_relevance_bootstrap(rows([(0,.1)]),rows([(1,.9)]),repeats=20)
