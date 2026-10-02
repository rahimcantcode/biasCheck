# Bias Checker annotation rubric, pilot v2

Prepared 2026-10-02. Completed human reviews: **0**. No gold labels assigned.

This pilot develops rules using 60 historical natural articles and 40 original AI-authored controlled examples. All are development material. Existing dataset labels and model predictions are hidden, not replaced. v2 changes the annotation schema and rubric, not any frozen text, item ID or order. Archived v1 artifacts remain in `legacy_v1/`; v1 annotations require a new human review under v2, never an automatic relabel.

## Primary construct: political AUTHOR FRAMING

Read the complete supplied frozen text. Judge the author's political framing in U.S. context. Do not classify the publisher, the quoted speaker in isolation, factual truth, emotional tone, writing quality, your agreement, or your personal politics.

First choose relevance:

- **POLITICAL:** meaningful content about government, policy, elections, political institutions or ideological debate
- **NONPOLITICAL:** clearly nonpolitical content; ordinary practical public-service information can qualify
- **UNCERTAIN:** the relevance boundary or missing context prevents a defensible decision

For POLITICAL text, independently choose author framing:

- **LEFT / RIGHT:** the author's narration, evaluative choices or sustained framing support the corresponding U.S. ideological direction. An explicit policy proposal is not required, but textual evidence for the direction is. A party name, isolated quotation or criticism of corruption/competence alone is insufficient
- **CENTER:** enough political context exists and the author framing is substantively nonaligned, balanced or consistently centrist. CENTER does not mean true, reasonable, unbiased, calm, or merely “no explicit policy stance”
- **UNCERTAIN:** evidence is insufficient, author-endorsed directions are irreconcilably mixed, attribution is unclear, sarcasm is ambiguous, or this U.S. scheme does not represent the text adequately

NONPOLITICAL relevance requires author framing NOT_APPLICABLE. UNCERTAIN relevance requires author framing UNCERTAIN. The compatibility final label is derived only from relevance and author framing. Optional policy stance can never set it.

## Optional separate axis: issue-policy stance

Assess only an **author-endorsed issue position**, not positions merely reported in quotations. Choose LEFT, CENTER, RIGHT, MIXED, UNCERTAIN, NO_EXPLICIT_STANCE, or NOT_APPLICABLE. Leave NOT_ASSESSED if you are not assessing this axis. Explain the issue and endorsement in the rationale when assessed.

**NO_EXPLICIT_STANCE is not CENTER.** An article can have directional author framing without stating a policy proposal. Conversely, reporting a directional policy proposal need not make the author's framing directional. MIXED policy stance can coexist with a defensible single framing label; explain the difference rather than copying one axis into the other.

## Attribution and uncertainty are required fields

Record who expresses the relevant framing or stance: AUTHOR_NARRATION, QUOTED_SPEAKERS_ONLY, MIXED_AUTHOR_AND_QUOTES, NO_STANCE_EXPRESSED, or UNCLEAR. This is a structured summary; the paraphrased rationale must explain the actual relationship.

Record context sufficiency separately: SUFFICIENT, INSUFFICIENT, or UNCERTAIN. Resolved political LEFT/CENTER/RIGHT requires SUFFICIENT. Adequate context can still reveal genuinely mixed author positions, so SUFFICIENT does not force a resolved direction.

For a primary UNCERTAIN label, select the main reason:

- INSUFFICIENT_CONTEXT
- MIXED_AUTHOR_POSITIONS
- ATTRIBUTION_UNCLEAR
- SARCASM_OR_AMBIGUITY
- OUTSIDE_US_SCHEME
- OTHER, explained in the rationale

Use NONE when the primary label is resolved; describe any residual concerns in the rationale. Do not collapse mixed positions into lack of context. Do not turn abstentions into CENTER to improve agreement.

## Reading context, prior exposure and reviewer provenance

All pilot reviewers should read **the same complete frozen text only**. The record stores the exact supplied text's SHA-256 plus the complete-frozen-text scope and full-read confirmation. Historical source JSON uses only trimmed `content_original`; article text is not copied into exports. A URL, current live page, headline, summary or remembered article is not an equivalent substitute.

Do not open outside material for the judgment: full live articles, event background, party-policy panels, model answers or other reviewers' decisions. If you already did, retain the judgment but disclose what was read, its source/location and extent in the external-context field. Such cases are excluded from the strict blinded/frozen-text-only subset, not silently deleted.

