"""Unit tests for baseline.assert_manifest_fresh (stale-manifest guard).

Guards against editing the plot registry CSV but running ndvi/baseline.py
without re-parsing it (ndvi/registry.py), which would otherwise silently
ignore the new/edited plots. Pure filesystem - no Earth Engine, no network.
Run:  python -m unittest discover tests
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "ndvi"))
import baseline  # noqa: E402
from pipeline_utils import PipelineError  # noqa: E402


class ManifestFreshnessTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        d = Path(self._tmp.name)
        self.csv = d / "baseline_plots.csv"
        self.manifest = d / "plots_normalized.json"
        self.csv.write_text("plot_id\n")
        self.manifest.write_text("{}")

    def tearDown(self):
        self._tmp.cleanup()

    def _set_mtimes(self, csv_mtime, manifest_mtime):
        os.utime(self.csv, (csv_mtime, csv_mtime))
        os.utime(self.manifest, (manifest_mtime, manifest_mtime))

    def test_raises_when_manifest_older_than_csv(self):
        self._set_mtimes(csv_mtime=2000, manifest_mtime=1000)
        with self.assertRaises(PipelineError) as ctx:
            baseline.assert_manifest_fresh(self.csv, self.manifest)
        self.assertEqual(ctx.exception.cause, "stale-manifest")

    def test_passes_when_manifest_newer_than_csv(self):
        self._set_mtimes(csv_mtime=1000, manifest_mtime=2000)
        baseline.assert_manifest_fresh(self.csv, self.manifest)  # no raise

    def test_passes_when_mtimes_equal(self):
        self._set_mtimes(csv_mtime=1500, manifest_mtime=1500)
        baseline.assert_manifest_fresh(self.csv, self.manifest)  # no raise

    def test_passes_when_manifest_missing(self):
        # registry.py's own missing-manifest handling owns this case.
        self.manifest.unlink()
        os.utime(self.csv, (2000, 2000))
        baseline.assert_manifest_fresh(self.csv, self.manifest)  # no raise


if __name__ == "__main__":
    unittest.main()
