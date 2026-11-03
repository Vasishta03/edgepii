"""Dependency-free span validation, metrics, and deterministic redaction."""
import hashlib
import re
from collections import Counter


def text_key(text):
    return hashlib.sha256(' '.join(text.casefold().split()).encode()).hexdigest()


def validate(record):
    text = record['text']
    previous_end = 0
    for span in sorted(record['spans'], key=lambda s: (s['start'], s['end'])):
        a, b = span['start'], span['end']
        if not (isinstance(a, int) and isinstance(b, int) and 0 <= a < b <= len(text)):
            raise ValueError('invalid character offsets')
        if a < previous_end:
            raise ValueError('overlapping entities cannot be represented by flat BIO')
        if span.get('value', text[a:b]) != text[a:b]:
            raise ValueError('span value disagrees with source text')
        previous_end = b
    return record


def align_bio(offsets, spans, label2id):
    """Label every non-special subtoken; reject partial annotation boundaries.

    A boundary inside a token cannot be exactly recovered. Reject it rather than
    silently expanding gold annotations; preprocessing audit reports such cases.
    """
    labels = []
    previous = None
    for a, b in offsets:
        if a == b:
            labels.append(-100)
            previous = None
            continue
        hits = [i for i, s in enumerate(spans) if a < s['end'] and b > s['start']]
        if not hits:
            labels.append(label2id['O']); previous = None
        elif len(hits) != 1:
            raise ValueError('token overlaps multiple entities')
        else:
            i = hits[0]; s = spans[i]
            if a < s['start'] or b > s['end']:
                raise ValueError('entity boundary lies inside token')
            prefix = 'I-' if previous == i else 'B-'
            labels.append(label2id[prefix + s['label']]); previous = i
    return labels


def decode_bio(offsets, labels):
    spans = []
    current = None
    for (a, b), label in zip(offsets, labels):
        if a == b:
            continue
        if label == 'O':
            current = None
            continue
        prefix, kind = label.split('-', 1)
        if prefix == 'B' or current is None or current['label'] != kind:
            current = dict(start=a, end=b, label=kind)
            spans.append(current)
        else:
            current['end'] = b
    return spans


def span_counts(gold, pred, typed=True):
    def key(s):
        return (s['start'], s['end'], s['label']) if typed else (s['start'], s['end'])
    g, p = set(map(key, gold)), set(map(key, pred))
    return Counter(tp=len(g & p), fp=len(p-g), fn=len(g-p))


def prf(counts):
    tp, fp, fn = (counts[k] for k in ('tp','fp','fn'))
    return dict(precision=tp/(tp+fp) if tp+fp else 0., recall=tp/(tp+fn) if tp+fn else 0., f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0., **counts)


def merge_intervals(spans):
    merged = []
    for s in sorted(spans, key=lambda s: (s['start'], s['end'])):
        a, b = s['start'], s['end']
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(b, merged[-1][1])
        else:
            merged.append([a, b])
    return merged


def redact(text, spans):
    for a, b in reversed(merge_intervals(spans)):
        if not 0 <= a < b <= len(text):
            raise ValueError('invalid redaction offsets')
        text = text[:a] + '[REDACTED]' + text[b:]
    return text


def privacy_counts(gold, masked):
    """Coverage proxy, NOT a formal privacy guarantee or downstream utility score.

    Any unmasked character makes an irrelevant gold entity partially leaked.
    Relevant PII is assessed separately as character retention.
    """
    covered = set()
    for a, b in merge_intervals(masked):
        covered.update(range(a,b))
    result = Counter()
    for s in gold:
        chars = set(range(s['start'],s['end']))
        if s.get('relevance') == 0:
            result.update(irrelevant_entities=1, leaked_entities=int(bool(chars-covered)), irrelevant_chars=len(chars), leaked_chars=len(chars-covered))
        elif s.get('relevance') == 1:
            result.update(relevant_chars=len(chars), retained_relevant_chars=len(chars-covered))
    return result


def privacy_rates(c):
    def rate(a,b): return c[a]/c[b] if c[b] else None
    return dict(irrelevant_entity_leakage=rate('leaked_entities','irrelevant_entities'), irrelevant_character_leakage=rate('leaked_chars','irrelevant_chars'), relevant_character_retention=rate('retained_relevant_chars','relevant_chars'), **c)
