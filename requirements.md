# Fuellhorn Application

## Übersicht
Anwendung zur Erfassung und Verwaltung von Lebensmittelvorräten. Unterstützt werden gekaufte Produkte sowie selbst eingemachte und eingefrorene Lebensmittel (gekauft, gekauft und eingefroren, gekocht oder aus dem Garten eingefroren).

## Projektziele & Zielgruppe

### Primäres Ziel
Verwaltung des Lebensmittelvorrats für eine Familie (eigener Haushalt).

### Mittelfristig
Bereitstellung als selbst-hostbare Open-Source-Lösung für andere Familien.

### Langfristig (optional)
Möglichkeit eines SaaS-Angebots. Kommerzieller Aspekt hat keine Priorität.

## Akteure & Rollen

### Administrator
- Verwaltet Benutzerkonten
- Kann alle Funktionen nutzen
- Verantwortlich für System-Einstellungen

### Befüller (Normaler Benutzer)
- Erfasst neue Artikel im Vorrat
- Entnimmt Artikel aus dem Vorrat
- Sucht und filtert in der Übersicht
- Sieht Ablaufwarnungen

## Use Cases / Hauptszenarien

### UC1: Einkauf erfassen
**Akteur:** Befüller
**Vorbedingung:** Benutzer kommt vom Einkaufen mit mehreren Artikeln
**Ziel:** Schnelle Erfassung von 5-20 Artikeln
**Ablauf:**
1. Benutzer startet Erfassungs-Wizard
2. Für jeden Artikel:
   - Barcode scannen (falls vorhanden) → Produktdaten werden automatisch geladen
   - ODER manuell Produktname eingeben
   - Menge und Einheit erfassen (kann mehrfach sein, z.B. "6 Flaschen à 0,5l")
   - MHD erfassen (scannen oder manuell)
   - Lagerort auswählen
   - Optional: Kategorien zuordnen
3. Artikel werden im Vorrat gespeichert
**Erfolgskriterium:** Max. 3 Schritte pro Artikel, Erfassung dauert < 30 Sekunden pro Artikel

### UC2: Gekaufte Artikel einfrieren
**Akteur:** Befüller
**Vorbedingung:** Benutzer hat Lebensmittel gekauft und möchte sie einfrieren (z.B. frisches Fleisch)
**Ziel:** Erfassung von gekauften, dann eingefrorenen Artikeln
**Ablauf:**
1. Benutzer startet Erfassung
2. Barcode scannen ODER Produktname manuell eingeben
3. Artikel-Typ auswählen: "Gekauft und eingefroren"
4. MHD des Originalprodukts erfassen (optional, wird ignoriert für Haltbarkeitsberechnung)
5. **Einfrierdatum** erfassen (meist = heute)
6. Menge und Einheit
7. Lagerort = Gefriertruhe/Gefrierschrank
8. System berechnet automatisch: Haltbarkeit = Einfrierdatum + Gefrierzeit (je nach Kategorie)
**Besonderheit:** Ursprüngliches MHD wird hinfällig, neue Haltbarkeit basiert auf Einfrierdatum

### UC3: Gartenprodukte einfrieren
**Akteur:** Befüller
**Vorbedingung:** Benutzer hat Gemüse/Obst aus dem Garten geerntet
**Ziel:** Erfassung von selbst eingefrorenen Gartenprodukten
**Ablauf:**
1. Benutzer startet Erfassung
2. Produktname eingeben (z.B. "Tomaten aus Garten")
3. Artikel-Typ: "Selbst hergestellt (gefroren)"
4. Produktionsdatum = Erntedatum erfassen
5. Menge und Einheit (z.B. "500g")
6. Lagerort = Tiefkühltruhe
7. Optional: Notiz (z.B. "blanchiert")
8. System berechnet: Haltbarkeit = Erntedatum + Gefrierzeit
**Besonderheit:** Kein MHD, sondern Produktionsdatum + Gefrierzeiten relevant

