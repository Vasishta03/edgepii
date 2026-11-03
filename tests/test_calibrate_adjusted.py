from edgepii.calibrate_adjusted import choose,pareto,select_operating_points


def point(threshold,leak,retain,policy='context-aware'):
    return dict(threshold=threshold,policy=policy,irrelevant_character_leakage=leak,relevant_character_retention=retain)


def test_adjusted_rule_preserves_primary_infeasibility():
    candidates=[point(.5,.20,.80),point(.9,.14,.40)]
    mask=point(None,.13,.20,'mask-all-detected')
    result=select_operating_points(candidates,mask,.05,.05)
    assert result['primary']['status']=='infeasible'
    assert result['adjusted']['budget']==.18
    assert result['adjusted']['chosen']['threshold']==.9


def test_choose_breaks_ties_by_leakage_then_threshold():
    candidates=[point(.8,.1,.5),point(.9,.08,.5),point(.95,.08,.5)]
    assert choose(candidates,.2)['threshold']==.95


def test_pareto_removes_dominated_points():
    candidates=[point(.5,.3,.8),point(.6,.2,.8),point(.7,.1,.4)]
    assert [x['threshold'] for x in pareto(candidates)]==[.6,.7]
