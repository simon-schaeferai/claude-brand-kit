# Einrichtung

## Voraussetzungen

- Claude Code installiert und angemeldet. Folge der [offiziellen Installation](https://code.claude.com/docs/en/setup) und starte einmal `claude` zum Anmelden. Dieses Repo installiert Claude Code nicht automatisch.
- Git, curl und Python 3.10 oder neuer im PATH. Keine Python-Pakete erforderlich.
- macOS/Linux mit Bash, auf Windows WSL. Native PowerShell wird vom Bootstrap nicht unterstützt.

Der Startbefehl in der README installiert nur diesen Skill unter `~/.claude/skills/brand-setup`. Er ändert noch keine Markenregeln. Bei einem bestehenden abweichenden Skill stoppt er. Vor einem Update lokale Änderungen sichern und den Unterschied prüfen; kein automatisches Force-Update.

## Ohne Remote-Skript-Ausführung

```bash
git clone https://github.com/simon-schaeferai/claude-brand-kit.git
python3 claude-brand-kit/scripts/install.py skill --source claude-brand-kit
claude
```

In Claude Code: `/brand-setup https://deine-website.de`.

Alternativ nur in einem Projekt: klone dieses Repo in dessen noch nicht vorhandenes `.claude/skills/brand-setup/` und starte dort Claude Code. Der Markenpaket-Installer bietet unabhängig davon global oder projektspezifisch an.

## Nach der Abnahme

Ein neues Gespräch lädt den ergänzten CLAUDE.md-Block. Nutze beispielsweise: „Erstelle eine kleine Beispielseite für meine Marke mit dem installierten Markenpaket.“ Kundenmarken behalten ihre eigenen Vorgaben.

Zur Entfernung: den markierten `brand-setup:<slug>`-Block aus der jeweiligen CLAUDE.md entfernen und das entsprechende Markenpaket löschen, nachdem benötigte Dateien gesichert sind. Andere Regeln nicht entfernen. Den Skill separat unter `~/.claude/skills/brand-setup` entfernen.

Es werden keine Website-Änderungen veröffentlicht, keine Zugangsdaten gespeichert und keine Nutzerdaten an dieses GitHub-Repo übertragen. Website-Abfragen und Claude-Code-Nutzung unterliegen den normalen Werkzeugen und Einstellungen deiner Claude-Sitzung.
