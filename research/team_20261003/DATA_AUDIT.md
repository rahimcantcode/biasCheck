# Dataset audit and acquisition decision

Date: 2026-10-03. Repository baseline: `4268bab42c1186ddcd1fee5b9b80ab4a2ae9f8a4`.
Prepared by the dataset-engineering agent; this is an evidence audit, not a new
human annotation, legal clearance, or accuracy result.

## Decision

The data problem is real, but "all our labels are publisher labels" is not an
established diagnosis. We lack the original checkpoint's row-level training
record, and our newer corpora measure different constructs. The next useful
investment is fixed-context human annotation with provenance, not another model
selection round on the same 66 examples. Existing label disagreement is evidence
to investigate, not permission to replace references with an agent's opinion.

Use three separate data lanes:

1. Preserve historical corpora for reproducibility and explicitly named auxiliary
   tasks. Do not turn their article, source, or binary-bias labels into directional
   phrase annotations.
2. Complete the existing independent-human rubric pilot. Add a separately
   versioned natural-text development pool with recorded rights and no seeded
   labels. The two verified Wikinews candidates below can start acquisition.
3. Commission or obtain explicit permission for contemporary multi-source news
   and opinion content for training and final evaluation. Freeze whole event
   families and publication windows before labeling/model selection. A final test
   must be a separate collection, not the pilot after it has been adjudicated.

## Targeted search for the missing training repository

A follow-up connector search of the owner `rahimcantcode` on 2026-10-03 found
24 accessible repository metadata records. Filtering their names for bias,
classifier, political, NLP, training, machine-learning terms found only
`biasCheck`. Repository searches for bias, classifier, training, archived bias,
and `bias-classifier` found no second matching project. Account-scoped code
search found no `NewsMediaBias` or `train_test_split` matches; `roberta` matches
were the existing biasCheck serving, configuration and UI files.

This did not recover the separately mentioned "bias classifier" repository,
training notebook, exact original dataset URLs, split IDs, or authentic original
run outputs. Search covers connector-accessible metadata and indexed default
branches; it does not prove no deleted, renamed, private/unconnected, nonindexed,
or different-owner repository exists. No unrelated repository contents or raw
training/evaluation data were opened. The original-model provenance remains
unresolved, so the row count and old accuracy remain historical claims.

## Existing data inventory

| Resource | Actual supervision and scope | Size or split from committed records | Decision |
|---|---|---|---|
| Original RoBERTa training mixture | Historical claim: AllSides plus NewsMediaBias. Exact source identity, snapshots, labeling process, split IDs and original evaluation checkpoint were not recovered. | Approximately 53k is a historical claim, not an audited count. | Recover notebook and row manifest before reproducing the old 89% claim. No assumption that this mixture equals the separately acquired Baly corpus. |
| Baly Article-Bias-Prediction | Authors describe manual article-level AllSides ideology labels. The political source field is separate. CENTER is not a nonpolitical label. | Upstream repository advertises 37,554 articles; paper describes 34,737. Project's corrected split: 23,603 train, 2,356 validation, 1,300 test. | Historical development only. Exact duplicates and registrable-domain overlap handled; ownership, syndication, event/time overlap and checkpoint training exposure remain unresolved. |
| PoliticalBiasCorpus / BiasLab | Perceived political framing. Project preserves two worker labels and source resolution rules. Input reconstruction is title plus three excerpts; original workers could consult more context. | 270 released human-derived labels: 139 strict agreements, 131 Center/partisan resolutions. Project: 115 train, 66 reused development, 89 reserved. | Research-only project use under CC BY-NC-SA 4.0. The 89 inputs remain unopened by this audit. Event strings are disjoint, but a shared episode crosses train/development. |
| UK argument stance challenge | Three-human majority for whether Proposition plus Locution expresses a political stance. Zero means no stance, not nonpolitical. | 1,000 source pairs: 274 development, 726 reserved. | Auxiliary attribution/stance research only. No mapping to U.S. LEFT/CENTER/RIGHT. Reserved inputs remain unopened by this audit. |
| Existing reviewer pilot v2 | Intended independent human framing, relevance and exact-span collection. Frozen supplied text; exposure disclosure required. | 60 historical natural articles plus 40 AI-authored controls; completed human reviews: 0 in baseline records. | Start with P001-P010 independently, discuss/freeze rubric, then finish. All pilot items remain development. Do not resample or silently revise v2. |
| Phrase diagnostic sets | AI-authored expected spans and directions. Their precision measures agreement with developer expectations. | 38 original/development cases plus 32 inspected transfer cases, 70 now development. | Preserve as regression tests. No human-gold or population-accuracy claim. |

