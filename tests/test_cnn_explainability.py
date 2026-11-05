import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "deep_learning" / "explainability" / "run_shap.py"
SPEC = importlib.util.spec_from_file_location("run_shap", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys_modules = __import__("sys").modules
sys_modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class ExplainabilityUnitTests(unittest.TestCase):
    def test_segmentation_round_trip_and_operators(self):
        payload = "127.0.0.1 && whoami; echo $(id)"
        segments = mod.segment_payload(payload)
        self.assertEqual("".join(segments), payload)
        self.assertIn("&&", segments)
        self.assertIn(";", segments)
        self.assertIn("$(", segments)

    def test_mask_preserves_length_and_hides_segment(self):
        segments = ["echo", " ", "&&", " ", "id"]
        masked = mod.apply_mask(segments, np.array([1, 1, 0, 1, 1]))
        self.assertEqual(len(masked), len("".join(segments)))
        self.assertEqual(masked, "echo    id")

    def test_lime_ranks_causal_feature_highest(self):
        def predictor(masks):
            masks = np.atleast_2d(masks)
            return 0.1 + 0.8 * masks[:, 1]
        values = mod.lime_attributions(predictor, 4, num_samples=800, seed=42)
        self.assertEqual(int(np.argmax(np.abs(values))), 1)
        self.assertGreater(values[1], 0.7)

    def test_group_selection_is_deterministic(self):
        df = pd.DataFrame({
            "payload_id": ["a", "b", "c", "d"], "payload": ["x"] * 4,
            "label": [1, 1, 0, 0], "source": ["normal", "held", "normal", "normal"],
        })
        grouped = mod.assign_groups(df, np.array([0.9, 0.1, 0.2, 0.8]), "held")
        self.assertEqual(grouped.group.tolist(), ["true_positive", "holdout_source", "true_negative", "false_positive"])
        first = mod.choose_samples(grouped, 1, 42)
        second = mod.choose_samples(grouped, 1, 42)
        self.assertEqual(first.payload_id.tolist(), second.payload_id.tolist())


if __name__ == "__main__":
    unittest.main()
