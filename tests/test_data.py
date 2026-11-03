from collections import Counter
import pytest
from edgepii.prepare import capid_record,bucket,read_jsonl,ROOT
from edgepii.core import text_key


def test_repeated_capid_strings_are_explicit():
    audit=Counter()
    r=capid_record(dict(context='Ann met Ann.',question='Who?',piis={'Ann':{'type':'name','relevance':'1'}}),'x',{'name':'NAME'},audit)
    assert len(r['spans'])==2 and audit['repeated_annotation_strings']==1


def test_missing_capid_is_not_fuzzy_matched():
    with pytest.raises(ValueError):capid_record(dict(context='Ann',question='',piis={'Anne':{'type':'name','relevance':'1'}}),'x',{'name':'NAME'},Counter())


def test_group_hash_normalizes_whitespace_and_case():
    assert bucket('Hi  ANN')==bucket('hi ann')


def test_frozen_splits_are_disjoint():
    if not (ROOT/'data/processed/ai4privacy_train.jsonl').exists():pytest.skip('run preprocessing first')
    for dataset in ['ai4privacy','capid']:
        sets=[{text_key(r['text']) for r in read_jsonl(ROOT/'data/processed'/f'{dataset}_{split}.jsonl')} for split in ['train','validation','test']]
        assert not (sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2])


def test_research_v2_removes_template_overlap_without_changing_v1():
    import json
    path=ROOT/'results/research_data_audit.json'
    if not path.exists():pytest.skip('prepare research v2 first')
    audit=json.loads(path.read_text())
    old={r['id'] for r in read_jsonl(ROOT/'data/processed/ai4privacy_train.jsonl')}
    new={r['id'] for r in read_jsonl(ROOT/'data/research/ai4privacy_train.jsonl')}
    removed=set(audit['removed_training_ids']['ai4privacy'])
    assert old-new==removed and len(new)==34801