### UC4: Vorgekochtes einfrieren/einmachen
**Akteur:** Befüller
**Vorbedingung:** Benutzer hat auf Vorrat gekocht
**Ziel:** Erfassung von selbst gekochten/eingemachten Produkten
**Ablauf:**
1. Produktname (z.B. "Bolognese-Sauce")
2. Artikel-Typ: "Selbst hergestellt (gefroren)" oder "Selbst hergestellt (eingemacht)"
3. Produktionsdatum erfassen (= Kochdatum)
4. Menge und Einheit
5. Lagerort (Tiefkühltruhe oder Keller bei Eingemachtem)
6. Optional: Zutaten/Rezept-Referenz
7. System berechnet Haltbarkeit basierend auf Produktionsdatum + konfigurierter Haltbarkeit
**Besonderheit:** Schwierig, Haltbarkeit zu bestimmen

### UC6: Artikel entnehmen
**Akteur:** Befüller
**Vorbedingung:** Benutzer kocht und benötigt Zutaten
**Ziel:** Schnelle Entnahme von Artikeln aus dem Vorrat
**Ablauf:**
1. Benutzer sucht Artikel (über Liste, Filter oder Scan)
2. Wählt Artikel aus
3. Gibt Entnahmemenge an (Teilentnahme oder komplett)
4. Artikel-Bestand wird reduziert bzw. Artikel wird entfernt
**Erfolgskriterium:** Entnahme in < 10 Sekunden möglich

### UC7: Ablaufende Artikel prüfen
**Akteur:** Befüller
**Vorbedingung:** Benutzer möchte Lebensmittelverschwendung vermeiden
**Ziel:** Übersicht über bald ablaufende Artikel
**Ablauf:**
1. Benutzer öffnet "Ablauf-Übersicht"
2. System zeigt Artikel sortiert nach Ablaufdatum (berechnet je nach Artikel-Typ)
3. Farbcodierung: Rot (< 3 Tage), Gelb (< 7 Tage), Normal
4. Haltbarkeit wird typ-spezifisch berechnet:
   - Gekauft: basierend auf MHD
   - Gekauft und eingefroren: Einfrierdatum + Gefrierzeit
   - Selbst hergestellt: Produktionsdatum + konfigurierte Haltbarkeit
**Erfolgskriterium:** Sofortige Übersicht, welche Artikel prioritär verbraucht werden sollten

### UC8: Vorrat durchsuchen
**Akteur:** Befüller
**Vorbedingung:** Benutzer sucht bestimmte Artikel oder möchte Überblick
**Ziel:** Artikel finden oder filtern
**Ablauf:**
1. Such- und Filterfunktion nutzen
2. Filtern nach: Kategorie, Lagerort, Ablaufdatum, Produktname
3. Sortieren nach verschiedenen Kriterien
4. Ergebnis anzeigen
**Erfolgskriterium:** Intuitive Bedienung, schnelle Ergebnisse

## Datenfelder pro Artikel

### Pflichtfelder
- **Produktname**: Was ist es?
- **Erfassungsdatum**: Wann wurde es erfasst?
- **Menge und Einheit**: Pro Packung auch mehrfach möglich (z.B. 600g, 12 Stück)
- **Lagerort**: z.B. Keller, Tiefkühltruhe, Kühlschrank

### Optionale Felder
- **Artikelkategorie**: Mehrfachauswahl möglich (z.B. Getränke, Alkoholisch)
- **Artikel-Typ**: Bestimmt, wie die Haltbarkeit berechnet wird
  - Gekauft (nicht gefroren): MHD ist relevant
  - Gekauft (bereits gefroren): MHD ist relevant
  - Gekauft und eingefroren: MHD wird ignoriert, Einfrierdatum + Gefrierzeit gilt
  - Selbst hergestellt (gefroren): Produktionsdatum + Gefrierzeit gilt
  - Selbst hergestellt (eingemacht): Produktionsdatum + geschätzte Haltbarkeit gilt
- **Mindesthaltbarkeitsdatum (MHD)**: Relevant bei gekauften Artikeln
- **Produktionsdatum/Erntedatum**: Bei selbst hergestellten Produkten wichtig
- **Einfrierdatum**: Wenn gekaufte Artikel nachträglich eingefroren werden
- **Barcode**: Falls vorhanden

## Funktionale Anforderungen

### Erfassung
- **Einfaches Erfassen**: Via Barcode und Produktdatenbank (wenn es eine offene API gibt)
- **Einkaufszettel-Scan**: Scannen vom Einkaufszettel und Markieren der zu erfassenden Produkte
- **MHD-Erfassung**: Optional via Kamera (Herausforderung: oft schlechte Druckqualität)
- **Wizard**: Max. 3 Schritte (Barcode vs. kein Barcode etc.)

