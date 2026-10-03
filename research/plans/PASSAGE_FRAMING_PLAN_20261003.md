# Passage framing prototype: execution proposal

Prepared 2026-10-03 after discussion among the lead, annotation researcher,
dataset engineer, ML engineer, evaluation engineer, application engineer, and
research recorder. Starting implementation: `96408c458c79d0907a6eadad6cdebbbd3cdd3fd6`.

**Status: planning only. Implementation awaits the user's instruction to start.**
This document changes the proposed future task, not the historical experiments,
current production behavior, or their reported outcomes.

## Agreed scope

Build a research prototype that highlights potentially partisan language in
short English-language U.S. political-news passages for human review. Operationalize
the first version as **evaluative political framing**: wording that praises,
condemns, legitimizes, delegitimizes, or characterizes a political actor or policy
through evaluative language or metaphor beyond a plain description.

Interface heading: **Potential framing cues**. Explanation: **Highlights
evaluative political language for your review.** A cue is not proof of political
bias, factual error, author intent, or the ideology of an article or publisher.
This deliberately narrow target will miss other forms of political bias, such
as selection, omission, and ideological positioning without evaluative wording.

Start with two topics, chosen after a short availability audit. Immigration and
trade/tariffs are practical initial candidates because the source researcher
found natural reporting on both; healthcare and taxation were earlier illustrative
options, not verified corpus commitments. Verify enough usable text and source
diversity before freezing the pilot. Start with one topic if two cannot be sourced
adequately, and narrow the interface and evaluation claims accordingly. Topic
choice must precede model-based selection of examples.

Use coherent excerpts, preferably 60 to 180 words, preserving complete sentences
and speaker context. The interface may accept up to approximately 250 words,
subject to a hard source-token limit and full-prompt context check. Very short
or incomplete passages may require more context. Never silently truncate.

Illustrative examples below are invented to explain the rubric, not evaluation
data or validated model outputs.

| Text | Intended treatment |
|---|---|
| The bill raises the corporate tax rate from 21% to 25%. | Plain description, no framing cue |
| Congress should raise corporate taxes. | Plain advocacy, not automatically a framing cue |
| This reckless tax grab threatens working families. | Candidate evaluative wording, such as `reckless tax grab` |
| A senator called the proposal a reckless tax grab. | Attributed rhetoric, not automatically the reporter's framing |
| A bill's formal title includes Tax Relief. | No automatic flag based only on the title or keyword |
| The flood was devastating. | Emotional wording outside this political-framing target |

Defer LEFT/CENTER/RIGHT labels, overall article ratings, fact checking, omission
detection, long-document processing, URL extraction, and uploads in the v1 UI.
Preserve earlier research code and results without treating their labels as
references for this new task.

## Phases and ownership

| Phase | Work and owner | Concrete exit condition |
|---|---|---|
| 1. Freeze a small contract | Annotation researcher + lead define cues, context, attribution, uncertainty, topic/length bounds | Versioned rubric with positive examples and hard negative controls |
| 2. Build and pilot in parallel | Dataset/annotation roles prepare 30 natural passages; application/ML roles build a phrase-only vertical slice | Runnable prototype; two independent reviews of each pilot passage; agreement, disagreement and actual review time recorded |
| 3. Bounded model comparison | ML + evaluation roles expand development only if useful and compare at most two learned candidates | Complete paired outputs, error analysis, measured runtime, selected configuration or explicit no-winner outcome |
| 4. Independent scoped evaluation | Evaluation + annotation roles prepare new event-separated references and evaluate the frozen candidate once | Counts, span quality, false highlights, attribution, coverage, failures and uncertainty reported |
| 5. Demonstration and staging | Application + lead check real end-to-end behavior and actual hosting resources | A clearly labeled research demo whose claims match its measured limits |

The research recorder maintains decisions, versions, failed attempts, limitations,
and the distinction between software correctness and semantic quality throughout.
The lead integrates work and resolves disagreements. All roles review one
another's contracts before implementation merges.

The first complete milestone is **a runnable prototype and the 30-passage pilot**.
The larger annotation effort is conditional, not a prerequisite to start building.

## Data and human review

Use 10 pilot passages for independent annotation followed by discussion; apply
the revised rules to 20 fresh pilot passages. Two actual people annotate without
model suggestions. They see exactly the same excerpt as the model. Record exact
spans, attribution, no-cue versus uncertain decisions, and a brief reason.

