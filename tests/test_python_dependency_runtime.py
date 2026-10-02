"""Dependency compatibility checks without downloaded weights or network access."""
import torch
from transformers import AutoModelForSequenceClassification, RobertaConfig, RobertaForSequenceClassification


def test_tiny_roberta_safetensors_round_trip(tmp_path):
    """Exercise the real lazy model import and loading-info contract used by serving.

    Mocked API tests did not catch Transformers 5.10.4 importing a dtype absent
    from torch 2.6.0. A tiny random checkpoint is enough to detect that regression;
    this is not a political-label accuracy or production checkpoint test.
    """
    torch.manual_seed(0)
    config = RobertaConfig(
        vocab_size=16, hidden_size=8, intermediate_size=16,
        num_hidden_layers=1, num_attention_heads=2, max_position_embeddings=16,
        num_labels=3, id2label={0: 'LEFT', 1: 'CENTER', 2: 'RIGHT'},
        label2id={'LEFT': 0, 'CENTER': 1, 'RIGHT': 2},
    )
    original = RobertaForSequenceClassification(config).eval()
    original.save_pretrained(tmp_path, safe_serialization=True)
    loaded, info = AutoModelForSequenceClassification.from_pretrained(
        tmp_path, local_files_only=True, use_safetensors=True,
        trust_remote_code=False, output_loading_info=True,
    )
    assert not any(info.get(key) for key in (
        'missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs',
    ))
    loaded.eval()
    encoded = {'input_ids': torch.tensor([[0, 4, 5, 2]]),
               'attention_mask': torch.tensor([[1, 1, 1, 1]])}
    with torch.inference_mode():
        before, after = original(**encoded).logits, loaded(**encoded).logits
    assert tuple(after.shape) == (1, 3)
    assert torch.isfinite(after).all()
    # Attention backend selection can differ after loading. Allow only ordinary
    # float32 roundoff rather than requiring bit-for-bit identical execution.
    torch.testing.assert_close(before, after, rtol=1e-5, atol=1e-7)
    assert loaded.config.id2label == {0: 'LEFT', 1: 'CENTER', 2: 'RIGHT'}


def tokenizer_fixture():
    from types import SimpleNamespace
    from tokenizers import Tokenizer, models, pre_tokenizers, processors
    backend = Tokenizer(models.WordLevel({'[UNK]': 0, '<s>': 1, '</s>': 2,
                                          'word': 3, 'café': 4, 'bridge': 5}, unk_token='[UNK]'))
    backend.pre_tokenizer = pre_tokenizers.Whitespace()
    backend.post_processor = processors.TemplateProcessing(
        single='<s> $A </s>', special_tokens=[('<s>', 1), ('</s>', 2)])
    return SimpleNamespace(backend_tokenizer=backend, num_special_tokens_to_add=lambda pair=False: 2)


def test_legacy_special_token_builder_is_preserved():
    from types import SimpleNamespace
    from backend.model import prepare_window_features
    tokenizer = SimpleNamespace(build_inputs_with_special_tokens=lambda ids: [7, *ids, 8])
    assert prepare_window_features(tokenizer, None, [([3, 4], 0, 2, 2)], 10, 2) == [
        {'input_ids': [7, 3, 4, 8]}]


def test_v5_window_processor_preserves_ids_and_input_encoding():
    from types import SimpleNamespace
    from backend.model import prepare_window_features, token_windows
    tokenizer = tokenizer_fixture()
    for length in (1, 9, 10, 11, 18, 19, 20, 50):
        text = ' '.join(['word', 'café', 'bridge'][i % 3] for i in range(length))
        encoding = tokenizer.backend_tokenizer.encode(text, add_special_tokens=False)
        ids = encoding.ids
        windows = list(token_windows(ids, capacity=10, stride=2))
        features = prepare_window_features(tokenizer, SimpleNamespace(encodings=[encoding]), windows, 10, 2)
        assert [f['input_ids'] for f in features] == [[1, *w[0], 2] for w in windows]
        assert encoding.ids == ids and not encoding.overflowing
        assert sum(w[3] for w in windows) == length


