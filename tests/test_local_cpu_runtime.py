import hashlib
import json
from pathlib import Path
import pytest
from research.scripts import local_cpu_runtime as module


def prepare(monkeypatch,tmp_path):
    install=tmp_path/'installed';repo=tmp_path/'repo';(repo/'research').mkdir(parents=True)
    weights=install/'models/test.gguf';weights.parent.mkdir(parents=True);weights.write_bytes(b'model fixture')
    server=install/'runtime/bin/server';server.parent.mkdir(parents=True);server.write_bytes(b'binary fixture')
    catalog={'models':{'qwen3_4b':{'file':'test.gguf','sha256':hashlib.sha256(weights.read_bytes()).hexdigest()}},
             'runtime':{'server_relative_path':'bin/server','server_sha256':hashlib.sha256(server.read_bytes()).hexdigest()}}
    raw=json.dumps(catalog).encode();(repo/'research/local_phrase_runtime.json').write_bytes(raw)
    record={'manifest_sha256':hashlib.sha256(raw).hexdigest(),'model_key':'qwen3_4b','model':catalog['models']['qwen3_4b'],'runtime':catalog['runtime'],'release_approved':False}
    path=install/'qwen3_4b.installed.json';path.write_text(json.dumps(record))
    monkeypatch.setattr(module,'ROOT',install);monkeypatch.setattr(module,'REPOSITORY',repo);monkeypatch.delenv('BIASCHECK_LOCAL_MODEL',raising=False)
    return weights,path


def test_launcher_uses_only_pinned_installation_paths(monkeypatch,tmp_path):
    weights,_=prepare(monkeypatch,tmp_path);r=module.LlamaRuntime()
    assert r.weights==weights
    assert '--offline' in r.command and '--no-agent' in r.command and '--no-context-shift' in r.command
    assert r.command[r.command.index('--host')+1]=='127.0.0.1'


def test_changed_weights_fail_before_executable_start(monkeypatch,tmp_path):
    weights,_=prepare(monkeypatch,tmp_path);r=module.LlamaRuntime();weights.write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):r.__enter__()


def test_tampered_installation_record_rejected(monkeypatch,tmp_path):
    _,path=prepare(monkeypatch,tmp_path);r=json.loads(path.read_text());r['model']['sha256']='0'*64;path.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='catalog'):module.LlamaRuntime()


def test_unknown_model_does_not_read_arbitrary_path(monkeypatch,tmp_path):
    prepare(monkeypatch,tmp_path);monkeypatch.setenv('BIASCHECK_LOCAL_MODEL','../../private')
    with pytest.raises(ValueError,match='Unknown'):module.LlamaRuntime()