Allow documented two-person consensus after preserving both independent reviews.
Use a third reviewer for unresolved cases when available; otherwise keep them
uncertain. This is a new rubric/schema version. Do not bypass the existing v2
validator or pretend it accepts new semantics. Provide a lightweight browser
workflow rather than requiring people to edit a large manual JSON record.

Planning estimate: two to four minutes per passage per reviewer, or about two
to four combined person-hours for 30 passages, plus one to two person-hours for
discussion/corrections. Measure actual time and agreement before expansion.

Conditional sample plan: **50 development passages total, including the 30 pilot
items, plus 100 fresh final-test passages: 150 unique natural passages overall.**
Re-review affected pilot items if the rubric changes. Every pilot item stays
development material. The final 100 are not required for an early technical demo.
If review capacity only supports a smaller final check, report it as a small
descriptive study with correspondingly limited conclusions.

Collect source URL, author/date where available, article and event group, exact
text hash, excerpt context, and applicable usage terms. Separate development
and test by article and event, including syndicated/near-duplicate stories.
Use multiple sources and distinguish source diversity from political balance.
Do not select examples because a candidate model gets them right or wrong.
Include plain descriptions, ordinary advocacy, attributed rhetoric, negation,
ambiguous speaker context, and nonpolitical controls. Report actual human-labeled
strata rather than forcing desired labels or claiming natural prevalence.

Resource roles:

- **BABE:** useful starting research resource because it has word- and
  sentence-level expert bias annotations. Its native label is not automatically
  our narrower evaluative-political-framing label. Inspect annotation alignment
  and applicable terms before use.
- **BASIL, corrected release:** useful for lexical-span and attribution/context
  examples. Informational-bias labels must not be collapsed into the new lexical
  task. The original paper reports 300 articles and 1,727 spans; corrected release
  counts and labels must be checked separately.
- **New natural passages:** primary task-specific references. Global Voices
  original content is one potential attribution-licensed source, subject to
  per-item exceptions and policy review. It cannot alone establish multi-source
  performance or balanced political coverage.
- **Existing article datasets and 100-item v2 pilot:** historical diagnostics
  only unless specific texts are suitable and newly annotated under this rubric.
  Never project article ideology labels onto words or treat exposed items as
  fresh test examples.
- **Existing 70 synthetic phrase cases:** software/regression inspiration only.
  Reassess expectations under the new task and report separately from natural,
  human-annotated evaluation. Existing reserved holdouts stay closed.

Human references are the dependency for accuracy claims, not for building the
interface, auditing sources, or measuring memory. Agents may draft instructions
and test fixtures; they do not count as independent human reviewers.

## Model and serving plan

First compare the existing pinned **Qwen3-4B-Instruct-2507** runtime, retasked to
the new contract, with **Qwen3-8B** if measured compute resources permit it. A
larger model is a hypothesis to test, not an assumed improvement. Pin exact
weights/runtime, prompt, decoding and preprocessing before scored comparisons.
Use the same task and supplied context, one structured generation per passage,
and complete records of failures. Avoid ensembles, retrieval, broad model sweeps,
and hidden retries. Include no-highlight and abstain-all accounting baselines.

Bound development initially to two prompt/configuration revisions per learned
candidate on up to 50 development items, at most 200 scored development calls,
followed by one selected configuration on the reserved final sample. Any added
experiment needs a recorded failure-based justification and a revised budget.
Choose limits and stopping rules before the final evaluation.

Proposed resource envelope to verify, not a performance guarantee: 512 source
tokens under both candidate tokenizers, 4,096 total runtime context with output
reservation, one concurrent generation, and measured CPU/memory use. Reject
oversize inputs or incomplete output explicitly. If 8B does not fit, report a
single-candidate feasibility study; do not pretend a comparison occurred. Identify
hosting cost and a fixed experiment budget before any paid compute is used.

Create a phrase-only endpoint and startup path that does not load or run the old
RoBERTa article classifier. Reuse text rendering, exact Unicode offsets, source
hashes, overlap validation, request guards and error handling. Replace required
directional fields with task-specific cue/attribution fields in a new response
version. Do not silently reinterpret the legacy API.

Return distinct states: suggestions available; no supported suggestions found;
insufficient context/uncertain; unsupported scope; and operational failure.
Preserve the pasted text exactly. Author cues and attributed quotations must be
visibly distinct; unknown attribution must not appear as an author judgment.
Avoid numeric correctness confidence and `neutral` or `unbiased` conclusions
from an empty result. Explanations should refer to the actual wording and are
themselves experimental suggestions.

