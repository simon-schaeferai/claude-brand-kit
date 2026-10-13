# Markenpaket-Vertrag

Pflichtdateien (alle UTF-8):

- `brand.md`: Einstieg mit relativen Links auf Regeln, Tokens, Komponenten, Fonts, Assets und Vorschau; erklärt Absenderwahl und Einbindung aller drei CSS-Dateien.
- `rules/brand-guide.md`: Positionierung, Markencharakter, Layout, Typografie, Farbe, Bildwelt, Komponenten, Bewegung; Evidenz-IDs und offene Punkte.
- `rules/preferences.md`: bestätigte Vorlieben, Do/Don't und Änderungspolitik; nicht mit erfundenem Geschmack füllen.
- `tokens/tokens.css`: semantische CSS-Variablen mit Evidenz-IDs. Kein fremdes Brand-Präfix.
- `tokens/fonts.css`: lokale `@font-face` (URLs relativ zu dieser Datei) oder deklarierte System-Fallbacks. Keine versteckten Remote-Abhängigkeiten.
- `components/components.css`: echte wiederverwendbare Klassen, responsive und zugänglich, dieselben Klassen in der Vorschau.
- `fonts/README.md`: Familie, Gewichte, Herkunft, Lizenzstatus, lokale Dateinamen oder bewusste Fallbacks; Lizenzen neben erlaubten lokalen Fonts ablegen.
- `assets/README.md`: Logo-/Asset-Dateinamen, Quellen, Nutzungsrechte und Einschränkungen. Wenn kein Logo verfügbar: ausdrücklich fehlend, niemals erfinden.
- `preview/index.html`: offline nutzbare Vorschau, nur relative lokale Verweise, keine Scripts oder remote Requests. Fehlende Dateien nicht referenzieren.
- `evidence.json`: Liste der belegten/abgeleiteten/ungeprüften Entscheidungen (siehe extraction.md).
- `approval.md`: Abnahmebericht mit offenen Punkten; vor Go ausdrücklich „Entwurf“.
- `manifest.json`: Metadaten und vollständige SHA-256-Dateiliste, ohne das Manifest selbst.

Beispiel für das Manifest (Dateiliste durch den Befehl unten erzeugen, nicht manuell raten):

```json
{
  "schema_version": 1,
  "slug": "example-brand-v1",
  "brand_name": "Example",
  "source_url": "https://example.com",
  "created_at": "2026-10-13T12:00:00Z",
  "approval": {"status": "draft"},
  "files": {}
}
```

```bash
python3 <skill-dir>/scripts/install.py manifest --source <kit>
python3 <skill-dir>/scripts/install.py validate --source <kit>
```

Das Manifest-Kommando aktualisiert nur die Hash-Liste des bewusst neuen Arbeitsentwurfs. Nach jeder Inhaltsänderung erneut ausführen. Erlaubte Dateitypen: Markdown, JSON, CSS, HTML, PNG/JPG/WebP/ICO, bereinigtes SVG, WOFF/WOFF2/TTF/OTF und TXT-Lizenzen. Keine Symlinks, Skripte, Sessions, `.env`, privaten Notizen, Roh-Dumps oder vollständigen HTML/CSS-Kopien von Quellseiten im Paket.

Zur Nutzung in einem neuen Artefakt alle Paketbestandteile bewahren. Beispiel: `tokens/fonts.css`, `tokens/tokens.css`, `components/components.css` einbinden, ihre relativen Font-/Bildpfade erhalten. Für einzelne HTML-Artefakte CSS und lizenzierte Assets inline einbetten oder gemeinsam ausliefern. Nicht bloß Farben abschreiben und Komponenten neu erfinden. Vorschau nicht auf Karten verweisen lassen, die gar nicht installiert werden.