### Verwaltung
- **Entnahme-Funktion**: Einfache Erfassung der Entnahme von Produkten
- **Übersichtsliste**: Mit Such- und Filterfunktionen
- **Ablaufdatum-Übersicht**: Anzeige von Produkten, die bald verbraucht werden müssen
  - Hinweis: Bei selbst eingemachten Produkten schwierig zu bestimmen

## User Stories

### Erfassung
- Als Befüller möchte ich Artikel per Barcode scannen, um schnell Produktdaten zu laden
- Als Befüller möchte ich mehrere Artikel nacheinander erfassen, ohne jedes Mal zur Startseite zu müssen
- Als Befüller möchte ich Mengenangaben flexibel eingeben können (z.B. "6x500g" oder "12 Stück"), um reale Verpackungen abzubilden
- Als Befüller möchte ich das MHD per Kamera erfassen, um Tippfehler zu vermeiden
- Als Befüller möchte ich häufig genutzte Lagerorte schnell auswählen können
- Als Befüller möchte ich bei selbst eingefrorenen Produkten das Produktionsdatum statt MHD erfassen

### Verwaltung
- Als Befüller möchte ich bei der Entnahme zwischen Teilmenge und vollständiger Entnahme wählen
- Als Befüller möchte ich sehen, welche Artikel bald ablaufen, um Lebensmittelverschwendung zu vermeiden
- Als Befüller möchte ich nach Kategorien filtern können (z.B. "alle Getränke"), um schnell einen Überblick zu bekommen
- Als Befüller möchte ich nach Lagerort filtern können (z.B. "was ist im Keller?")
- Als Befüller möchte ich sehen, wo sich ein Artikel befindet, ohne lange zu suchen

### Administration
- Als Administrator möchte ich Benutzer anlegen und verwalten
- Als Administrator möchte ich Kategorien definieren und bearbeiten
- Als Administrator möchte ich Lagerorte konfigurieren
- Als Administrator möchte ich Standardwerte für Gefrierzeiten festlegen (z.B. "Gemüse: 12 Monate")

## Geschäftsregeln & Validierungen

### Artikel
- Produktname ist Pflichtfeld (min. 2 Zeichen)
- Menge muss > 0 sein
- Lagerort ist Pflichtfeld
- Bei gefrorenen Artikeln: MHD ist optional, Gefrierzeit wird berücksichtigt
- Bei selbst hergestellten Produkten: Produktionsdatum ist wichtiger als MHD

### Haltbarkeit

Die Haltbarkeitsberechnung hängt vom Artikel-Typ ab:

#### 1. Gekauft (nicht gefroren)
- **Haltbarkeit**: MHD des Produkts
- **Beispiel**: Frisches Fleisch im Kühlschrank, Konserven im Vorratsschrank

#### 2. Gekauft (bereits gefroren)
- **Haltbarkeit**: MHD des Produkts (steht auf der Verpackung)
- **Beispiel**: Tiefkühlpizza, TK-Gemüse
- **Besonderheit**: Bleibt gefroren, MHD ist vom Hersteller angegeben

#### 3. Gekauft und eingefroren
- **Haltbarkeit**: Einfrierdatum + konfigurierbare Gefrierzeit (je nach Produktkategorie)
- **MHD wird ignoriert**: Das ursprüngliche MHD ist durch das Einfrieren hinfällig
- **Beispiel**: Frisches Fleisch gekauft (MHD 25.11.2025), eingefroren am 23.11.2025 → neue Haltbarkeit = 23.11.2025 + 6 Monate
- **Wichtig**: Einfrierdatum muss erfasst werden

#### 4. Selbst hergestellt (gefroren)
- **Haltbarkeit**: Produktionsdatum/Erntedatum + konfigurierbare Gefrierzeit
- **Beispiel**: Geerntete Tomaten eingefroren → Erntedatum + 12 Monate
- **Beispiel**: Selbstgekochte Bolognese → Kochdatum + 3 Monate

#### 5. Selbst hergestellt (eingemacht)
- **Haltbarkeit**: Produktionsdatum + geschätzte Haltbarkeit (konfigurierbar)
- **Beispiel**: Eingemachte Marmelade → Herstellungsdatum + 12 Monate
- **Herausforderung**: Haltbarkeit schwer zu bestimmen, konservative Schätzwerte nötig

