# Release schneiden

Füllhorn wird vollständig über GitHub Actions veröffentlicht: [.github/workflows/release.yaml](.github/workflows/release.yaml).
Es gibt keine Datei, in der eine Versionsnummer gepflegt wird – `hatch-vcs` leitet die Version aus dem Git-Tag ab.

| Auslöser | Was passiert |
|---|---|
| **GitHub-Release veröffentlicht** (Tag `vX.Y.Z…`) | Voller Release: PyPI, Container-Images auf ghcr.io, Helm-Chart |
| **Push auf `main`** | QA, Tests, Paket bauen, Veröffentlichung auf Test-PyPI (test.pypi.org) – keine Images, kein Chart |
| **Manueller Start** (`gh workflow run release.yaml`) | Wie ein Push auf `main` (Probelauf) |

Ein Release entsteht also **nicht** durch einen Tag allein und **nicht** durch einen Merge, sondern erst, wenn das
GitHub-Release veröffentlicht wird.

## Vorbedingungen

- Der letzte Release-Lauf auf `main` ist grün (`gh run list --workflow release.yaml --branch main --limit 1`).
  Der Lauf enthält die komplette Testsuite inklusive E2E-Tests und der Coverage-Schwelle.
- `uv.lock` ist committet und aktuell: Der Smoke-Test vergleicht die im Image installierten Versionen mit der
  Lock-Datei und bricht bei Abweichung ab.
- `gh auth status` ist in Ordnung, und das Konto darf Releases erstellen.
- PyPI und Test-PyPI laufen über Trusted Publishing (OIDC) in den GitHub-Environments `pypi` und `testpypi`;
  im Repository liegen keine Upload-Tokens.

## Versions- und Tag-Regeln

Der Tag ist die Version. Erlaubt sind genau diese Formen (ohne führendes `v` in der Python-Version):

| Tag | Python-Version | Chart-Version | `latest`-Tag am Image |
|---|---|---|---|
| `v1.2.3` | `1.2.3` | `1.2.3` | ja |
| `v1.2.3a4` | `1.2.3a4` | `1.2.3-alpha.4` | nein |
| `v1.2.3b4` | `1.2.3b4` | `1.2.3-beta.4` | nein |
| `v1.2.3rc4` | `1.2.3rc4` | `1.2.3-rc.4` | nein |

Alles andere, insbesondere `.devN` und `.postN`, lässt sich nicht eindeutig nach SemVer übersetzen; der Job
`helm-publish` bricht dann mit einer Fehlermeldung ab – nachdem Paket und Image schon veröffentlicht sind.
Deshalb vor dem Veröffentlichen die Tag-Form prüfen.

`appVersion` des Charts ist die Python-Version, und `image.tag` ist im Chart leer. Chart und Image passen damit
immer zusammen, ohne dass man etwas pflegen muss. [charts/fuellhorn/Chart.yaml](charts/fuellhorn/Chart.yaml) wird
im Workflow gesetzt und nicht im Repository geändert.

## Ablauf

1. Stand prüfen: `main` ist aktuell, der letzte Lauf grün, keine offenen Migrations- oder Chart-Änderungen, die
   noch in den Release sollen.
2. Nächste Version wählen. Vorabversionen (`aN`) sind der Normalfall, solange `1.0.0` nicht steht.
3. Release veröffentlichen – der Befehl legt den Tag auf dem aktuellen `main`-Stand an:

   ```bash
   gh release create v1.0.0a10 --prerelease --generate-notes --target main
   ```

   Für ein stabiles Release ohne `--prerelease`; nur dann bekommt das Image `latest`.
   Mit `--notes-file notes.md` lassen sich eigene Release-Notes mitgeben (siehe „Nacharbeiten“).
4. Lauf beobachten:

   ```bash
   gh run list --workflow release.yaml --limit 1
   gh run watch <run-id>
   ```

5. Ergebnis prüfen: PyPI-Version vorhanden, Image ziehbar, Chart-Version abrufbar.

   ```bash
   docker pull ghcr.io/jensens/fuellhorn:1.0.0a10
   helm show chart oci://ghcr.io/jensens/fuellhorn --version 1.0.0-alpha.10
   ```

