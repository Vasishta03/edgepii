import pytest
from edgepii.core import align_bio,decode_bio,redact,span_counts,prf,privacy_counts,privacy_rates,validate


def test_unicode_offsets_and_mismatched_values():
    r={'text':'Hi Zoë!','spans':[dict(start=3,end=6,value='Zoë',label='NAME')]}
    assert validate(r)==r
    r['spans'][0]['value']='Zoe'
    with pytest.raises(ValueError):validate(r)


def test_overlap_rejected_and_redaction_union():
    spans=[dict(start=0,end=4,label='NAME'),dict(start=2,end=6,label='NAME')]
    with pytest.raises(ValueError):validate(dict(text='abcdefg',spans=spans))
    assert redact('abcdefg',spans)=='[REDACTED]g'


def test_bio_subtokens_and_orphan_i():
    offsets=[(0,0),(0,2),(2,5),(6,9),(0,0)]
    spans=[dict(start=0,end=5,label='NAME')]
    labels=['O','B-NAME','I-NAME']
    ids=align_bio(offsets,spans,{v:i for i,v in enumerate(labels)})
    assert ids==[-100,1,2,0,-100]
    assert decode_bio(offsets,['O','I-NAME','I-NAME','O','O'])==spans


def test_partial_token_boundary_rejected():
    with pytest.raises(ValueError):align_bio([(0,4)],[dict(start=1,end=3,label='NAME')],{'O':0,'B-NAME':1,'I-NAME':2})


def test_type_error_not_span_error():
    g=[dict(start=0,end=4,label='NAME')];p=[dict(start=0,end=4,label='ID')]
    assert prf(span_counts(g,p))['f1']==0
    assert prf(span_counts(g,p,False))['f1']==1


def test_partial_leakage_and_retention():
    g=[dict(start=0,end=4,relevance=0),dict(start=5,end=9,relevance=1)]
    c=privacy_rates(privacy_counts(g,[dict(start=0,end=2),dict(start=5,end=6)]))
    assert c['irrelevant_entity_leakage']==1
    assert c['irrelevant_character_leakage']==.5
    assert c['relevant_character_retention']==.75
    assert privacy_rates(privacy_counts([],[]))['irrelevant_entity_leakage'] is None


def test_adjacent_same_type_entities_stay_distinct():
    assert len(decode_bio([(0,2),(3,5)],['B-NAME','B-NAME']))==2
