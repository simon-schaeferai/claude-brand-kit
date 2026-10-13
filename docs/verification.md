# Prüfumfang

Stand: 13. Oktober 2026.

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/bootstrap.sh
```

10 Tests bestanden. Die Tests laufen ausschließlich in temporären Verzeichnissen:

- Vollständiges Paket einschließlich Komponenten, Fonts-/Asset-Verzeichnissen, Vorschau und Evidenz kopiert. SHA-256-Dateiliste geprüft.
- Globale und projektbezogene Einbindung. Bestehende Regeltexte bleiben byte-identisch erhalten; wiederholte Installation ändert weder Inhalt noch Dateizeitpunkte.
- Abweichende vorhandene Pakete, Skill-Dateien und Regelblöcke werden abgelehnt. Fehlende Abnahme und falscher Scope ebenfalls.
- Fehlende, veränderte oder zusätzliche Dateien erkannt. Defekte/externe CSS-/HTML-Verweise, aktive SVG-Inhalte, Symlinks und `.env` abgelehnt.
- Bootstrap-Skript mit echter lokaler Skill-Installation, simulierter Git-Kopie und simuliertem Claude-Prozess zweimal durchlaufen. Website-Argument und Arbeitsordner geprüft, URLs mit Zugangsdaten abgelehnt. Es wird vor der Markenabnahme keine CLAUDE.md angelegt.

Das README-Bild zeigt den echten Testlauf und den tatsächlichen Dateibestand einer ausdrücklich fiktiven Testmarke. Die Test-Fixture prüft Dateimechanik, keine Designqualität.

Nicht als getestet behauptet: vollständige Website-Extraktion durch einen live gestarteten Claude-Agenten, Freundes-Website, lizenzierte Schriftbeschaffung, jedes Betriebssystem oder jede Website. Die Bootstrap-Eingabe über ein echtes interaktives Terminal erfordert den Nutzer. Markenqualität und verfügbare Browser-Werkzeuge bleiben Teil der späteren Abnahme.

Der Installer ist ein Integritätsprüfer, kein vollständiger Malware-/Secret-Scanner. Der Agent muss Inhalte und Nutzungsrechte vor der Installation prüfen. Idempotenz bedeutet: identischer Bestand wird bewahrt; Versionsupdates werden bewusst separat behandelt. Gleichzeitige Installationen sind nicht vorgesehen.

## Offizielle Grundlagen

Am 13. Oktober 2026 geprüft:

- [Claude-Code-Skills](https://code.claude.com/docs/en/skills): persönliche Skills unter `~/.claude/skills/`, Projekt-Skills unter `.claude/skills/`, Aufruf über `/skill-name`.
- [Claude-Code-Memory](https://code.claude.com/docs/en/memory): persönliche Anweisungen in `~/.claude/CLAUDE.md`, Projekt-Anweisungen in `CLAUDE.md`.
- [Claude-Code-Setup](https://code.claude.com/docs/en/setup): Installation und Anmeldung bleiben bei Claude Code; keine alten DesignSync- oder Design-Login-Befehle erforderlich.

`BRAND_SETUP_HOME` erlaubt einen isolierten Installationspfad für Bootstrap-Tests. Für normale Nutzung nicht setzen; Claude selbst lädt seine persönlichen Skills aus seinem normalen Home.
