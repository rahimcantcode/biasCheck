import hashlib
import io
from pathlib import Path
import tarfile
import pytest
from research.scripts.setup_local_phrase_runtime import fetch_verified,extract_runtime,digest


def test_existing_verified_artifact_needs_no_network(tmp_path):
    p=tmp_path/'model';p.write_bytes(b'fixed public fixture')
    fetch_verified('https://example.invalid/model',p,hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_size)


def test_mismatched_local_artifact_rejected(tmp_path):
    p=tmp_path/'model';p.write_bytes(b'wrong')
    with pytest.raises(ValueError):fetch_verified('https://example.invalid/model',p,'0'*64,5)


def test_archive_cannot_escape_destination(tmp_path):
    a=tmp_path/'bad.tar.gz'
    with tarfile.open(a,'w:gz') as t:
        info=tarfile.TarInfo('../escape');info.size=1;t.addfile(info,io.BytesIO(b'x'))
    with pytest.raises(tarfile.FilterError):extract_runtime(a,tmp_path/'out')
    assert not (tmp_path/'escape').exists()


def test_archive_can_extract_a_regular_file(tmp_path):
    a=tmp_path/'good.tar.gz'
    with tarfile.open(a,'w:gz') as t:
        info=tarfile.TarInfo('runtime/readme');info.size=1;t.addfile(info,io.BytesIO(b'x'))
    extract_runtime(a,tmp_path/'out')
    assert (tmp_path/'out/runtime/readme').read_bytes()==b'x'
