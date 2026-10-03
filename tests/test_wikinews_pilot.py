"""Synthetic parser contracts only; no news labels or network access."""
import hashlib
import json
import pytest
from research.scripts.collect_wikinews_pilot import SEEDS, collect, extract


def snapshot(revision=5004396, date="2026-02-07"):
    body = "An ordinary report with a quoted position and enough context to exercise exact source preservation. " * 2
    html = f'''<div class="mw-parser-output">
    <p><strong class="published"><span id="publishDate" title="{date}"></span>Date</strong>
    <span title="rft.rights=CC-BY+2.5"></span></p>
    <div class="infobox"><p>Exclude this navigation.</p></div>
    <p>{body}<a>café 😀</a></p>
    <figure><figcaption><p>Exclude image caption.</p></figcaption></figure>
    <div><p>Exclude comment box.</p></div>
    <div><h2>Sources</h2></div><p>Exclude references.</p></div>'''
    return json.dumps({"parse": {"revid": revision, "title": SEEDS[revision], "text": html}}).encode()


def test_source_boundary_unicode_and_honest_provenance():
    raw = snapshot()
    text, item = extract(raw, 5004396)
    assert "café 😀" in text and "Exclude" not in text
    assert item["paragraph_count"] == 1
    assert item["text_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert item["raw_response_sha256"] == hashlib.sha256(raw).hexdigest()
    assert item["rights"]["metadata_conflict"] is True
    assert item["rights"]["approved_uses"] == []
    assert item["label"] is None and item["human_review_count"] == 0
    assert item["split"] == "development"
    assert not item["training_approved"] and not item["final_test_eligible"]


@pytest.mark.parametrize("revision", [True, 123, "5004396"])
def test_unreviewed_revision_rejected(revision):
    with pytest.raises(ValueError):
        extract(snapshot(), revision)


def test_wrong_snapshot_rejected():
    with pytest.raises(ValueError, match="mismatch"):
        extract(snapshot(5013866), 5004396)


def test_pre_transition_date_rejected():
    with pytest.raises(ValueError, match="transition"):
        extract(snapshot(date="2024-12-16"), 5004396)


def test_api_error_and_empty_body_rejected():
    with pytest.raises(ValueError):
        extract(b'{"error":{"info":"not found"}}', 5004396)
    page = json.loads(snapshot())
    page["parse"]["text"] = '<div class="mw-parser-output"><span id="publishDate" title="2026-02-07"></span></div>'
    with pytest.raises(ValueError, match="body"):
        extract(json.dumps(page).encode(), 5004396)


def test_closed_root_never_collects_sibling_footer():
    page = json.loads(snapshot())
    page["parse"]["text"] = page["parse"]["text"].replace('<div><h2>Sources</h2></div><p>Exclude references.</p>', '')
    page["parse"]["text"] += '<div><p>Sibling footer must not become article text.</p></div>'
    text, _ = extract(json.dumps(page).encode(), 5004396)
    assert "Sibling footer" not in text


def test_heading_outside_root_does_not_hide_article():
    page = json.loads(snapshot())
    page["parse"]["text"] = '<h1>Outside root heading</h1>' + page["parse"]["text"]
    text, _ = extract(json.dumps(page).encode(), 5004396)
    assert "ordinary report" in text


def test_replay_without_network_preserves_unlabeled_records(tmp_path):
    source = tmp_path / "snapshots"
    source.mkdir()
    for revision in SEEDS:
        (source / f"{revision}.json").write_bytes(snapshot(revision))
    output = tmp_path / "output"
    result = collect(output, source)
    assert len(result["items"]) == 2 and not result["release_approved"]
    assert result["retrieval_mode"] == "saved_api_snapshots"
    assert all("text" not in row and row["label"] is None for row in result["items"])
    manifest = json.loads((output / "dataset_manifest.json").read_text())
    assert all(row["review"]["status"] == "pending" for row in manifest["records"])
    assert all(row["source"]["rights_status"] == "unresolved" for row in manifest["records"])
    from research.scripts.validate_dataset_manifest import validate_manifest
    checked = validate_manifest(manifest)
    assert not checked["release_approved"]
    assert checked["errors"] == []
    with pytest.raises(ValueError, match="fresh"):
        collect(output, source)
