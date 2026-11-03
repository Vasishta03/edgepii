"""Shared tokenization and inference for every backbone."""
import numpy as np
import torch
from .core import align_bio, decode_bio


def detection_features(record, tokenizer, label2id, max_length, stride):
    enc=tokenizer(record['text'],return_offsets_mapping=True,truncation=True,max_length=max_length,stride=stride,return_overflowing_tokens=True)
    features=[]
    for i,offsets in enumerate(enc['offset_mapping']):
        item={k:v[i] for k,v in enc.items() if k in tokenizer.model_input_names}
        item['labels']=align_bio(offsets,record['spans'],label2id)
        features.append(item)
    return features


def relevance_feature(record, span, tokenizer, max_length):
    prefix=f"Question: {record['question']} Entity: {record['text'][span['start']:span['end']]}"
    first=tokenizer(prefix,add_special_tokens=False)['input_ids']
    if len(first)>max_length//2:
        raise ValueError('question/entity exceeds relevance prefix budget')
    enc=tokenizer(record['text'],add_special_tokens=False,return_offsets_mapping=True)
    hits=[i for i,(a,b) in enumerate(enc['offset_mapping']) if a<span['end'] and b>span['start']]
    if not hits: raise ValueError('entity has no context tokens')
    room=max_length-len(first)-tokenizer.num_special_tokens_to_add(pair=True)
    if hits[-1]-hits[0]+1>room: raise ValueError('entity exceeds context window')
    start=max(0,min(hits[0]-(room-(hits[-1]-hits[0]+1))//2,len(enc['input_ids'])-room))
    second=enc['input_ids'][start:start+room]
    item=tokenizer.prepare_for_model(first,second,add_special_tokens=True,return_attention_mask=True)
    item={k:v for k,v in item.items() if k in tokenizer.model_input_names}
    if 'relevance' in span:item['labels']=span['relevance']
    return item


@torch.inference_mode()
def detect(record, model, tokenizer, max_length, stride, device):
    enc=tokenizer(record['text'],return_offsets_mapping=True,truncation=True,max_length=max_length,stride=stride,return_overflowing_tokens=True)
    scores={};counts={}
    for i, offsets in enumerate(enc['offset_mapping']):
        batch={k:torch.tensor([v[i]],device=device) for k,v in enc.items() if k in tokenizer.model_input_names}
        logits=model(**batch).logits[0].cpu().numpy()
        for offset,score in zip(offsets,logits):
            key=tuple(offset)
            if key[0]==key[1]:continue
            scores[key]=scores.get(key,0)+score; counts[key]=counts.get(key,0)+1
    offsets=sorted(scores)
    labels=[model.config.id2label[int(np.argmax(scores[o]/counts[o]))] for o in offsets]
    return decode_bio(offsets,labels)


@torch.inference_mode()
def relevant_probability(record, span, model, tokenizer, max_length, device):
    feature=relevance_feature(record,span,tokenizer,max_length)
    batch={k:torch.tensor([v],device=device) for k,v in feature.items() if k!='labels'}
    return float(model(**batch).logits.softmax(-1)[0,1].cpu())