For every item, explicitly answer whether you previously saw model predictions, legacy dataset labels, or another reviewer's answers. Any Yes requires exposure notes. The project owner has previously seen some controlled-case model outputs; this must remain disclosed. The tool preserves exposure through save, reload, import, export and comparison. A post-discussion re-review cannot erase prior exposure or be represented as a new independent person.

Each reviewer attests human manual authorship and independently made judgments. Machine-generated labels or rationales cannot qualify as independent human review. Use an alias consistently; aliases alone do not prove different people. The tool validates provenance fields, not real-world identity or honesty.

### Important corpus context caveat

The earlier **PoliticalBiasCorpus** annotation setup allowed annotators access to the full article, event background and party-policy panels; which optional context each worker actually used is unknown. A snippet-only model comparison may therefore differ from the original human reading context. This caveat is about that corpus, not a claim that its existing labels are wrong. Do not alter its released or worker labels. The pilot's fixed-text-only procedure is a new, explicitly narrower protocol; it cannot be retroactively attributed to the original corpus or to the separate Article-Bias-Prediction source dataset.

## Difficult cases

1. Reporting a left/right quotation does not automatically endorse it. Read author narration, selection and surrounding context
2. Opposing quotations can coexist with strong author framing; opposing author-endorsed positions may justify UNCERTAIN rather than CENTER
3. Partisan names, corruption criticism, loaded tone and factual disagreement are not independent proof of ideological direction
4. Ordinary “left/right,” “liberal amount” or “conservative estimate” are not political signals
5. Procedural political reporting may be CENTER when the complete text supports that judgment; “Taxes” does not supply enough context
6. Do not map unfamiliar international, religious or satirical context mechanically onto U.S. ideology

## Required completed record

- Full frozen text read, exact snapshot hash and external-context disclosure
- Relevance, author framing, derived final label, and optional policy-axis assessment status
- Attribution, context sufficiency and uncertainty reason
- Confidence low/medium/high (not a probability) and a paraphrased rationale of at least 15 characters
- Human reviewer identity, timezone-aware completion time, exposure answers and necessary notes
- Review phase, pass ID and, after initial calibration, agreed rubric freeze ID

Skip unavailable/corrupt text with a reason. Never judge from a URL alone. Exact-span annotation is deferred in v2; no offsets are fabricated. Rationale paraphrases remain required.

## First 10, discussion, freeze and re-review

Two humans use distinct consistent IDs and preferably separate browser profiles. Independently review P001–P010 under `initial_independent_10`, without consulting one another. Export both passes before discussion. Discuss rule ambiguities, document the agreed interpretation/change and assign a shared `rubric_freeze_id` in a separate calibration record. Do not change rubric text without a version change after it is frozen.

If rules change, independently re-review the first 10 under `post_discussion_rereview`, preserve earlier exports and disclose any remembered model/peer answers. Use a new `review_pass_id` but the same reviewer ID. Do not count pre/post-discussion passes as distinct reviewers. Continue remaining items under `frozen_main` and the agreed freeze. The UI records these phases; humans must actually carry out the discussion/freeze process.

Compare same-rubric exports. The report gives all-paired descriptive diagnostics, same-phase/same-freeze results and a stricter blinded/frozen-text-only subset. Author-framing agreement uses pairs both deemed political; policy-axis agreement excludes NOT_ASSESSED/NOT_APPLICABLE. Every axis includes denominator, exclusions, agreements/disagreements and a 95% Wilson interval for raw agreement. Kappa is a descriptive point estimate, undefined in degenerate cases; no kappa interval is claimed. Items clustered by source/event violate simple independence assumptions, so Wilson intervals may be too narrow. Small samples are not certification.

Keep natural articles and synthetic controls separate. The queue preserves original records and flags disagreements, uncertainty, prior exposure, external context and different rounds/freezes. A third human or documented human consensus may adjudicate with reasoning. Comparison does not choose a winner, manufacture machine gold, or approve a label. Agreement is consistency, not objective accuracy.

## Separation from future evaluation

All 100 pilot items remain development material, even after adjudication. Historical articles may overlap checkpoint training and do not represent current media. Synthetic controls test behaviors, not real-world performance. A future accuracy claim requires a separate rights-reviewed, contemporary, source/event/time-separated evaluation set, independent human review/adjudication, locked model and decision policy, and pre-registered class/slice sample sizes and acceptance gates.