#### Konfigurierbare Gefrierzeiten (Beispiele)
- Fleisch (roh): 6-12 Monate
- Fisch: 3-6 Monate
- Gemüse (blanchiert): 12 Monate
- Obst: 12 Monate
- Gekochte Gerichte: 3 Monate
- Backwaren: 3 Monate

### Entnahme
- Teilentnahme: Restmenge muss > 0 sein
- Bei Entnahme der gesamten Menge: Artikel wird als "entnommen" markiert (Soft-Delete, nicht gelöscht!)
- Entnahmedatum wird protokolliert
- Entnommene Artikel werden in Standardansicht nicht angezeigt (Filter: nur aktive Artikel)
- Daten bleiben erhalten für spätere Statistik-Features (Post-MVP)

### Kategorien
- Flache Tag-Struktur (keine Hierarchie im MVP)
- Mehrfachzuordnung möglich (z.B. "Getränke" + "Alkoholisch")
- Gut benannte, aussagekräftige Tags
- Admin kann Tags hinzufügen, bearbeiten, löschen

### Lagerorte
- Lagerorte sind konfigurierbar
- Vorschläge: Keller, Kühlschrank, Gefriertruhe, Gefrierschrank, Vorratsschrank
- Einem Lagerort kann ein Typ zugeordnet werden (gefroren/gekühlt/normal) → beeinflusst Haltbarkeitsberechnung

## Nicht-funktionale Anforderungen

### Benutzerfreundlichkeit
- Erfassung eines Artikels in max. 30 Sekunden
- Entnahme eines Artikels in max. 10 Sekunden
- Max. 3 Klicks/Schritte für häufige Aktionen
- Intuitive Bedienung, auch ohne Anleitung nutzbar

### Multi-User & Self-Hosting
- Mehrbenutzerfähig (ein Haushalt = mehrere Benutzer)
- Selbst-hostbar (für mittelfristige Open-Source-Veröffentlichung)
- Einfache Installation und Konfiguration

### Plattform
- Erreichbar von verschiedenen Geräten (Desktop, Tablet, Smartphone)
- Kamera-Zugriff für Barcode- und MHD-Scan (primär mobile Nutzung)

### Datenhaltung
- Artikel werden nicht gelöscht, sondern archiviert (für spätere Statistiken)
- Vollständige Historie der Entnahmen

### Erweiterbarkeit
- Vorbereitung für spätere Features: Statistiken, Einkaufslisten, Rezept-Integration

### Sicherheit & Access Control

#### Authentifizierung
- **Sichere Passwort-Speicherung**: Passwörter werden gehasht (z.B. bcrypt, Argon2)
- **Login mit Username/Email + Passwort**
- **Session-Management**: Sichere Session-Verwaltung mit HTTPOnly Cookies
- **Passwort-Anforderungen**: Mindestlänge, Komplexität (konfigurierbar)
- **Password-Reset-Funktion**: Per Email (nur für Admin)
- **Account-Lockout**: Nach X fehlgeschlagenen Login-Versuchen (konfigurierbar)
- **Logout-Funktion**: Sicheres Session-Beenden

#### Autorisierung & Rollen

**Rollenmodell:**
- **Administrator**: Volle Berechtigung
  - Benutzerverwaltung (anlegen, bearbeiten, löschen, Passwort zurücksetzen)
  - System-Konfiguration (Kategorien, Lagerorte, Gefrierzeiten)
  - Zugriff auf alle Vorrats-Daten
  - Kann alle Artikel erfassen, bearbeiten, entnehmen

- **Befüller (Normaler Benutzer)**: Eingeschränkte Berechtigung
  - Kann Artikel erfassen, bearbeiten, entnehmen
  - Kann Vorrat durchsuchen und filtern
  - Kann eigene Daten einsehen
  - **KANN NICHT**: Benutzer verwalten, System-Konfiguration ändern

**Access Control Rules:**
- Jeder Benutzer sieht den gesamten Vorrat des Haushalts (gemeinsamer Vorrat)
- Nur Admins können Benutzer verwalten
- Nur Admins können Kategorien und Lagerorte verwalten
- Jeder Benutzer kann Artikel erfassen und entnehmen
- Artikel gehören zum Haushalt, nicht zu einzelnen Benutzern

