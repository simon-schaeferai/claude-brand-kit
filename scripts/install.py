#!/usr/bin/env python3
"""Lokale Installation und Integritätsprüfung. Keine Netzwerke oder LLM-Aufrufe."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit, unquote

REQUIRED = {'brand.md', 'rules/brand-guide.md', 'rules/preferences.md',
            'tokens/tokens.css', 'tokens/fonts.css', 'components/components.css',
            'fonts/README.md', 'assets/README.md', 'preview/index.html',
            'evidence.json', 'approval.md'}
EXTENSIONS = {'.md', '.json', '.css', '.html', '.png', '.jpg', '.jpeg', '.webp',
              '.ico', '.svg', '.woff', '.woff2', '.ttf', '.otf', '.txt'}


def fail(message):
    raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root, restricted=True):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            fail(f'Symlink nicht erlaubt: {p}')
        if not p.is_file():
            continue
        name = p.relative_to(root).as_posix()
        if restricted and (any(x.startswith('.') for x in p.relative_to(root).parts)
                           or p.suffix.lower() not in EXTENSIONS):
            fail(f'Dateityp/Pfad nicht erlaubt: {name}')
        if p.stat().st_size > 20 * 1024 * 1024:
            fail(f'Datei zu groß: {name}')
        result[name] = digest(p)
    return result


def read_manifest(root):
    return json.loads((root / 'manifest.json').read_text(encoding='utf-8'))


def local_reference(root, file, url):
    url = unquote(url.strip())
    if not url or url.startswith('#') or url.startswith('data:'):
        return
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or url.startswith('/') or '\\' in url:
        fail(f'Keine externe/absolute Ressource: {file.relative_to(root)}: {url}')
    target = (file.parent / parsed.path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        fail(f'Fehlender/ausbrechender Verweis: {file.relative_to(root)}: {url}')


def validate(source):
    root = source.resolve()
    if source.is_symlink():
        fail('Paketwurzel darf kein Symlink sein')
    files = inventory(root)
    if not REQUIRED <= files.keys():
        fail('Pflichtdateien fehlen: ' + ', '.join(sorted(REQUIRED - files.keys())))
    m = read_manifest(root)
    if m.get('schema_version') != 1 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', m.get('slug', '')):
        fail('Schema/Slug ungültig')
    if len(m['slug']) > 58 or not m.get('brand_name') or not m.get('created_at'):
        fail('Metadaten unvollständig')
    if any(c in m['brand_name'] for c in '\r\n<>') or len(m['brand_name']) > 200:
        fail('Markenname enthält unzulässige Zeichen')
    if urlsplit(m.get('source_url', '')).scheme not in {'https', 'http'}:
        fail('source_url muss HTTP(S) sein')
    if m.get('files') != {k: v for k, v in files.items() if k != 'manifest.json'}:
        fail('Manifest stimmt nicht mit vollständigem Dateibestand überein')
    evidence = json.loads((root / 'evidence.json').read_text(encoding='utf-8'))
    if not isinstance(evidence, list) or not evidence:
        fail('Evidenzliste fehlt')
    ids = {e.get('id') for e in evidence}
    if len(ids) != len(evidence) or None in ids:
        fail('Evidenz-IDs fehlen oder sind doppelt')
    for e in evidence:
        if e.get('status') not in {'observed', 'derived', 'unverified'} or not e.get('reason'):
            fail('Evidenz braucht Status und Begründung')
        if e['status'] == 'observed' and not (e.get('source_url') and e.get('selector')):
            fail('Beobachtete Evidenz braucht URL und Selektor/Element')
        if e['status'] == 'derived' and (not e.get('based_on') or not set(e['based_on']) <= ids):
            fail('Abgeleitete Evidenz braucht gültige based_on-IDs')
    for name in files:
        file = root / name
        if file.suffix == '.md':
            for ref in re.findall(r'\[[^\]]*\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
                if not urlsplit(ref).scheme:
                    local_reference(root, file, ref)
        if file.suffix in {'.css', '.html', '.svg'}:
            body = file.read_text(encoding='utf-8')
            if re.search(r'<\s*script\b|\bon\w+\s*=|javascript:', body, re.I):
                fail(f'Aktiver Inhalt nicht erlaubt: {name}')
            refs = re.findall(r'url\(\s*[\"\']?([^\)\"\']+)\s*[\"\']?\s*\)', body, re.I)
            refs += re.findall(r'(?:src|href)\s*=\s*[\"\']([^\"\']+)', body, re.I)
            refs += re.findall(r'@import\s+[\"\']([^\"\']+)', body, re.I)
            for ref in refs:
                local_reference(root, file, ref)
    return m


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.brand-setup-')
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
        os.replace(temp, path)
    finally:
        if Path(temp).exists():
            Path(temp).unlink()


def install_skill(source, home):
    dest = home / '.claude/skills/brand-setup'
    # Nur veröffentlichte Skill-Dateien installieren, keine Git-History oder Tests.
    selected = [source / 'SKILL.md', source / 'scripts/install.py', *sorted((source / 'references').glob('*.md'))]
    if any(not p.is_file() or p.is_symlink() for p in selected):
        fail('Skill-Dateien fehlen oder sind Symlinks')
    expected = {p.relative_to(source).as_posix(): digest(p) for p in selected}
    if any(p.is_symlink() for p in [dest, dest.parent, dest.parent.parent]):
        fail('Bestehender Skill-/Konfigurations-Symlink wird nicht ersetzt')
    if dest.exists():
        if inventory(dest, restricted=False) == expected:
            print(f'Skill bereits identisch installiert: {dest}')
            return
        fail(f'Bestehender Skill bleibt unverändert: {dest}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(dir=dest.parent, prefix='.brand-setup-'))
    try:
        for p in selected:
            target = stage / p.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
        stage.rename(dest)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print(f'Skill installiert: {dest}')


def install_kit(args):
    m = validate(args.source)
    approval = m.get('approval', {})
    if not args.approved or approval.get('status') != 'approved' or approval.get('scope') != args.scope:
        fail('Konkrete Abnahme und passender Scope erforderlich')
    if args.scope == 'project':
        if not args.project or not args.project.is_dir():
            fail('Existierender Projektpfad erforderlich')
        base = args.project.resolve() / '.claude'
        rules = args.project.resolve() / 'CLAUDE.md'
        if approval.get('project') != str(args.project.resolve()):
            fail('Projektpfad weicht von der Abnahme ab')
    else:
        if args.project:
            fail('--project ist nur für scope project erlaubt')
        base = args.home.resolve() / '.claude'
        rules = base / 'CLAUDE.md'
    dest = base / 'brands' / m['slug']
    skill_name = m['slug'] + '-brand'
    skill_dest = base / 'skills' / skill_name
    relative_pack = Path(os.path.relpath(dest, skill_dest)).as_posix()
    description = json.dumps(f'Verwendet das freigegebene Markenpaket von {m["brand_name"]} für Gestaltung und Visual-Arbeit mit dieser Absendermarke.', ensure_ascii=False)
    skill = (f'---\nname: {skill_name}\ndescription: {description}\n---\n\n'
             f'# {m["brand_name"]}\n\n'
             'Vor Gestaltung zuerst den Absender bestimmen. Für diese Marke zuerst '
             f'[{m["brand_name"]}: Markenpaket]({relative_pack}/brand.md), '
             f'[Markenregeln]({relative_pack}/rules/brand-guide.md) und '
             f'[Vorlieben]({relative_pack}/rules/preferences.md) lesen. '
             'Alle Verweise relativ zu diesem SKILL.md auflösen.\n\n'
             f'Für HTML {relative_pack}/tokens/fonts.css, {relative_pack}/tokens/tokens.css '
             f'und {relative_pack}/components/components.css gemeinsam einbinden. '
             f'Fonts aus {relative_pack}/fonts/ und Logo/Assets aus {relative_pack}/assets/ '
             'mit korrekten lokalen Verweisen und ihren Lizenzhinweisen verwenden. '
             'Bei einzelnen Artefakten einbetten oder gemeinsam ausliefern.\n\n'
             'Andere Absendermarken behalten ihre eigenen Vorgaben. Keine Preise, '
             'Versprechen oder Kundenstimmen aus der Quellwebsite übernehmen. '
             'Bei Konflikten nachfragen. Änderungen am Markenpaket erst nach '
             'konkreter Abnahme. Die Quellwebsite nicht automatisch umbauen.\n')
    # Keine indirekten Writes durch vorhandene Symlinks.
    for p in [base, base.parent, dest.parent, dest, rules, skill_dest.parent, skill_dest]:
        if p.is_symlink():
            fail(f'Symlink-Ziel wird nicht verändert: {p}')
    begin = f'<!-- brand-setup:{m["slug"]}:begin -->'
    end = f'<!-- brand-setup:{m["slug"]}:end -->'
    block = (f'{begin}\n'
             f'Für Branding-Arbeit zuerst den Absender bestimmen. Für {m["brand_name"]} '
             f'vor Visual-Arbeit den persönlichen Skill /{skill_name} laden '
             f'({skill_dest / "SKILL.md"}) und das Markenpaket unter '
             f'{dest / "brand.md"} lesen. Dessen Regeln, '
             'Tokens, Fonts, Assets und Komponenten verwenden. Für andere Marken deren '
             'eigene Vorgaben verwenden. Bei mehreren passenden Marken oder Konflikten '
             'nachfragen. Die Quellwebsite nicht automatisch umbauen.\n'
             f'{end}')
    old = rules.read_text(encoding='utf-8') if rules.exists() else ''
    if begin in old or end in old:
        if old.count(begin) != 1 or old.count(end) != 1 or block not in old:
            fail('Bestehender Regelblock weicht ab; keine automatische Änderung')
        new = old
    else:
        new = old + ('\n\n' if old else '') + block + '\n'
    if skill_dest.exists():
        if inventory(skill_dest, restricted=False) != {'SKILL.md': hashlib.sha256(skill.encode('utf-8')).hexdigest()}:
            fail(f'Bestehender persönlicher Skill bleibt unverändert: {skill_dest}')
    if dest.exists():
        if inventory(dest) != inventory(args.source.resolve()):
            fail(f'Bestehendes Markenpaket bleibt unverändert: {dest}')
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(dir=dest.parent, prefix='.brand-kit-'))
        try:
            shutil.copytree(args.source, stage, dirs_exist_ok=True)
            validate(stage)
            stage.rename(dest)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    if not skill_dest.exists():
        skill_dest.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(dir=skill_dest.parent, prefix='.brand-skill-'))
        try:
            (stage / 'SKILL.md').write_text(skill, encoding='utf-8')
            stage.rename(skill_dest)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    if new != old:
        atomic_write(rules, new.encode('utf-8'))
    print(f'Markenpaket geprüft und installiert: {dest}\nPersönlicher Skill: /{skill_name} ({skill_dest})\nRegeln: {rules}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    for command in ['skill', 'manifest', 'validate', 'kit']:
        c = sub.add_parser(command)
        c.add_argument('--source', type=Path, required=True)
        if command in {'skill', 'kit'}:
            c.add_argument('--home', type=Path, default=Path.home(), help='Alternatives Home (Tests)')
        if command == 'kit':
            c.add_argument('--scope', choices=['global', 'project'], required=True)
            c.add_argument('--project', type=Path)
            c.add_argument('--approved', action='store_true')
    args = p.parse_args()
    try:
        if args.command == 'skill':
            install_skill(args.source.resolve(), args.home.resolve())
        elif args.command == 'manifest':
            m = read_manifest(args.source)
            files = inventory(args.source.resolve())
            m['files'] = {k: v for k, v in files.items() if k != 'manifest.json'}
            atomic_write(args.source / 'manifest.json', (json.dumps(m, ensure_ascii=False, indent=2) + '\n').encode())
            print('Dateiliste und SHA-256 aktualisiert')
        elif args.command == 'validate':
            m = validate(args.source)
            print(f'Paket gültig: {m["slug"]} ({len(m["files"])} Dateien)')
        else:
            install_kit(args)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        p.exit(1, f'STOP: {exc}\n')


if __name__ == '__main__':
    main()
