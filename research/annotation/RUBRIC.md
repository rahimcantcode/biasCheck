# Bias Checker annotation rubric, pilot v1

This 100-item pilot develops labeling rules. It is not a release benchmark. It contains 60 historical articles from 12 source identifiers and 41 topics, plus 40 original AI-authored controlled examples. Existing dataset labels and model scores are withheld from reviewers. None of these examples currently has a human-approved label.

## Task

Read the complete supplied text. Classify its expressed political framing in the context of U.S. politics. Do not label an author, publisher, person, party, or yourself. Do not use agreement with a claim, writing quality, factual accuracy, emotional tone, or a publisher's reputation as a substitute for evidence in the text.

First decide relevance: POLITICAL, NONPOLITICAL, or UNCERTAIN. Political relevance includes government policy, elections, political institutions, and public ideological debate. Ordinary references to public services can be nonpolitical when the text only supplies practical instructions. If that boundary is unclear, record uncertainty and explain why.

If POLITICAL, choose LEFT, CENTER, RIGHT, or UNCERTAIN:

- LEFT: sustained authorial framing supports positions conventionally associated with the U.S. political left, such as stronger redistribution or collective labor protections. A policy mention alone is insufficient.
- RIGHT: sustained authorial framing supports positions conventionally associated with the U.S. political right, such as a smaller federal economic role or traditionalist policy positions. A policy mention alone is insufficient.
- CENTER: enough political context exists to judge the framing, and the text is substantively nonaligned, balanced, or consistently centrist. Center does not mean true, reasonable, unbiased, or emotionally calm.
- UNCERTAIN: insufficient context, irreconcilable mixed positions, ambiguous sarcasm, unclear authorial endorsement, or framing that this U.S. left/right scheme does not represent adequately. Do not force a classification.

NONPOLITICAL is the final label for clearly nonpolitical material. If relevance is UNCERTAIN, the final label is UNCERTAIN. For the initial five-label export, political uncertainty and relevance uncertainty both map to UNCERTAIN; keep the relevance field to distinguish them.

## Difficult cases

1. Quotations: distinguish the quoted speaker from the article's framing. Reporting a left or right statement does not automatically endorse it. Evaluate attribution, criticism, selection and surrounding context. Do not infer omitted context you have not seen.
2. Mixed positions: balance between opposing quotations can coexist with a strong authorial stance. Conversely, opposing author-endorsed positions may warrant UNCERTAIN rather than CENTER. Explain the dominant framing if you choose a directional label.
3. Political names: praise or criticism of a named party is not by itself enough to establish ideology. Corruption, transparency and competence criticism can occur across ideological positions.
4. Ordinary words: left/right directions, liberal quantities and conservative estimates are not ideological signals by themselves.
5. Factual procedural news: CENTER may be appropriate when relevant political context is sufficient. A fragment such as “Taxes” normally lacks sufficient context to judge leaning.
6. Loaded language: record it in notes if useful, but hostile tone alone does not determine political direction.
7. International, religious, satirical or unfamiliar context: do not map it mechanically onto U.S. ideology. Use uncertainty when the mapping cannot be defended.

## Every completed judgment must contain

- Confirmation that the entire frozen text was read.
- Relevance and final label.
- Human confidence: low, medium or high. This is not a model probability.
- A brief paraphrase of the textual evidence and an explanation of attribution or ambiguity where relevant.
- Reviewer identifier and completion time. Use aliases rather than sensitive personal information.

Evidence notes should paraphrase news articles rather than copy long passages. Skip unavailable or corrupted material with a reason; never label from the headline or URL alone.

## Independent review and adjudication

Rahim and a second reviewer should use separate review IDs and preferably separate browser profiles. Work independently, without model scores, legacy labels or the other person's decisions. Each reviewer exports their own JSON. Complete the first 10 items, compare interpretations, and refine the rubric before proceeding. Record any rubric changes; if changed, re-review the first 10 independently under the final pilot rubric. Do not count pre-discussion and post-discussion answers as independent agreement.

Use compare_reviews.py to measure agreement on identical fully reviewed items and produce a disagreement queue. Report relevance agreement, five-label agreement and Cohen's kappa, with denominators. A third reviewer or documented consensus adjudicates disagreements using the full text and evidence. Preserve both original judgments. Agreement measures consistency, not objective correctness.

## Separation from future evaluation

All 100 pilot items are development material because the rubric and workflow are adjusted using them. Do not place them in the later frozen final test, even after consensus. Do not claim model accuracy from this pilot. Synthetic and natural-news results must stay separate. The historical public articles may overlap old checkpoint training, and the publisher sources are not an independent sample of today's media.

After the pilot, collect a separate contemporary evaluation set with documented usage rights, source/event/time separation, independent review and adjudication. Register class/slice sample sizes and acceptance gates before evaluating candidates. Keep development, calibration and final-test IDs and content hashes separate.
