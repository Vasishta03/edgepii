import pytest
from edgepii.relevance_controls import question_sensitivity


def test_question_sensitivity_reports_probability_change_and_flips():
    result=question_sensitivity([.1,.8],[.2,.4])
    assert result['mean_absolute_probability_change']==pytest.approx(.25)
    assert result['median_absolute_probability_change']==pytest.approx(.25)
    assert result['decision_flip_rate']==.5


def test_question_sensitivity_requires_paired_values():
    with pytest.raises(ValueError):question_sensitivity([],[])
    with pytest.raises(ValueError):question_sensitivity([.1],[.1,.2])
