# Secondary failure sensitivity

Recorded during the corrected run, after its first successful active call and
before scoring. This supplements rather than changes the frozen comparison.

The primary report retains all 60 outcomes, including upstream and refinement
failures. Token precision is conditional on delivered highlights: withholding
a failed request can remove both true and false positive tokens.

If any refinement requests fail, also compare baseline and refined spans on
exactly the same successfully refined requests, separately for the lexical/
unannotated strata and for all strata. Use the unchanged scorer and reference
filters. Report sample sizes, token numerators and denominators, and recall.
This selected-success sensitivity is descriptive and does not establish
generalization or compensate for lost service coverage. Do not count failed
withheld highlights as intentional model drop decisions.
