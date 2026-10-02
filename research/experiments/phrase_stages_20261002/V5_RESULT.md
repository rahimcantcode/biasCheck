# V5 result: limited transfer gain, new development regressions

V5 changes only the direction-stage demonstrations. Extraction and speaker prompts, model, schema, decoding, literal validation and metric functions remain the same as v4. Independent review and66 structural/provenance tests passed before the freeze. The32 new targeted synthetic transfer cases were prepared by an independent AI reviewer, hash-bound before candidate freeze, and not inspected between paired arms. Both arms finished before transfer scoring. They are now exposed development evidence.

| Exact diagnostic | V4 reused38 | V5 reused38 | V4 new32 | V5 new32 |
|---|---:|---:|---:|---:|
| Valid cases | 38/38 | 38/38 | 30/32 | 30/32 |
| Exact span+direction+speaker recovery | 25/27 | 23/27 | 15/19 | 16/19 |
| Exact emitted-span precision | 25/34 | 23/31 | 15/22 | 16/22 |
| Exact author-only recovery | 20/21 | 18/21 | 13/15 | 14/15 |
| Exact author-only precision | 20/27 | 18/25 | 13/19 | 14/19 |
| Zero-expected-span cases with false highlights | 7/15 | 4/15 | 5/16 | 4/16 |
| Exact whole cases | 28/38 | 29/38 | 23/32 | 25/32 |

The new transfer improvement is one additional exact expected span and one fewer negative case with false highlights. It is too small, and residual error too high, to justify promotion. The old development negatives improved, but two correct LEFT decisions became RIGHT for the identical phrase “taxing the rich is good” under neutral padding and injection-plus-policy context.

V5 suppresses the old direct classifier-instruction false highlight and one negation-clipped output. It still mistakes reported policy facts and quoted string mentions for expressed policy positions, mishandles some rejected opinions, and inherits occurrence/alignment and discourse-voice errors. Both transfer arms fail the same two extraction cases on invalid enclosing contexts. One failure is a positive repeated-voice input, so fixed recall and coverage retain it. The zero-expected-span failure is not counted as a correct negative. Transfer candidate objects are identical across all32 pairs.

Direction abstention is still rare: one NO_DIRECTION among23 validated transfer candidates in each arm, applied to different cases. V5 correctly rejects one transfer case under the frozen convention but its reason falsely claims the negation was omitted even though the candidate retains it. A label can match while its explanation is unreliable; explanations need their own assessment.

The single sequential run covered102 article/arm evaluations in about14minutes9seconds. On the new transfer, summed case time was237.8s for v4 and249.0s for v5; mean case latency7.43s and7.78s. Peak sampled runtime RSS was approximately5.07GiB, with one CPU slot/four threads and4096 context. These short synthetic examples do not establish real-article throughput, tail latency, service reliability or deployment sizing.

After inference, all66 tests passed again and frozen code/protocol/model/runtime/fixture identities verified. Raw responses and every failure remain preserved. No model call was retried, no semantic output repaired, and no serving or external repository state changed. Existing89 and726 sealed corpus items were not accessed. Independent full audit is recorded separately.

Next research should change model capability rather than keep tuning demonstrations to these now70 exposed examples. An approximately8B instruction model is worth a bounded resource and quality comparison if it fits actual CPU memory, using a frozen pipeline and new reviewer-owned transfer cases. Release remains unapproved.
