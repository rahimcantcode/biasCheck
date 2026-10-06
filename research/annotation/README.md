# The first 100-example review pilot

Prepared 2026-09-29. Human reviews completed: **0**. No gold labels assigned.

- 60 real historical articles from 12 dataset source identifiers and 41 topics.
- 40 original AI-authored controlled examples addressing ordinary nonpolitical text, political word false positives, procedural reporting, policy positions, attribution, mixed views, and inadequate context.
- No news article text is redistributed here. The manifest stores original links, IDs and frozen text hashes; article text is loaded locally from the source dataset.
- No model predictions or inherited dataset class labels appear in the review screen or manifest. Sample selection uses source/topic/length diversity, not class labels, and excludes the 60 articles from our earlier model comparison. This does not establish independence from historical model training.

## Start reviewing

Open **Bias_Checker_Review_Pilot.html** in your browser. The 40 controlled examples are immediately available. Choose a unique reviewer ID such as `Rahim-A` and click **Open my workspace**. Read RUBRIC.md first.

For the 60 historical articles, click **Load article snapshots**. The page downloads the pinned files directly from GitHub and verifies their hashes. If downloads are blocked or you prefer offline review, obtain the pinned source dataset on your own computer:

```bash
git clone https://github.com/ramybaly/Article-Bias-Prediction research-data
git -C research-data checkout ced8111a720948e6a410e52031ace99c4e53f096
```

In the review page, choose the dataset's `data/jsons` folder. Only the 60 matching filenames are read. Each text hash must match the frozen manifest before a judgment can be saved. Read the source JSON's `content_original` only; do not consult its `bias_text` legacy label. The viewer hides that label automatically.

If the browser blocks local folder/hash features, serve the annotation folder locally using `python -m http.server 8765 --bind 127.0.0.1` and open `http://localhost:8765/Bias_Checker_Review_Pilot.html`.

Do not substitute changed live article text for a frozen snapshot. The original URLs are references, not verified replacements. If a source file is unavailable, record a skip with a reason.

### Offline snapshot bundle

The **Offline snapshot bundle** file picker accepts the local `texts.json` emitted
by `research/scripts/pilot_context_audit.py`: an array of `{id, text}` records for
all 100 frozen pilot items. The existing verified copy is at
`research/checkpoints/pilot-context-20261003/texts.json` (not committed).
Every ID must occur exactly once and every text must match its manifest SHA-256.
Missing, duplicate, unknown, or altered items reject the entire import without
changing loaded texts. Loading preserves the current unsaved judgment. No
predictions or labels are imported, and no network request is made by this path.
Keep article snapshots local; source reuse rights have not been cleared for
redistribution. This is still a development pilot, not an independent test set.

Save each judgment before moving on. Export your JSON frequently. Local browser storage is convenient, not a durable backup. Article text is not sent to a server, stored in review exports, or transmitted to a model. Exported files contain your ID, judgments, paraphrased rationales and timestamps.

If browser storage fails, recorded judgments remain in memory and can still be
exported. The warning persists across item navigation, and switching reviewer
workspaces is blocked while records are unpersisted. Export before closing the
tab. A subsequent successful save persists all recorded judgments and clears the
storage warning; initiating a download alone does not prove it was saved to disk.

A second reviewer should work independently with a separate reviewer ID and browser profile. Review the first 10 items, discuss rule ambiguities, and then independently re-review those items if the rubric changes. Do not treat the earlier and later passes as independent reviewers.

## Compare completed reviews

```bash
python compare_reviews.py --first review-Rahim-A.json --second review-reviewer-B.json --output agreement.json
```

The tool validates identities, frozen text hashes, required evidence and label consistency. It reports relevance and final-label agreement, Cohen's kappa, paired denominators, historical versus controlled slices, and an adjudication queue. It never manufactures missing judgments or approves gold labels.

Reviewer IDs differing only by surrounding whitespace, case, or Unicode
compatibility forms are not accepted as distinct reviewers. Original IDs remain
unchanged in exports and reports; each row must still exactly match its export's
reviewer ID. Reviewed and skipped items must have a calendar-valid ISO completion
datetime with an explicit timezone (`Z` or a numeric offset). Duplicate manifest
IDs are rejected, even if their contents match. These checks cannot authenticate
a reviewer, verify a claimed timestamp, or prove independent human judgment.

Every manifest item must have a valid text SHA-256, and distinct IDs may not share
the same text fingerprint (hash comparison is case-insensitive). This prevents
exact snapshots being counted twice, including items not yet reviewed. It does
not detect near-duplicate articles or establish source/event independence.

Preserve the two independent exports. Adjudicate differences with documented reasoning and reviewer identity. A future gold dataset requires completed adjudication and explicit human sign-off. All pilot items remain development data, excluded from the later final evaluation.

## Reproduce

From the repository root, with the pinned dataset at `../research-data`:

```bash
python research/annotation/build_pilot.py
python research/annotation/render_reviewer.py
```

The seed and frozen manifest preserve selection/order. Do not regenerate IDs after annotation starts. Change the pilot version if content, ordering or rubric changes.

## What this does not complete

No independent human annotation, contemporary news collection, model retraining, accuracy measurement or production release is claimed. The historical dataset's source availability and reuse rights must be reviewed before further distribution or commercial use. Synthetic examples stress specific behaviors but do not estimate real-world performance.
