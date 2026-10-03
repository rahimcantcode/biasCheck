# Two-article acquisition smoke, not a labeled dataset

On 2026-10-03 the lead retrieved two explicitly pinned Wikinews article revisions
through the public MediaWiki API. The saved responses yielded 10 and 4 body
paragraphs, with 272 and 172 words including their titles. The archived articles
were published in February and March 2026. They are convenience-selected examples
from one publisher, not a balanced or representative news corpus. No model was
run on them and no human or AI political labels were assigned.

`wikinews_intake_summary.json` preserves source URLs, titles, attribution,
publication dates, actual response and extracted-text SHA-256 hashes, extraction
changes, and pending review status. Full API responses and extracted text are
kept only in ignored `research/data/` storage. The policy indicates CC BY 4.0
for post-transition text, while both pages' embedded citation metadata says
CC-BY 2.5. That conflict is recorded rather than silently resolved. Neither item
has approved training, annotation or evaluation uses in the intake manifest.
Images are not acquired. Page-specific rights, quoted third-party material and
extraction fidelity require review before use.

The extractor retains the title and top-level paragraphs before the first
section heading, normalizes whitespace, and excludes navigation, date banner,
images, references and subsequent sections. It is a narrow collector for two
reviewed revisions, not a generic full-article extractor. Page `oldid` does not
freeze transcluded templates; response hashes identify the actual retrieved
bytes. Human reviewers and any future model must receive the same frozen text.

## Reproduce

From the repository root, use a fresh output directory:

```bash
python research/scripts/collect_wikinews_pilot.py \
  --output research/data/wikinews-new-intake
python research/scripts/validate_dataset_manifest.py \
  research/data/wikinews-new-intake/dataset_manifest.json
```

To replay saved responses without network access, provide `--snapshots DIRECTORY`
containing `5004396.json` and `5013866.json`. An optional `--public-summary PATH`
writes metadata only and refuses to overwrite that path. Each acquisition uses
at most two bounded API requests with no model inference.

The observed validator result is structurally valid but **not ready for final
evaluation**: rights and human review are unresolved; the protocol is not frozen;
there is no calibration or final-test split and no independent clustering audit.
Provisional story identifiers only separate these two visibly different topics;
they do not establish an exhaustive event-family or near-duplicate audit. Both
examples are permanently development material after team inspection.

Ten synthetic parser/integration tests passed with pytest 9.0.3. These exercise
source boundaries, hashes, Unicode, revision/date rejection, missing bodies,
non-overwriting replay and rejection of evaluation readiness. They do not prove
political accuracy, legal clearance or natural-text extraction fidelity.

Sources: [pinned copyright policy](https://en.wikinews.org/w/index.php?title=Wikinews:Copyright&oldid=4991371),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
[MediaWiki parse API](https://www.mediawiki.org/wiki/API:Parsing_wikitext).
