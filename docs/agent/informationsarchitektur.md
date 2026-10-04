# Informationsarchitektur

Dieses Dokument beschreibt die Struktur, Navigation und User Flows der Füllhorn-App.

---

## 1. Hauptbereiche

Füllhorn ist eine mobile-first Vorratsverwaltung mit vier Hauptbereichen:

| Bereich | Route | Rolle | Beschreibung |
|---------|-------|-------|--------------|
| Übersicht | `/dashboard` | Alle | Dashboard mit ablaufenden Artikeln |
| Erfassen | `/items/add` | Alle | Artikel schnell erfassen (Wizard) |
| Vorrat | `/items` | Alle | Vorratsliste durchsuchen |
| Einstellungen | `/admin/*` | Admin | Kategorien, Lagerorte, Benutzer |

### Priorisierung

```
1. Übersicht      [Alle]  - Kritische Artikel sofort sichtbar
2. Erfassen       [Alle]  - Häufigste Aktion (1-2 Taps erreichbar)
3. Vorrat         [Alle]  - Suche und Filter
4. Einstellungen  [Admin] - Verwaltung
```

---

## 2. Navigation

### Bottom Navigation (Mobile)

Sticky am unteren Bildschirmrand, immer sichtbar (`app/ui/components/bottom_nav.py`, drei Einträge):

```
┌─────────────────────────────────┐
│   [🏠]       [➕]       [📦]    │
│  Übersicht  Erfassen   Vorrat   │
└─────────────────────────────────┘
```

| Icon | Label | Route | Beschreibung |
|------|-------|-------|--------------|
| 🏠 | Übersicht | `/dashboard` | Dashboard |
| ➕ | Erfassen | `/items/add` | Wizard starten |
| 📦 | Vorrat | `/items` | Vorratsliste |

**Benutzermenü** (oben rechts im Dashboard, `app/ui/components/user_dropdown.py`):
- Profil (`/profile`: Passwort, E-Mail, Smart-Default-Zeitfenster)
- Einstellungen (nur Admin, `/admin/settings`)
- Abmelden

### Seitenstruktur

```
/                   - Login bzw. Weiterleitung zum Dashboard
/login              - Anmeldeseite
/dashboard          - Übersicht (nach Login)
/items              - Vorratsliste (Filter: ?location=<id>, ?filter=expiring)
/items/add          - Artikel erfassen (Wizard)
/items/{id}/edit    - Artikel bearbeiten
/profile            - Profil (Passwort, E-Mail, Smart-Default-Zeitfenster)
/admin/settings     - Einstellungen: Einstieg zu Kategorien, Lagerorten, Benutzern; System-Defaults
/admin/categories   - Kategorien verwalten
/admin/locations    - Lagerorte verwalten
/admin/users        - Benutzer verwalten
```

---

## 3. User Flows

### 3.1 Login

```
Login-Seite
    │
    ├── Benutzername + Passwort eingeben
    ├── [Optional] "Angemeldet bleiben" aktivieren
    │
    └── → Dashboard
```