Defer training a token-classification model until error analysis, available human
span labels and latency measurements justify it. A later encoder could predict
cue boundaries and attribution directly. Sentence-classifier attention or
saliency is not a substitute for validated phrase extraction. The public
DA-RoBERTa-BABE model is sentence-level and its card lists CC-BY-NC-4.0; it is
not a drop-in commercial phrase model.

## Evaluation and stopping decisions

Measure exact-span precision/recall, meaning-preserving overlap precision/recall,
attribution errors, passage detection, and false author highlights on plain
description/advocacy and quoted-only controls separately. Use one-to-one matches;
freeze overlap rules before final evaluation. Omitting `not` or a meaning-changing
qualifier cannot receive semantic credit just because character overlap is high.
Overlap-only semantic review should be blind to candidate identity.

Report human agreement before consensus, model coverage, uncertainty, invalid
outputs, timeouts, and incomplete processing. Abstention on positive examples
remains missed recall. A fully assessed empty result differs from a failed or
unassessed case. Publish counts and event-aware uncertainty intervals; do not
collapse these measures into an unsupported headline accuracy percentage.

Provisional supervised-demo development aspirations: 85% meaning-preserving
span precision with correct attribution, 60% span recall, at most 10% false author
highlights in each negative control group, and 80% decided coverage. These are
planning targets, not achieved performance or approved release standards. Review
feasibility after the pilot and freeze any chosen criteria before opening the
test. Report exact-boundary metrics alongside the semantic measure. Tiny control
groups yield wide uncertainty even if point estimates meet targets.

If people cannot apply the rubric consistently, simplify it before collecting
more data. If both candidates fail, inspect the paired errors and decide whether
the remedy is clearer context, different labels, better modeling or a narrower
demonstration. Do not retune against the final test and call it untouched. Do not
train simply because a new architecture is available.

For staging, verify real predictions in the browser, source integrity, quotation
behavior, all result states, actual peak memory, latency, and busy/timeout handling.
A roughly 15-second response is a provisional demo goal to measure, not a VPS
promise. Historical 4B memory/latency numbers come from a different pipeline and
cannot establish current Hostinger capacity. Deployment follows measured fit
and retains a rollback version.

## Decisions from team discussion

1. Exclude plain advocacy from the positive label instead of adding a second
   stance-detection task.
2. Remove directional labels from v1 rather than force ambiguous cues into
   LEFT/RIGHT categories.
3. Use a small new passage pilot, not all 100 old article items as a prerequisite.
4. Permit documented consensus; a third human is optional for unresolved cases.
5. Reuse the pilot inside 50 development items, reducing the conditional total
   from 180 to 150 without treating development as a final test.
6. Build the vertical slice in parallel with human review. Independent labels
   constrain quality claims, not all engineering progress.
7. Reuse proven source-integrity components, but version the changed task and API.
8. Start with at most two model candidates and defer fine-tuning until evidence
   identifies a learnable gap.

## Primary sources checked during planning

- BABE paper: https://aclanthology.org/2021.findings-emnlp.101/
- BABE repository: https://github.com/Media-Bias-Group/Neural-Media-Bias-Detection-Using-Distant-Supervision-With-BABE
- BASIL paper: https://aclanthology.org/D19-1664/
- BASIL corrected release: https://github.com/launchnlp/BASIL
- Global Voices republishing policy: https://globalvoices.org/about/global-voices-attribution-policy/
- Global Voices AI editorial policy: https://globalvoices.org/about/global-voices-policy-on-ai/
- Example immigration source, not yet a labeled or approved corpus item: https://globalvoices.org/2026/07/04/what-the-ending-of-the-u-s-temporary-protection-status-could-mean-for-haiti/
- Example trade source, not yet a labeled or approved corpus item: https://globalvoices.org/2025/04/08/trumps-tariffs-on-penguins-and-pine-trees-feel-like-a-late-april-fools-joke/
- Qwen3-4B-Instruct-2507: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
- Qwen3-8B: https://huggingface.co/Qwen/Qwen3-8B
- DA-RoBERTa-BABE model card: https://huggingface.co/mediabiasgroup/da-roberta-babe-ft

No implementation, model inference, dataset downloads, training, deployment or
new human annotation was performed in this planning round. Only this proposal
is a new repository artifact.
