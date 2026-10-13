import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/install.py'
spec = importlib.util.spec_from_file_location('installer', SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def fixture(root):
    root.mkdir()
    for name in installer.REQUIRED:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('# Fiktive Testmarke\n', encoding='utf-8')
    (root / 'preview/index.html').write_text('<link href="../tokens/tokens.css" rel="stylesheet"><link href="../tokens/fonts.css" rel="stylesheet"><link href="../components/components.css" rel="stylesheet"><p>Testmarke</p>')
    (root / 'evidence.json').write_text(json.dumps([{'id': 'color-1', 'status': 'observed', 'source_url': 'https://example.com', 'selector': ':root', 'reason': 'Test-Fixture, keine echte Extraktion'}]))
    (root / 'manifest.json').write_text(json.dumps({'schema_version': 1, 'slug': 'fixture-brand', 'brand_name': 'Fiktive Testmarke', 'source_url': 'https://example.com', 'created_at': '2026-10-13', 'approval': {'status': 'approved', 'scope': 'global'}, 'files': {}}))
    refresh(root)


def refresh(root):
    m = installer.read_manifest(root)
    m['files'] = {k: v for k, v in installer.inventory(root).items() if k != 'manifest.json'}
    (root / 'manifest.json').write_text(json.dumps(m))


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.kit = self.base / 'kit'
        fixture(self.kit)
        self.home = self.base / 'home'
        self.home.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, ok=True):
        r = subprocess.run(['python3', str(SCRIPT), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(r.returncode == 0, ok, r.stdout + r.stderr)
        return r

    def install(self, *args, ok=True):
        return self.run_cli('kit', '--source', self.kit, '--home', self.home, '--scope', 'global', *args, ok=ok)

    def test_full_package_and_idempotence(self):
        rules = self.home / '.claude/CLAUDE.md'
        rules.parent.mkdir()
        rules.write_text('Eigene vorhandene Regeln.\n')
        self.install('--approved')
        dest = self.home / '.claude/brands/fixture-brand'
        self.assertEqual(installer.inventory(dest), installer.inventory(self.kit))
        personal = self.home / '.claude/skills/fixture-brand-brand/SKILL.md'
        self.assertTrue(personal.is_file())
        self.assertIn('../../brands/fixture-brand/brand.md', personal.read_text())
        self.assertIn('/fixture-brand-brand', rules.read_text())
        before = rules.read_bytes()
        stamps = {p: p.stat().st_mtime_ns for p in [rules, personal, *dest.rglob('*')]}
        self.install('--approved')
        self.assertEqual(rules.read_bytes(), before)
        self.assertTrue(before.startswith(b'Eigene vorhandene Regeln.\n'))
        self.assertEqual(stamps, {p: p.stat().st_mtime_ns for p in stamps})

    def test_refuse_existing_changed_brand_without_rule_mutation(self):
        self.install('--approved')
        rules = self.home / '.claude/CLAUDE.md'
        old = rules.read_bytes()
        (self.kit / 'brand.md').write_text('Verändert')
        refresh(self.kit)
        self.install('--approved', ok=False)
        self.assertEqual(old, rules.read_bytes())

    def test_unapproved_and_wrong_scope(self):
        self.install(ok=False)
        m = installer.read_manifest(self.kit)
        m['approval']['scope'] = 'project'
        (self.kit / 'manifest.json').write_text(json.dumps(m))
        self.install('--approved', ok=False)
        self.assertFalse((self.home / '.claude').exists())

    def test_project_integration(self):
        project = self.base / 'project'
        project.mkdir()
        m = installer.read_manifest(self.kit)
        m['approval'] = {'status': 'approved', 'scope': 'project', 'project': str(project.resolve())}
        (self.kit / 'manifest.json').write_text(json.dumps(m))
        args = ['kit', '--source', self.kit, '--scope', 'project', '--project', project, '--approved']
        self.run_cli(*args)
        self.run_cli(*args)
        self.assertEqual((project / 'CLAUDE.md').read_text().count(':begin -->'), 1)
        self.assertTrue((project / '.claude/brands/fixture-brand/components/components.css').is_file())
        self.assertFalse((self.home / '.claude').exists())
        self.assertTrue((project / '.claude/skills/fixture-brand-brand/SKILL.md').is_file())

    def test_personal_skill_conflict_preserves_all_existing_files(self):
        skill = self.home / '.claude/skills/fixture-brand-brand/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('Existing personal skill')
        self.install('--approved', ok=False)
        self.assertEqual(skill.read_text(), 'Existing personal skill')
        self.assertFalse((self.home / '.claude/brands').exists())
        self.assertFalse((self.home / '.claude/CLAUDE.md').exists())

    def test_missing_modified_extra_files(self):
        (self.kit / 'tokens/tokens.css').unlink()
        self.run_cli('validate', '--source', self.kit, ok=False)
        (self.kit / 'tokens/tokens.css').write_text('changed')
        self.run_cli('validate', '--source', self.kit, ok=False)
        refresh(self.kit)
        (self.kit / 'extra.txt').write_text('extra')
        self.run_cli('validate', '--source', self.kit, ok=False)

    def test_links_and_active_content(self):
        for value in ['url(../fonts/missing.woff2)', 'url(https://example.com/font.woff2)', 'url(../../../escape.txt)']:
            (self.kit / 'tokens/fonts.css').write_text(value)
            refresh(self.kit)
            self.run_cli('validate', '--source', self.kit, ok=False)
        (self.kit / 'tokens/fonts.css').write_text('/* system fallback */')
        (self.kit / 'assets/logo.svg').write_text('<svg onload="bad()"></svg>')
        refresh(self.kit)
        self.run_cli('validate', '--source', self.kit, ok=False)

    def test_symlink_and_secret_file(self):
        (self.kit / 'link.txt').symlink_to(self.kit / 'brand.md')
        self.run_cli('validate', '--source', self.kit, ok=False)
        (self.kit / 'link.txt').unlink()
        (self.kit / '.env').write_text('TEST_ONLY=not-a-secret')
        self.run_cli('manifest', '--source', self.kit, ok=False)

    def test_conflicting_block(self):
        self.install('--approved')
        rules = self.home / '.claude/CLAUDE.md'
        rules.write_text(rules.read_text().replace('Für Branding-Arbeit', 'Changed'))
        old = rules.read_bytes()
        self.install('--approved', ok=False)
        self.assertEqual(old, rules.read_bytes())

    def test_skill_install_idempotence_and_conflict(self):
        args = ['skill', '--source', ROOT, '--home', self.home]
        self.run_cli(*args)
        self.run_cli(*args)
        dest = self.home / '.claude/skills/brand-setup'
        self.assertTrue((dest / 'scripts/install.py').is_file())
        self.assertFalse((dest / 'tests').exists())
        (dest / 'SKILL.md').write_text('Local customization')
        self.run_cli(*args, ok=False)
        self.assertEqual((dest / 'SKILL.md').read_text(), 'Local customization')


if __name__ == '__main__':
    unittest.main(verbosity=2)
