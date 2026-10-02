import copy
import sys
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from stance_contract import validate


class StanceContractTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"id": "a", "text": "The witness said lower taxes. The report takes no position."}]
        self.pred = {"id": "a", "political": True, "author_stance": "CENTER", "evidence": [],
                     "attributed_stances": [{"evidence_span": "lower taxes", "stance": "RIGHT"}],
                     "rationale": "Attributed statement without author endorsement."}

    def test_valid_attribution(self):
        validate(self.rows, {"predictions": [self.pred]})

    def test_invented_quote_rejected(self):
        self.pred["attributed_stances"][0]["evidence_span"] = "higher taxes"
        with self.assertRaises(ValueError):
            validate(self.rows, {"predictions": [self.pred]})

    def test_unsupported_direction_rejected(self):
        self.pred["author_stance"] = "LEFT"
        with self.assertRaises(ValueError):
            validate(self.rows, {"predictions": [self.pred]})

    def test_nonpolitical_direction_rejected(self):
        self.pred["political"] = False
        with self.assertRaises(ValueError):
            validate(self.rows, {"predictions": [self.pred]})

    def test_missing_duplicate_and_unknown_ids(self):
        for predictions in ([], [self.pred, copy.deepcopy(self.pred)], [dict(self.pred, id="other")]):
            with self.assertRaises(ValueError):
                validate(self.rows, {"predictions": predictions})

    def test_extra_fields_rejected(self):
        self.pred["confidence"] = .99
        with self.assertRaises(jsonschema.ValidationError):
            validate(self.rows, {"predictions": [self.pred]})

    def test_empty_span_rejected(self):
        self.pred["evidence"] = [""]
        with self.assertRaises(ValueError):
            validate(self.rows, {"predictions": [self.pred]})

    def test_nonpolitical_attribution_rejected(self):
        self.pred.update(political=False, author_stance="INSUFFICIENT")
        with self.assertRaises(ValueError):
            validate(self.rows, {"predictions": [self.pred]})

    def test_empty_rationale_rejected(self):
        self.pred["rationale"] = "   "
        with self.assertRaises(ValueError):
            validate(self.rows, {"predictions": [self.pred]})
