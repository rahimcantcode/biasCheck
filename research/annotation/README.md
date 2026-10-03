# Human annotation pilot v2

October 3 follow-through: a source-verified, development-only adjudication
validator is now available in `validate_adjudication.py`. It binds the original
manifest and two v2 review exports, requires explicit third-human decisions,
and leaves unresolved items unresolved. It does not authorize training, create
independent final-test gold, or approve a model. See the practical
[pilot and adjudication instructions](../team_20261003/ANNOTATION_PILOT.md).

Prepared 2026-10-02. Completed human reviews: **0**. No human gold labels, model retraining or improved-accuracy claim.

The 100 examples are unchanged: 60 natural historical articles from 12 source identifiers and 41 topics, plus 40 AI-authored controlled examples. Text, IDs and order are copied exactly from frozen v1. News article text is not redistributed. Selection excludes the earlier 60-article model comparison, but independence from historical checkpoint training is unknown.

## What changed

v2 separates primary political AUTHOR FRAMING from optional author-endorsed issue-policy stance. No explicit policy stance does not mean CENTER. Required fields now cover attribution, sufficient versus missing/mixed context, uncertainty reason, exact frozen reading context, external context, prior model/legacy-label/peer-answer exposure, human manual authorship, review phase and rubric freeze.

`pilot_manifest.json` and `legacy_v1/` preserve v1; `pilot_manifest_v2.json` is the new version. The v2 reviewer uses a different local-storage namespace. Existing v1 exports are never silently reinterpreted as v2; preserve them and conduct a new human review. No completed annotations have been added.

## Start reviewing

1. Read **RUBRIC.md** and open **Bias_Checker_Review_Pilot.html**
2. Enter a consistent unique reviewer alias and attest human manual independent judgment
3. The 40 controlled examples are verified locally. Click **Load article snapshots** for the 60 historical texts, or select the pinned source dataset's `data/jsons` folder
4. Both reviewers independently review P001–P010, export, discuss ambiguities, agree/freeze the rubric, and re-review independently if rules change. Keep earlier exports and disclose prior peer/model answers
5. Continue the remaining items under the shared freeze. Save each item; export every pass frequently
6. On a later visit/page reload, load the pinned article snapshots first, then open the same reviewer workspace or import your export. Historical article text is not stored in browser storage; span-reviewed historical items cannot be restored until their exact snapshots are verified. A failed restore leaves the saved review unchanged

Remote loading retrieves only pinned GitHub source JSONs and verifies `content_original.trim()` against the frozen hash. The viewer does not display legacy labels. For offline snapshots:

```bash
git clone https://github.com/ramybaly/Article-Bias-Prediction research-data
git -C research-data checkout ced8111a720948e6a410e52031ace99c4e53f096
```

Read only the supplied frozen text. Live article URLs, event background and party-policy panels are outside this pilot's reading context; any use must be disclosed. If browser hashing/storage is blocked, serve this folder locally:

```bash
python -m http.server 8765 --bind 127.0.0.1
```

Open `http://localhost:8765/Bias_Checker_Review_Pilot.html`. Each reviewer should use a separate browser profile. Exports contain aliases, structured judgments, provenance, paraphrased rationales, timestamps and any human-selected short exact span excerpts, not full article text. Browser storage is not a backup. Import validates the entire v2 export before modifying a workspace and preserves exposure/context fields. Replacing a saved review or import requires confirmation; retain the previous export first.

## Compare two human exports

```bash
python research/annotation/compare_reviews.py \
  --first review-A-v2.json --second review-B-v2.json \
  --output agreement.json --snapshots research-data/data/jsons
```

Validation rejects wrong pilot/rubric, duplicate item IDs, empty/inconsistent reviewer identities, machine/nonhuman provenance, missing exposure/context, unread text, mismatched hashes and inconsistent axis labels. Repeated passes or case variants of the same alias cannot count as different reviewers. This validates self-attestations, not real-world human identity.

The report contains per-axis raw agreement, agree/disagree counts, denominators, excluded counts, 95% Wilson intervals, descriptive Cohen's kappa, natural/synthetic slices, same-round and strict blinded/frozen-text-only subsets. Optional policy NOT_ASSESSED/NOT_APPLICABLE pairs are excluded from that axis. Author framing uses pairs both judged political. Intervals assume independent items and can understate uncertainty for clustered sources/events; agreement is not accuracy.

The disagreement queue retains both original judgments plus uncertainty/exposure/context/round flags. It leaves adjudication empty and `gold_labels_approved` false. Preserve original exports, document human adjudication, and keep every pilot item out of any future independent final test. No machine prediction serves as gold. Span agreement is reported separately for all paired reviews, natural/synthetic slices, same-round reviews and the blinded/frozen-text-only subset, with each subset’s own eligible/excluded denominators.

## Reproduce and test

```bash
python research/annotation/build_v2_manifest.py
python research/annotation/render_reviewer.py
python -m pytest tests/test_annotation.py tests/test_annotation_audit.py tests/test_annotation_dom.py tests/test_annotation_spans.py -q
```

The v2 builder derives a new manifest from frozen v1 without altering items. The standalone HTML embeds the manifest and reviewer script. Original v1 files under `legacy_v1/` are preserved snapshots, not the active workflow. Do not regenerate sample selection after reviews start. Bump the pilot/rubric version for future content, ordering, schema or instruction changes.

The Node DOM/event-fixture regression verifies save/reload/export/import, provenance rejection/preservation, and interrupted navigation using the actual reviewer script and HTML control IDs. It needs Node and otherwise explicitly skips. It does not launch a browser or establish visual layout/browser compatibility; real-browser QA remains unverified. The Python suite always validates schema and comparison behavior.

## Corpus context caveat and remaining work

The earlier PoliticalBiasCorpus annotation interface allowed full-article, event-background and party-policy-panel access; actual optional-context use per worker is unknown. Its released labels are preserved. This v2 fixed-text protocol does not retroactively change that corpus's construct or equate snippet-only model context with the original human context. It is also distinct from the Article-Bias-Prediction dataset providing this pilot's historical snapshots.

Independent humans still need to complete the pilot. Contemporary, rights-reviewed data collection, independent adjudication, a separate frozen evaluation and pre-registered release criteria are still required. The versioned span extension collects exact phrases, repeated-occurrence selections, Unicode codepoint offsets, local LEFT/RIGHT and AUTHOR/QUOTED/UNKNOWN attribution. NO_DIRECTIONAL_SPANS is distinct from NOT_ASSESSED. It never seeds from a model or article label. Imports require loaded verified text for span-reviewed items; offline comparison without historical snapshots explicitly marks their spans unverified, excludes them from exact-span agreement and blocks gold qualification. See RUBRIC.md for context/negation rules.

## Human review is not a production import

There is currently **no automatic human-export → gold dataset or production conversion**. These files are raw, provenance-bearing pilot judgments. Before any training/evaluation use, humans must adjudicate disagreements and uncertainty with the complete frozen source, preserve both independent originals, and explicitly sign off. A future conversion step must preserve item/source identity, exact text hashes, codepoint offsets, attribution, exposure/context provenance and review/rubric versions, with validation against the frozen snapshots. Conversion must not silently rewrite labels or boundaries.

Even adjudicated pilot records remain development data. They cannot substitute for a separate, rights-reviewed, frozen independent evaluation or authorize a production model/policy release. No conversion, adjudication, gold approval or release is claimed by this reviewer.