**Session-Länge** (`app/auth/session.py`, Issue #384):
- Mit "Angemeldet bleiben": 30 Tage (`REMEMBER_ME_MAX_AGE`, Cookie-Laufzeit, verlängert sich bei jedem Aufruf)
- Ohne: 24 Stunden ohne Aktivität (`SESSION_MAX_AGE`)
- Passwortänderung meldet alle anderen Sitzungen des Benutzers ab; die Login-Seite nennt den Grund

### 3.2 Artikel erfassen (3-Schritt-Wizard)

```
Schritt 1: Basisinformationen
    │
    ├── Produktname *
    ├── Artikel-Typ * (5 Optionen, Chips)
    ├── Menge * + Einheit * (Chips)
    ├── Notizen (optional, in jedem Schritt editierbar)
    │
    └── [Weiter →]

Schritt 2: Haltbarkeit
    │
    ├── Kategorie * (Chips, nach Artikel-Typ gefiltert und nach Gruppen sortiert)
    ├── Datum je Typ: MHD / Hergestellt am / Eingefroren am
    │   ("Selbst eingefroren" erfasst Herstellungs- und Einfrierdatum, siehe architektur_erklaert.md)
    ├── Notizen (optional)
    │
    └── [← Zurück] [Weiter →]

Schritt 3: Lagerort & Notizen
    │
    ├── Lagerort * (Chips, nur zum Typ passende Lagerorte)
    ├── Notizen (optional)
    │
    └── [← Zurück] [💾 Speichern]
                   [💾 Speichern & Nächster]
```

Pflichtfelder zeigen ihre Meldung unter dem Feld, sobald es berührt wurde oder Weiter/Speichern
trotz Fehlern geklickt wird; die Buttons bleiben zusätzlich deaktiviert (Issue #396).

**Smart Defaults** (letzter Eintrag pro Nutzer in `user.preferences`; Zeitfenster aus Profil > System-Default >
Hardcoded: Typ 30, Kategorie 30, Lagerort 60 Min; Issue #397):
- Artikel-Typ: Letzter Typ innerhalb des Zeitfensters, sonst **keine Vorauswahl** – der Typ bestimmt
  Datums-Semantik und Filter (#387), ein stiller Default wäre eine Fehlerquelle
- Einheit: Letzte verwendete Einheit (ohne Zeitfenster), sonst "g"
- Lagerort: Letzter Lagerort innerhalb des Zeitfensters, sofern er zum Typ passt (#385)
- Kategorie: Letzte Kategorie innerhalb des Zeitfensters, sofern sie für den Typ angeboten wird

**"Speichern & Nächster":** Wichtigster Button für Bulk-Erfassung!

### 3.3 Artikel entnehmen

```
Vorratsliste oder Dashboard
    │
    ├── Auf Artikel tippen
    │
    └── Bottom Sheet öffnet sich
            │
            ├── Artikel-Details anzeigen
            ├── Menge eingeben (oder "Vollständig")
            │
            └── [Entnehmen] → Bestätigung Toast
```

**Alternativen:**
- Swipe-to-entnehmen (links wischen)
- Quick-Action Button in Item Card

### 3.4 Admin: Kategorien/Lagerorte verwalten

```
Einstellungen
    │
    ├── Kategorien verwalten >
    │       │
    │       ├── Liste mit Drag & Drop Sortierung
    │       ├── [+ Neue Kategorie]
    │       │       └── Dialog: Name + Farbe
    │       ├── [Bearbeiten] → Dialog
    │       └── [Löschen] → Bestätigung
    │
    └── Lagerorte verwalten >
            └── (analog zu Kategorien)
```

---

## 4. Rollen & Berechtigungen

### Zwei Rollen

| Rolle | Beschreibung |
|-------|--------------|
| `admin` | Voller Zugriff auf alles |
| `user` | Items lesen/schreiben, kein Admin-Bereich |

### Berechtigungsmatrix

| Aktion | user | admin |
|--------|------|-------|
| Dashboard sehen | ✅ | ✅ |
| Artikel erfassen | ✅ | ✅ |
| Artikel entnehmen | ✅ | ✅ |
| Vorrat durchsuchen | ✅ | ✅ |
| Kategorien verwalten | ❌ | ✅ |
| Lagerorte verwalten | ❌ | ✅ |
| Benutzer verwalten | ❌ | ✅ |

---

## 5. Artikel-Typen

Füllhorn unterscheidet 5 Artikel-Typen mit unterschiedlicher Haltbarkeitsberechnung:

| Typ | Beschreibung | Datum-Feld |
|-----|--------------|------------|
| `purchased_fresh` | Gekauft (nicht gefroren) | MHD |
| `purchased_frozen` | Gekauft (gefroren) | MHD |
| `purchased_then_frozen` | Gekauft & eingefroren | Einfrierdatum |
| `homemade_frozen` | Selbst hergestellt (TK) | Produktionsdatum |
| `homemade_preserved` | Selbst hergestellt (eingemacht) | Produktionsdatum |

**Haltbarkeitsberechnung:**
- `purchased_*`: MHD direkt verwenden
- `*_then_frozen` / `homemade_frozen`: Einfrierdatum + Gefrierzeit (Standard: 12 Monate)
- `homemade_preserved`: Produktionsdatum + Haltbarkeit (konfigurierbar)

---

## 6. Status-Anzeige

Artikel werden nach Ablaufdatum farblich gekennzeichnet:

| Status | Tage bis Ablauf | Farbe | Anzeige |
|--------|-----------------|-------|---------|
| Critical | < 3 Tage | Coral | 🔴 Border links |
| Warning | 3-7 Tage | Amber | 🟡 Border links |
| OK | > 7 Tage | Leaf | 🟢 Border links |

**Dashboard zeigt priorisiert:**
1. Kritische Artikel (abgelaufen / heute)
2. Warnungen (nächste 7 Tage)
3. Statistik (Gesamt, Ablaufend, Diese Woche entnommen)

---

## 7. Interaktions-Patterns

### Mobile Gesten

| Geste | Aktion |
|-------|--------|
| Tap | Element auswählen / öffnen |
| Swipe Left | Entnehmen-Aktion |
| Pull-to-Refresh | Listen aktualisieren |
| Long-Press | Context-Menu (Bearbeiten, Löschen) |
| Swipe-down | Bottom Sheet schließen |

### Feedback

| Aktion | Feedback |
|--------|----------|
| Button Press | Visual + Light Haptic |
| Erfolgreich | Toast + Success Haptic |
| Fehler | Inline-Fehler + Error Haptic |

---

## 8. Responsive Verhalten

| Viewport | Layout |
|----------|--------|
| Mobile (< 640px) | Bottom Nav, Single Column, Cards Full-Width |
| Tablet (640-1024px) | Bottom Nav oder Sidebar, Two-Column |
| Desktop (> 1024px) | Left Sidebar, Multi-Column, Tabellen |

**Max-Width für Inhalte:** 800px