The Baly validation split has 1,640 LEFT, 618 CENTER and only 98 RIGHT examples.
Always report class support and macro-F1. The published split counts above are
not interchangeable with the paper's counts, and the Baly test partition does
not certify independence from the original checkpoint's training.

The PoliticalBiasCorpus overlap review found one originating Franken-allegations
episode under different event strings and repeated publisher boilerplate across
development partitions. Keep the old records intact and qualify their claims.
A new split should join related-story, duplicate and source groups before any
partition assignment. A numerical hash of an event description is not semantic
event independence.

Evidence within the repository:

- `research/results/data_manifest.json`
- `research/results/corpus_comparison_20261001.json`
- `research/results/development_overlap_review_20261002.json`
- `research/results/argument_stance_protocol_20261002.json`
- `research/annotation/pilot_manifest_v2.json`, `README.md`, and `RUBRIC.md`
- `research/EXPERIMENT_LOG.md`, especially the September 28 audit and October 1-2 corrections

## External datasets checked

| Candidate | Verified useful supervision | Why it is not replacement gold | Rights status for this project |
|---|---|---|---|
| [BABE](https://github.com/Media-Bias-Group/Neural-Media-Bias-Detection-Using-Distant-Supervision-With-BABE) | 3,700 sentences with expert bias/opinion judgments and marked words; raw expert labels are available. | Its political `type` is the outlet orientation, not each sentence's direction. Binary bias and writer opinion are useful auxiliary tasks only. | The checked repository LICENSE is GNU AGPL v3. Underlying news-excerpt rights and intended dataset scope need clarification before commercial training/redistribution. Do not substitute a model card's license. |
| [BASIL release 2](https://github.com/launchnlp/BASIL) | Lexical/informational bias spans, including quote-speaker information. Original paper reports 300 articles and 1,727 spans. | Entity-oriented bias/polarity does not directly mean LEFT/RIGHT. Release 2 corrected speaker, polarity and offset issues, so the old span total is not a verified release-2 recount. | No root LICENSE was found at the checked path; a 404 is not a full legal determination. No blanket commercial or redistribution permission established. |
| [Baly paper](https://aclanthology.org/2020.emnlp-main.404/) | Article-level ideology rather than automatically inherited source labels, according to its authors. | It lacks our independent local directional-span and relevance gold. Original-model contamination is unknown. | Pinned repository LICENSE is Apache 2.0. This does not independently establish permission over every underlying publisher's article. |

Do not merge these tasks into one undifferentiated LEFT/RIGHT dataset. If auxiliary
training is pursued, preserve the native labels, dataset identity and separate
evaluation, and test whether transfer helps the product task.

## Acquisition route that can begin now

English Wikinews explicitly licenses text created after December 16, 2024 under
CC BY 4.0, unless otherwise specified. Its policy permits attribution to
"Wikinews". The [CC BY 4.0 deed](https://creativecommons.org/licenses/by/4.0/)
allows sharing/adaptation including commercial use, subject to its conditions;
it does not grant every third-party right. Check item notices and exclude media
and rights-uncertain inclusions. [Copyright policy, revision 4991371](https://en.wikinews.org/w/index.php?title=Wikinews:Copyright&oldid=4991371).

A concrete rights-metadata conflict was found during the root agent's collector
run: both rendered seed responses included `CC-BY 2.5` citation metadata, whereas
the current policy says CC BY 4.0 for post-2024 text. Keep this conflict explicit
and require manual item-rights review before training/publication; do not silently
choose a license. A pinned page revision may still render newer transcluded
templates. Preserve the actual response hash and exclude unrelated template text.

This is a feasible acquisition candidate, not cleared or labeled data. It is also
not an ongoing contemporary-news feed: the [archive page, revision 5023041](https://en.wikinews.org/w/index.php?title=Wikinews:Archives&oldid=5023041)
states that closure was scheduled for May 4, 2026. Treat the verified 2026 material
as early-2026 archival development, with unknown model-pretraining exposure.
The site's [neutral-point-of-view policy](https://en.wikinews.org/wiki/Wikinews:Neutral_point_of_view)
does not supply an individual article label or guarantee enough directional
author framing to train a three-way classifier.

Two real, publicly inspected seed records are in `dataset_registry.json`:

| Pinned revision | Publication date | Acquisition purpose, not a gold label |
|---|---|---|
| [5004396](https://en.wikinews.org/w/index.php?title=White_House_deletes_Truth_Social_post_portraying_Obamas_as_apes&oldid=5004396) | 2026-02-07 | Political reporting with quotations and criticism |
| [5013866](https://en.wikinews.org/w/index.php?title=Former_Major_League_Baseball_pitcher_Julio_Teher%C3%A1n_retires&oldid=5013866) | 2026-03-11 | Sports reporting for relevance review |

These are deliberately inspected development candidates. The root collector
subsequently acquired both sources, preserved response and extracted-text hashes
in `wikinews_intake_summary.json`, and left all labels null. Rights and extraction
review remain pending and approved uses remain empty. The resulting 272-word
and 172-word inputs include titles. See `WIKINEWS_INTAKE.md` for the narrow
extraction procedure and its limits; these are not final-test examples. The raw
API responses are archived locally. The extracted texts are not verified complete
articles: audit every omission and supply the same frozen extracted context to
human reviewers and models before comparing their judgments.

Initial collection proposal: at most 20 eligible natural articles, covering
political reporting with quotes, straightforward policy reporting, sports,
science/health and other nonpolitical material. Categories are selection strata,
not gold labels. Record failures and actual counts; do not fabricate category
balance when eligible items are unavailable. This pool exercises context and
false-positive behavior. A separate, permissioned multi-source editorial pool
is still required to supply adequately supported author-direction examples.

The public read API is `https://en.wikinews.org/w/api.php`. Official documentation:
[revisions](https://www.mediawiki.org/wiki/API:Revisions),
[category members](https://www.mediawiki.org/wiki/API:Categorymembers), and
[parsing](https://www.mediawiki.org/wiki/API:Parsing_wikitext).

Pinned seed request parameters:

```text
action=query&format=json&formatversion=2&prop=revisions
&rvprop=ids|timestamp|content&rvslots=main&revids=5004396|5013866
```

For a small discovery pass use `action=query`, `list=categorymembers`,
`cmtitle=Category:United_States`, `cmlimit=20`, `cmsort=timestamp`, `cmdir=desc`,
`cmnamespace=0`. Category-addition timestamps are not publication dates. Fetch
content by frozen revision after selection. Use an identifiable research user
agent, sequential requests, short timeouts and bounded retry/backoff. Do not
automatically follow source-article links, recursively crawl, or include images.
The dataset agent's unprivileged API probe failed with `Operation not permitted`;
The root collector subsequently reported successful API parsing after authorized
network escalation. Its separate artifacts govern acquisition hashes and outcomes.
Web retrieval of the policy, two seed pages and API documentation succeeded.

Each retained record needs page title/ID, source URL, revision URL/ID, publication
date, retrieval timestamp, full-context text SHA-256, extraction version,
license URL/version, item-specific exception check, attribution text, source and
event-family group, supplied reading context, development exposure, and nullable
human annotation. Store the original snapshot and extraction hash separately.
The attribution should identify Wikinews and title, link the revision and
CC BY 4.0, and state that text was extracted for annotation and formatting may
have changed. Do not claim endorsement.

For the task-matched contemporary directional lane, obtain written permission
from content owners or commission original reporting/opinion across viewpoints.
Permission must explicitly cover storage, human annotation, ML training,
evaluation, and intended commercial model use; record text-redistribution rights
separately. Nothing has been requested, purchased, or cleared on their behalf
in this audit. Merely providing a URL or ordinary republishing permission is
insufficient evidence to mark every intended use approved.

## Handoff and verification

- No sealed 89-item or 726-item inputs were opened, downloaded or sent to a model.
  Published aggregate metadata was read only. No original split or label changed.
- Primary repository metadata/licenses and papers were checked, with URLs and
  observed license blob SHAs in `dataset_registry.json`. New candidate datasets
  were not downloaded wholesale; unpinned repository metadata is marked as such.
- The original 89% figure and approximately 53k training size remain unreproduced.
  Zero new independent human reviews or product-accuracy observations were made.
- Validate the registry using `python -m json.tool
  research/team_20261003/dataset_registry.json` and check numeric counts against
  the committed summary manifests. This verifies the audit artifact's structure,
  not dataset quality or legal clearance.