#### Sicherheits-Best-Practices (Implementierung)
- **HTTPS-Pflicht**: Verschlüsselte Verbindung (TLS)
- **CSRF-Schutz**: Cross-Site Request Forgery Protection
- **XSS-Schutz**: Input-Validierung, Output-Encoding
- **SQL-Injection-Schutz**: Prepared Statements / ORM
- **Rate-Limiting**: Schutz vor Brute-Force-Angriffen (Login)
- **Content Security Policy (CSP)**
- **Secure Headers**: X-Frame-Options, X-Content-Type-Options, etc.

#### Audit-Logging (MVP)
- **Login/Logout-Events**: Wer hat sich wann ein-/ausgeloggt
- **Artikel-Änderungen**: Wer hat welchen Artikel erfasst/entnommen/bearbeitet
- **Konfigurations-Änderungen**: Wer hat Kategorien/Lagerorte geändert
- **Benutzer-Verwaltung**: Wer hat welchen Benutzer angelegt/geändert

**Log-Informationen:**
- Timestamp
- Benutzer (wer)
- Aktion (was)
- Betroffenes Objekt (welcher Artikel/Benutzer/etc.)
- IP-Adresse (optional)

#### Datenschutz
- Passwörter werden niemals im Klartext gespeichert
- Passwörter werden niemals in Logs geschrieben
- Audit-Logs enthalten keine sensiblen Daten (Passwörter, Sessions)
- Session-Tokens sind kryptografisch sicher generiert

#### Post-MVP Sicherheits-Features
- ❌ Zwei-Faktor-Authentifizierung (2FA/MFA)
- ❌ OAuth/SAML Integration
- ❌ API-Keys für externe Zugriffe
- ❌ Erweiterte Rollen (z.B. Read-Only-Benutzer)
- ❌ Fine-Grained Permissions (z.B. nur bestimmte Lagerorte)

## Offene Fragen & Herausforderungen

### Barcode & Produktdatenbank
- Welche offene Produktdatenbank kann genutzt werden? (z.B. Open Food Facts)
- Wie gehen wir mit unbekannten Barcodes um?
- Wie funktioniert das bei selbst eingefrorenen Produkten ohne Barcode?

### MHD-Erkennung via OCR
- Ist OCR bei oft schlechter Druckqualität zuverlässig genug?
- Fallback auf manuelle Eingabe?

### Haltbarkeit bei selbst hergestellten Produkten
- Wie bestimmen wir die Haltbarkeit von selbst Eingemachtem/Eingefrorenem?
- Konfigurierbare Standardwerte pro Kategorie?
- Benutzer-definierte Haltbarkeit?

### Einkaufszettel-Scan
- Welche OCR-Technologie?
- Wie zuverlässig ist das bei verschiedenen Kassenzettel-Formaten?
- Ist das ein Must-Have oder Nice-to-Have?

## MVP Definition (Version 1.0)

### Was ist IM MVP (Must-Have)

#### Artikel-Erfassung (manuell)
- ✅ Produktname, Menge, Einheit manuell eingeben
- ✅ Lagerort auswählen (aus konfigurierbarer Liste)
- ✅ Artikel-Typ auswählen (die 5 Typen)
- ✅ MHD manuell eingeben (für gekaufte Artikel)
- ✅ Produktionsdatum/Einfrierdatum manuell eingeben (für selbst hergestellte/eingefrorene)
- ✅ Kategorien zuordnen (einfache Tags, keine Hierarchie)
- ✅ Wizard mit max. 3 Schritten
- ✅ "Nächster Artikel" nach Erfassung, ohne zur Startseite zu müssen

#### Vorrats-Verwaltung
- ✅ Liste aller aktiven Artikel
- ✅ Suche nach Produktname
- ✅ Filter nach: Kategorie, Lagerort, Artikel-Typ
- ✅ Sortierung nach: Ablaufdatum, Produktname, Erfassungsdatum
- ✅ Artikel-Details anzeigen

#### Entnahme
- ✅ Artikel entnehmen (Teilmenge oder komplett)
- ✅ Bei vollständiger Entnahme: Artikel wird als "entnommen" markiert (nicht gelöscht!)
- ✅ Entnahmedatum wird gespeichert
- ✅ Entnommene Artikel werden NICHT in der Standardansicht angezeigt
- ✅ Bei Teilentnahme: Menge wird reduziert

