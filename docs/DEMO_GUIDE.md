# EdgePII demonstration guide

## Recommended setup

Use **BERT** with **Mask all detected**. BERT has the strongest measured CAPID detector in this project. The examples below were checked with BERT because it produces the cleanest entity boundaries and labels for the presentation set.

The task question does not generate an answer. Under the context-aware policy, it helps the relevance classifier estimate whether each detected entity is needed for the task. Under the recommended mask-all policy, every detected entity is masked and the question only demonstrates the input format.

## Verified examples

### Email address

Context:

```text
Contact email: maria@example.com.
```

Question:

```text
What contact method is available?
```

Expected protected context:

```text
Contact email: [REDACTED].
```

### Name and city

Context:

```text
Customer name: Anita Sharma. City: Bengaluru.
```

Question:

```text
Which personal fields should be removed?
```

Expected protected context:

```text
Customer name: [REDACTED]. City: [REDACTED].
```

### Identity record

Context:

```text
My passport number is A1234567. I was born on 14 March 1998.
```

Question:

```text
Which fields should be removed before sharing?
```

Expected protected context:

```text
My passport number is [REDACTED]. I was born on [REDACTED].
```

### Medical record

Context:

```text
Patient ID: PT-48291. Diagnosis: type 2 diabetes.
```

Question:

```text
What information should be protected in this record?
```

Expected protected context:

```text
Patient ID: [REDACTED]. Diagnosis: [REDACTED].
```

## Honest presentation note

These examples show clean redactions, but they do not prove that the detector is perfect. The measured evaluation includes misses, incorrect types and split spans. The live interface states this limitation. If asked, explain that the demo illustrates the working system while the paper reports aggregate performance on held-out data.
