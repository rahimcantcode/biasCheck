# Refinement schema compatibility diagnostic

2026-10-04. This is a deterministic runtime-grammar diagnostic, not a model
quality evaluation. No model was loaded and no inference was performed for it.

The aborted v2 run produced decisions missing `native_index` and `reason`.
Its generated schema put these requirements beside `oneOf`, while the two
alternatives contained only `original` and `bias_type` constraints.

## Source evidence

The pinned llama.cpp revision is
`fb4b2737a808a3fb7c2117a498f43815dc9be53e`.
In `common/json-schema.cpp`, `build_node`, lines 234–236, a node containing
`oneOf` or `anyOf` immediately returns `build_alternatives(schema.at(key), ...)`.
It does not combine the alternatives with sibling object properties or required
fields. `build_alternatives` builds each branch independently; `build_object`
reads required fields only from the branch passed to it. Therefore the v2 schema
compiled without the sibling `native_index` and `reason` requirements. This is
not the conjunction behavior of those sibling keywords in general JSON Schema.

| Evidence | SHA256 |
|---|---|
| `/tmp/llama-b11349-conversion-source/source.tar.gz` | `694497da4112aead51f4471c30919fea4b678add57b6de19ac2f61c0d72282d6` |
| Archive member `llama.cpp-fb4b2737a808a3fb7c2117a498f43815dc9be53e/common/json-schema.cpp` | `68ba2adbb6e0578c0d89e99cc9a9a7aa9c0b554b555bcd3908da71789045509d` |
| `research/checkpoints/unbias-runtime/bin/llama-b11349/libllama-common.so` | `12499566e0aa2cd1fe09cc6a34bf89f95ddedbc71ab41a66a7daaa141eb486e4` |

## Reproduction and structural correction

A small C++ probe linked against the pinned `libllama-common.so` and called
`json_schema_to_grammar(common_json::parse(input), true)`. It compiled both the
archived v2 schema and the corrected schema. The v2 grammar contained no
`native-index` or `reason` productions; each item alternative also made its
remaining fields optional. For example:

```text
decisions-item-0 ::= "{" space  (decisions-item-0-original-kv decisions-item-0-original-rest | decisions-item-0-bias-type-kv )? space "}"
```

The correction puts a complete object schema in each alternative: all four
properties, all four required fields, and `additionalProperties: false`, with
branch-specific empty/null versus nonempty/lexical constraints. The corrected
grammar requires every field in both alternatives:

```text
decisions-item-0 ::= "{" space decisions-item-0-native-index-kv "," space decisions-item-0-reason-kv "," space decisions-item-0-original-kv "," space decisions-item-0-bias-type-kv space "}"
decisions-item-1 ::= "{" space decisions-item-1-native-index-kv "," space decisions-item-1-reason-kv "," space decisions-item-1-original-kv "," space decisions-item-1-bias-type-kv space "}"
```

The generated v2 grammar SHA256 was
`0ffc502516f9e4cec6feb3207cdd27fc09e5006d5be1fcc0b9d591dc0b8e4454`;
the corrected grammar SHA256 was
`bac26abde313720c8e46868fb657e8e4aa2df27b6cae9df96ab6a58c2284871c`.
The transient probe and outputs are under `/tmp/unbias-schema-proof/`.

`tests/test_unbias_refinement.py::test_pinned_runtime_grammar_requires_all_fields`
rebuilds the probe from pinned archive headers and compares the complete item
productions, so it checks mandatory sequencing rather than mere key presence.
It skips explicitly when the pinned local source/runtime or C++ compiler is
unavailable. Run it with:

```bash
/tmp/bias-eval-venv/bin/python -m pytest tests/test_unbias_refinement.py -q
```

All 42 tests passed, including the actual converter regression. Earlier unit
tests checked Python validation and schema structure, not runtime conversion;
their success did not establish grammar compatibility.

Only the generated schema structure changed. `SYSTEM_PROMPT`,
`validate_refinement`, and `validate_model_refinement` were checked byte-for-byte
against `refinement_contract_v2.py.txt` and are unchanged. Frozen corrected
`backend/unbias/refinement.py` SHA256:
`4fd6a1b1ad8dabc93c845b43fff0c0924b37afc997b1ae17047d217987630253`.

This establishes the corrected grammar's required-field behavior. It does not
establish generation completion, semantic correctness, faithful minimal spans,
negation handling, or model accuracy. Earlier failed attempts remain preserved;
they are not reclassified as successful outputs.
