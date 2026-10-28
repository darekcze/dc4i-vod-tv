#!/usr/bin/env python3
"""Fast offline-only contract checks for the reproducible QA runner."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "vodtv_qa_runner", Path(__file__).with_name("run_fullstack_offline_qa.py")
)
assert SPEC and SPEC.loader
qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa)


class OfflineQAContract(unittest.TestCase):
    def test_static_suite_is_complete_and_unique(self):
        self.assertEqual(len(qa.NODE_TESTS), 50)
        self.assertEqual(len(set(qa.NODE_TESTS)), 50)
        self.assertEqual(len(qa.test_cases(Path("/tmp/never-use-this-fixture"))), 56)
        for suite in qa.NODE_TESTS:
            self.assertTrue(suite.startswith("test_"))
            self.assertNotIn("/", suite)
            self.assertNotIn("..", suite)

    def test_production_build_and_credentials_are_excluded(self):
        names = [
            ".git", "build", "private", "dist", "node_modules", "keys.js",
            ".env", "fixture.ipk", "test_user.mjs"
        ]
        ignored = qa.ignore_private("/unused", names)
        for name in (".git", "build", "private", "dist", "node_modules", "keys.js", "fixture.ipk"):
            self.assertIn(name, ignored)
        self.assertNotIn("test_user.mjs", ignored)

    def test_missing_fixture_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(qa.QAError):
                qa.verify_fixture(Path(tmp))

    def test_fixture_with_production_app_identity_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "OFFLINE_FIXTURE_ONLY.txt").write_text("only for QA\n")
            (root / "fixture-provenance.json").write_text('{"projectCommit":"untrusted"}')
            app = root / "build" / "dc4i-vodtv"
            app.mkdir(parents=True)
            (app / "appinfo.json").write_text('{"id":"com.dc4i.vodtv"}')
            with self.assertRaisesRegex(qa.QAError, "production application identity"):
                qa.verify_fixture(root)

    def test_receipt_must_not_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "receipt.json"
            existing.write_text("sentinel")
            with self.assertRaises(qa.QAError):
                qa.run(root, root, existing, 1)
            self.assertEqual(existing.read_text(), "sentinel")


if __name__ == "__main__":
    unittest.main()