## Was der Workflow tut

Die Jobs hängen voneinander ab; jeder Schritt läuft erst, wenn der vorige erfolgreich war.

1. **QA und Tests** – Ruff, `ty`, Unit-, Service-, UI-, Migrations- und E2E-Tests samt Coverage-Schwelle.
2. **Build** – `uv build` erzeugt sdist und Wheel; die Version kommt aus dem Tag.
3. **PyPI** – Veröffentlichung des Pakets. Dieser Schritt kommt zuerst, weil das Container-Image das Paket aus
   PyPI installiert; der folgende Job wartet bis zu fünf Minuten, bis die Version dort abrufbar ist.
4. **Images je Plattform** – `linux/amd64` und `linux/arm64` werden getrennt gebaut und unter dem Zwischen-Tag
   `<version>-linux-amd64` bzw. `-linux-arm64` abgelegt. Jedes Image durchläuft einen Smoke-Test: installierte
   Versionen gegen `uv.lock`, Migration und Anlegen des Admin-Benutzers mit SQLite, Start und `/api/health`.
5. **Multi-Arch-Manifest** – erst jetzt entstehen die Tags, die Nutzer verwenden: `<version>`, `<major>.<minor>`
   und bei stabilen Releases `latest`.
6. **Helm-Chart** – Chart-Version und `appVersion` werden gesetzt, das Chart als OCI-Artefakt nach
   `ghcr.io/jensens` geschoben. Das Chart erscheint bewusst zuletzt, damit es nie auf ein Image zeigt, das
   es nicht gibt.

## Wenn etwas scheitert

- **QA, Tests oder Build rot:** Es wurde nichts veröffentlicht. Fehler auf `main` beheben, Release und Tag löschen
  (`gh release delete v1.0.0a10 --cleanup-tag`) und mit derselben Versionsnummer neu veröffentlichen.
- **Smoke-Test eines Images rot:** Paket ist auf PyPI, aber es gibt kein Multi-Arch-Manifest und kein Chart. Nur
  die Zwischen-Tags `<version>-linux-*` existieren; die Version ist für Nutzer also nicht verwendbar.
- **Nach erfolgreichem PyPI-Upload:** Ein erneuter Lauf derselben Version scheitert, weil PyPI keine zweite
  Veröffentlichung derselben Datei annimmt. Dann die **nächste** Versionsnummer verwenden statt den Lauf zu
  wiederholen. (Nur Test-PyPI überspringt bereits vorhandene Dateien.)
- **Einzelne Jobs wiederholen** (z.B. nach einem Netzwerkfehler beim Push): `gh run rerun <run-id> --failed`.

## Nacharbeiten

Der Workflow erzeugt keine inhaltlichen Release-Notes. Was Betreiber beim Update wissen müssen, gehört in die
Notes des Releases:

- **Neue Migrationen:** Sie laufen automatisch, wenn der Container startet (steuerbar über
  `FUELLHORN_SKIP_MIGRATIONS`, siehe [docs/deployment/docker.md](docs/deployment/docker.md)). Im Helm-Chart
  übernimmt das der Init-Container bzw. der Migrations-Job.
- **Neue Seed-Daten:** Kommen Kategorien oder Haltbarkeiten dazu, legt die Migration sie nicht an. Einmal
  `fuellhorn seed shelf-life-defaults` ausführen; Quelle der Daten ist [app/seed.py](app/seed.py).
- **Geänderte Chart-Defaults:** neue oder umbenannte Werte in `values.yaml` nennen, damit bestehende
  Wertedateien angepasst werden können.
- **Abmeldungen:** Änderungen an der Sitzungsverwaltung oder ein neues `FUELLHORN_SECRET` melden alle Nutzer ab.
  Das gehört in die Notes, sonst wirkt es wie ein Fehler.

## Lokal prüfen, ohne zu veröffentlichen

```bash
# Paket bauen wie im Workflow
uv build

# Image aus dem veröffentlichten Paket bauen (ohne Argument die neueste Version)
docker build --build-arg FUELLHORN_VERSION=1.0.0a9 -t fuellhorn:test .

# Chart rendern und testen
helm lint charts/fuellhorn
helm unittest charts/fuellhorn
```
