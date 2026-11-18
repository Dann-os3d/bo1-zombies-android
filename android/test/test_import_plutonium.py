"""Off-device test of tools/native/import-plutonium.py (tools/native/test-plutonium.sh)."""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("imp", os.path.join(HERE, "..", "..", "tools", "native", "import-plutonium.py"))
imp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imp)


def touch(path, data=b"x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = imp.main(argv)
    return code, out.getvalue()


class ImportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t5 = os.path.join(self.tmp.name, "Plutonium", "storage", "t5")
        self.out = os.path.join(self.tmp.name, "game")
        touch(os.path.join(self.t5, "mods", "wds", "mod.ff"), b"ff")
        touch(os.path.join(self.t5, "mods", "wds", "wds.iwd"), b"iwd")
        touch(os.path.join(self.t5, "mods", "scripty", "maps", "a.gsc"), b"gsc")
        touch(os.path.join(self.t5, "mods", "bad-name", "mod.ff"), b"ff")
        os.makedirs(os.path.join(self.t5, "mods", "empty"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_import_from_plutonium_root_t5_and_mods(self):
        for src in (os.path.join(self.tmp.name, "Plutonium"), self.t5, os.path.join(self.t5, "mods")):
            code, text = run([src, "--out", self.out])
            self.assertEqual(code, 0, text)
            self.assertTrue(os.path.isfile(os.path.join(self.out, "mods", "wds", "mod.ff")))
            self.assertTrue(os.path.isfile(os.path.join(self.out, "mods", "wds", "wds.iwd")))

    def test_notes(self):
        _code, text = run([self.t5, "--out", self.out, "--dry-run"])
        self.assertIn("script-only", text)                  # scripty
        self.assertIn("rename the folder", text)            # bad-name
        self.assertIn("empty folder", text)
        self.assertIn("would import 3 of 4", text)
        self.assertFalse(os.path.exists(os.path.join(self.out, "mods")))   # dry run copies nothing

    def test_nothing_to_import(self):
        empty = os.path.join(self.tmp.name, "none", "mods")
        os.makedirs(empty)
        code, text = run([empty, "--out", self.out])
        self.assertEqual(code, 1)
        self.assertIn("nothing to import", text)

    def test_usage(self):
        self.assertEqual(run([])[0], 2)

    def test_check_game(self):
        game = os.path.join(self.tmp.name, "g")
        self.assertEqual(run(["--check-game", game])[0], 1)
        touch(os.path.join(game, "zone", "all", "x.ff"))
        code, text = run(["--check-game", game])
        self.assertEqual(code, 1)
        self.assertIn("localization.txt", text)
        touch(os.path.join(game, "localization.txt"))
        self.assertEqual(run(["--check-game", game])[0], 0)
        os.makedirs(os.path.join(game, "Call of Duty Black Ops"))
        code, text = run(["--check-game", game])
        self.assertEqual(code, 1)
        self.assertIn("nested", text)


if __name__ == "__main__":
    unittest.main()