#### Haltbarkeits-Dashboard
- ✅ Übersicht über bald ablaufende Artikel
- ✅ Farbcodierung: Rot (< 3 Tage), Gelb (< 7 Tage), Grün/Normal (> 7 Tage)
- ✅ Typ-spezifische Haltbarkeitsberechnung (alle 5 Typen)
- ✅ Sortiert nach Ablaufdatum (dringendste zuerst)

#### Konfigurations-Verwaltung (Admin)
- ✅ Benutzer anlegen, bearbeiten, löschen
- ✅ Kategorien/Tags definieren und verwalten (flache Liste, keine Hierarchie)
- ✅ Lagerorte definieren und verwalten
- ✅ Lagerort-Typen zuordnen (gefroren/gekühlt/normal)
- ✅ Gefrierzeiten konfigurieren (pro Kategorie)
- ✅ Standard-Haltbarkeitszeiten für eingemachte Produkte konfigurieren

#### Sicherheit & Access Control
- ✅ Authentifizierung (Login/Logout)
- ✅ Sichere Passwort-Speicherung (Hashing)
- ✅ Session-Management
- ✅ Rollenbasierte Zugriffskontrolle (Admin vs. Befüller)
- ✅ CSRF-Schutz
- ✅ XSS-Schutz (Input-Validierung)
- ✅ SQL-Injection-Schutz (Prepared Statements/ORM)
- ✅ Rate-Limiting (Login)
- ✅ Audit-Logging (wer hat was wann gemacht)
- ✅ HTTPS-Unterstützung

#### Plattform & Deployment
- ✅ Web-Anwendung (responsive, funktioniert auf Desktop & Mobile Browser)
- ✅ Self-hostbar (z.B. Docker)
- ✅ Einfache Installation und Konfiguration
- ✅ Multi-User (Benutzerverwaltung)

---

### Was ist NICHT im MVP (Post-MVP / Nice-to-Have)

#### Phase 2: Automatisierung & Komfort
- ❌ Barcode-Scanner Integration
- ❌ Produktdatenbank-Anbindung (Open Food Facts)
- ❌ OCR für MHD-Erkennung
- ❌ OCR für Einkaufszettel-Scan
- ❌ Bulk-Import / CSV-Import
- ❌ Barcode manuell eingeben (optional für spätere Suche)

#### Phase 3: Erweiterte Features
- ❌ Archiv-Ansicht (entnommene Artikel anzeigen)
- ❌ Statistiken (was wird am meisten verbraucht, Verschwendungsrate)
- ❌ Verbrauchshistorie / Diagramme
- ❌ Einkaufslisten-Generator (basierend auf Vorrat)
- ❌ Rezept-Integration
- ❌ Benachrichtigungen (Push/Email bei ablaufenden Artikeln)

#### Phase 4: Advanced & SaaS
- ❌ Native Mobile Apps (iOS/Android)
- ❌ Offline-Modus
- ❌ Sharing zwischen Haushalten
- ❌ Cloud-SaaS-Option
- ❌ Hierarchische Kategorien
- ❌ Fotos von Artikeln

---

## MVP-Scope-Zusammenfassung

**Fokus:** Manuelle, aber schnelle und intuitive Erfassung und Verwaltung von Lebensmittelvorräten mit intelligenter Haltbarkeitsberechnung.

**Nicht im Scope:** Automatisierung (Barcode, OCR), Statistiken, Archivansicht, erweiterte Features.

**Wichtigste Design-Entscheidungen:**
1. **Manuelle Eingabe**: Schnell und einfach, ohne technische Komplexität
2. **Flache Tags**: Keine hierarchischen Kategorien
3. **Soft-Delete**: Entnommene Artikel werden markiert, nicht gelöscht → Daten bleiben für spätere Features erhalten
4. **Web-First**: Responsive Web-App, keine nativen Apps
5. **Sicherheit First**: Sauberes Access Control, Audit-Logging, sichere Passwort-Verwaltung von Anfang an

## Technische Hinweise
- Die Anwendung muss gut geplant werden
- Barcode-Integration mit offener Produktdatenbank prüfen (Post-MVP)
- OCR für MHD und Einkaufszettel evaluieren (Post-MVP)




