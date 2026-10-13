"""Bootstrap-Steuerung isoliert; Git-Transport und Claude-Prozess sind Test-Doubles."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_with_own_url_and_repeat(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            bin_dir = base / 'bin'
            bin_dir.mkdir()
            (bin_dir / 'git').write_text('#!/usr/bin/env python3\nimport sys, shutil\nshutil.copytree(' + repr(str(ROOT)) + ', sys.argv[-1], ignore=shutil.ignore_patterns(".git", "__pycache__"))\n')
            (bin_dir / 'claude').write_text('#!/usr/bin/env python3\nimport sys, os\nfrom pathlib import Path\nPath(os.environ["BRAND_SETUP_HOME"]).joinpath("invocation.txt").write_text(sys.argv[1] + "\\n" + os.getcwd())\n')
            for p in bin_dir.iterdir():
                p.chmod(0o755)
            home = base / 'home'
            env = {**os.environ, 'PATH': str(bin_dir) + os.pathsep + os.environ['PATH'], 'BRAND_SETUP_HOME': str(home)}
            for _ in range(2):
                result = subprocess.run(['bash', str(ROOT / 'scripts/bootstrap.sh'), 'https://example.com'], env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((home / 'invocation.txt').read_text(), '/brand-setup https://example.com\n' + str((home / 'brand-work').resolve()))
            self.assertTrue((home / '.claude/skills/brand-setup/SKILL.md').is_file())
            self.assertFalse((home / '.claude/CLAUDE.md').exists())
            bad = subprocess.run(['bash', str(ROOT / 'scripts/bootstrap.sh'), 'https://user:pass@example.com'], env=env, capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)


if __name__ == '__main__':
    unittest.main()