def test_v5_window_processor_fails_closed_on_changed_content():
    from types import SimpleNamespace
    import pytest
    from backend.model import prepare_window_features
    tokenizer = tokenizer_fixture()
    encoding = tokenizer.backend_tokenizer.encode('word café', add_special_tokens=False)
    with pytest.raises(RuntimeError, match='changed token window content'):
        prepare_window_features(tokenizer, SimpleNamespace(encodings=[encoding]), [([5, 5], 0, 2, 2)], 10, 2)


def test_v5_window_processor_requires_a_safe_encoding():
    import pytest
    from backend.model import prepare_window_features
    with pytest.raises(RuntimeError, match='cannot safely prepare'):
        prepare_window_features(tokenizer_fixture(), None, [([3], 0, 1, 1)], 10, 2)


def runtime_policy_fixture():
    from copy import deepcopy
    from backend.model import WINDOW_PREPARATION_PROCESSOR
    runtime = dict(schema_version=1, torch='2.13.0+cpu', transformers='5.10.4',
                   tokenizers='0.22.2', window_preparation=WINDOW_PREPARATION_PROCESSOR,
                   device='cpu', dtype='torch.float32', attention_implementation='sdpa', batch_size=4)
    metadata = dict(weights_sha256='synthetic-weights', config_sha256='synthetic-config',
                    tokenizer_sha256='synthetic-tokenizer', aggregation='synthetic-aggregation',
                    max_length=512, stride=64, preprocessing='synthetic-preprocessing',
                    inference_runtime=runtime, id2label={'0': 'LEFT', '1': 'CENTER', '2': 'RIGHT'})
    policy = {**deepcopy(metadata), 'schema_version': 1, 'release_approved': False,
              'temperature': 1., 'min_confidence': .7, 'min_margin': .2,
              'min_tokens': 30, 'validated_modes': ['article']}
    return metadata, policy


def test_runtime_identity_is_observed_from_model_and_tokenizer():
    from types import SimpleNamespace
    from backend.model import inference_runtime, get_settings, WINDOW_PREPARATION_PROCESSOR
    model = torch.nn.Linear(2, 2, dtype=torch.float64)
    model.config = SimpleNamespace(_attn_implementation='eager')
    identity = inference_runtime(model, tokenizer_fixture())
    assert identity['dtype'] == 'torch.float64' and identity['device'] == 'cpu'
    assert identity['attention_implementation'] == 'eager'
    assert identity['batch_size'] == get_settings().batch_size
    assert identity['window_preparation'] == WINDOW_PREPARATION_PROCESSOR
    assert identity['torch'] == str(torch.__version__)


def test_runtime_identity_rejects_unknown_attention():
    from types import SimpleNamespace
    import pytest
    from backend.model import inference_runtime
    model = torch.nn.Linear(2, 2)
    model.config = SimpleNamespace(_attn_implementation='unknown')
    with pytest.raises(RuntimeError, match='Unobserved inference_runtime'):
        inference_runtime(model, tokenizer_fixture())


def test_identical_complete_runtime_policy_is_accepted_without_approving_release():
    from backend.model import validate_policy
    metadata, policy = runtime_policy_fixture()
    assert validate_policy(policy, metadata) is policy
    assert policy['release_approved'] is False


def test_every_runtime_component_is_bound():
    from backend.model import validate_policy, WINDOW_PREPARATION_LEGACY
    import pytest
    changes = dict(torch='2.6.0+cpu', transformers='4.57.1', tokenizers='0.22.1',
                   window_preparation=WINDOW_PREPARATION_LEGACY, device='cuda:0',
                   dtype='torch.float16', attention_implementation='eager', batch_size=1)
    for key, value in changes.items():
        metadata, policy = runtime_policy_fixture()
        policy['inference_runtime'][key] = value
        with pytest.raises(RuntimeError, match='does not match model: inference_runtime'):
            validate_policy(policy, metadata)


def test_missing_runtime_on_either_or_both_sides_is_rejected():
    from backend.model import validate_policy
    import pytest
    for missing in ('policy', 'metadata', 'both'):
        metadata, policy = runtime_policy_fixture()
        if missing in ('policy', 'both'):
            del policy['inference_runtime']
        if missing in ('metadata', 'both'):
            del metadata['inference_runtime']
        with pytest.raises(RuntimeError, match='incomplete inference_runtime'):
            validate_policy(policy, metadata)


