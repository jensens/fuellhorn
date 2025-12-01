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

Sticky am unteren Bildschirmrand, immer sichtbar:

```
┌─────────────────────────────────┐
│ [🏠]    [➕]    [📦]    [⋯]     │
│ Über-   Erfas-  Vorrat   Mehr   │
│ sicht   sen                     │
└─────────────────────────────────┘
```

| Icon | Label | Route | Beschreibung |
|------|-------|-------|--------------|
| 🏠 | Übersicht | `/dashboard` | Dashboard |
| ➕ | Erfassen | `/items/add` | Wizard starten |
| 📦 | Vorrat | `/items` | Vorratsliste |
| ⋯ | Mehr | - | Menü öffnet sich |

**"Mehr"-Menü:**
- Einstellungen (Admin)
- Profil / Passwort ändern
- Abmelden

### Seitenstruktur

```
/login              - Anmeldeseite
/dashboard          - Übersicht (nach Login)
/items              - Vorratsliste
/items/add          - Artikel erfassen (Wizard)
/items/{id}/edit    - Artikel bearbeiten
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

**Session-Länge:**
- Mit "Angemeldet bleiben": 30 Tage
- Ohne: 24 Stunden

### 3.2 Artikel erfassen (3-Schritt-Wizard)

```
Schritt 1: Grunddaten
    │
    ├── Produktname *
    ├── Artikel-Typ * (5 Optionen)
    ├── Menge * + Einheit *
    │
    └── [Weiter →]

Schritt 2: Datum
    │
    ├── MHD / Produktionsdatum / Einfrierdatum
    │   (abhängig vom Artikel-Typ)
    ├── Notizen (optional)
    │
    └── [← Zurück] [Weiter →]

Schritt 3: Lagerort & Kategorien
    │
    ├── Lagerort *
    ├── Kategorien (optional, Multi-Select)
    │
    └── [← Zurück] [💾 Speichern]
                   [💾 Speichern & Nächster]
```

**Smart Defaults (Zeitfenster 30 Min):**
- Artikel-Typ: Letzter Typ oder "Gekauft (nicht gefroren)"
- Einheit: Letzte verwendete Einheit
- Lagerort: Letzter Lagerort
- Kategorien: Letzte Kategorien

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