def test_partial_runtime_on_both_sides_does_not_implicitly_match():
    from backend.model import validate_policy, INFERENCE_RUNTIME_FIELDS
    import pytest
    for key in INFERENCE_RUNTIME_FIELDS:
        metadata, policy = runtime_policy_fixture()
        del policy['inference_runtime'][key]
        del metadata['inference_runtime'][key]
        with pytest.raises(RuntimeError, match='incomplete inference_runtime'):
            validate_policy(policy, metadata)


def test_runtime_schema_types_and_unobserved_values_fail_closed():
    from backend.model import validate_policy
    import pytest
    mutations = [('schema_version', True), ('schema_version', 1.0), ('schema_version', 2),
                 ('batch_size', True), ('batch_size', 4.0), ('batch_size', 0),
                 ('batch_size', 9), ('window_preparation', 'unknown'),
                 ('torch', ''), ('torch', 'unknown'), ('transformers', None),
                 ('transformers', 'unknown'), ('tokenizers', 22), ('tokenizers', 'unknown'),
                 ('device', 'unknown'), ('dtype', 'unknown'),
                 ('attention_implementation', ''), ('attention_implementation', 'unknown')]
    for key, value in mutations:
        metadata, policy = runtime_policy_fixture()
        metadata['inference_runtime'][key] = value
        policy['inference_runtime'][key] = value
        with pytest.raises(RuntimeError, match='inference_runtime'):
            validate_policy(policy, metadata)


def calibration_fixture():
    metadata, _ = runtime_policy_fixture()
    return {'split': 'validation', 'mode': 'article', 'data_sha256': 'synthetic-calibration',
            'annotation_provenance': {'human_reviewed': True, 'reference': 'synthetic unit-test fixture only'},
            'model': metadata,
            'predictions': [{'gold': ['LEFT', 'CENTER', 'RIGHT'][i % 3],
                             'logits': [10. if j == i % 3 else 0. for j in range(3)],
                             'token_count': 40} for i in range(102)]}


def test_calibration_rejects_legacy_runtime_before_fitting(monkeypatch):
    import pytest
    from research.scripts import calibrate
    monkeypatch.setattr(calibrate, 'minimize_scalar', lambda *a, **kw: pytest.fail('legacy report reached fitting'))
    for mutation in ('missing', 'partial'):
        report = calibration_fixture()
        if mutation == 'missing':
            del report['model']['inference_runtime']
        else:
            del report['model']['inference_runtime']['torch']
        with pytest.raises(ValueError, match='complete inference_runtime'):
            calibrate.fit(report)


def test_calibration_copies_runtime_and_stays_unapproved():
    from research.scripts.calibrate import fit
    report = calibration_fixture()
    policy = fit(report)
    assert policy['inference_runtime'] == report['model']['inference_runtime']
    assert policy['inference_runtime'] is not report['model']['inference_runtime']
    assert policy['release_approved'] is False


def test_offline_evaluation_rejects_calibration_test_runtime_drift():
    from copy import deepcopy
    import pytest
    from research.scripts.evaluate_policy import evaluate
    metadata, policy = runtime_policy_fixture()
    for changed_report in ('test', 'validation'):
        report = {'model': deepcopy(metadata)}
        validation = {'model': deepcopy(metadata)}
        (report if changed_report == 'test' else validation)['model']['inference_runtime']['torch'] = '2.6.0+cpu'
        with pytest.raises(RuntimeError, match='does not match model: inference_runtime'):
            evaluate(report, policy, validation)


def test_v5_processor_preserves_literal_special_tokens_in_article():
    from types import SimpleNamespace
    from backend.model import prepare_window_features, token_windows
    tokenizer = tokenizer_fixture()
    tokenizer.backend_tokenizer.add_special_tokens(['<s>', '</s>'])
    encoding = tokenizer.backend_tokenizer.encode('<s> word </s> café', add_special_tokens=False)
    assert encoding.ids == [1, 3, 2, 4]
    windows = list(token_windows(encoding.ids, capacity=10, stride=2))
    features = prepare_window_features(tokenizer, SimpleNamespace(encodings=[encoding]), windows, 10, 2)
    assert features == [{'input_ids': [1, 1, 3, 2, 4, 2]}]
