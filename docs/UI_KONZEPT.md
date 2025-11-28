# UI/UX Konzept - Fuellhorn

## 1. Design-Prinzipien

### 1.1 Core Principles
- **Mobile First**: Primär für Smartphone optimiert (Touch-Bedienung)
- **Schnelligkeit**: Häufige Aktionen in 1-2 Taps erreichbar
- **Einfachheit**: Fokus auf Kernfunktionen, keine Überladung
- **Touch-Optimiert**: Große Buttons (min. 44x44px), Touch-Targets
- **Offline-Ready**: Auch bei schlechtem Netz nutzbar (Post-MVP)

### 1.2 Zielgruppe
- **Primär**: Familien beim Einkaufen, am Kühlschrank, in der Küche
- **Nutzungskontext**: Smartphone in der Hand, oft einhändig
- **Verwendung**: Mehrmals pro Woche (Einkaufen, Kochen)
- **Geräte**: Primär Smartphone (80%), Tablet (15%), Desktop (5%)

### 1.3 Unterschied zu VellenBase
| Aspekt | VellenBase | Fuellhorn |
|--------|-----------|-----------|
| Primäre Plattform | Desktop | Smartphone |
| Navigation | Left Sidebar | Bottom Navigation |
| Hauptaktion | Daten verwalten | Schnell erfassen |
| Session-Länge | 10-30 Min | 1-3 Min |
| Nutzungshäufigkeit | 1-2x Woche | 3-5x Woche |

---

## 2. Informationsarchitektur

### 2.1 Hauptbereiche (nach Priorität)
```
1. 📱 Übersicht       [Alle]  - Dashboard mit ablaufenden Artikeln
2. ➕ Erfassen        [Alle]  - Artikel schnell erfassen
3. 🗑️ Entnehmen       [Alle]  - Artikel entnehmen
4. 📦 Vorrat          [Alle]  - Vorratsliste durchsuchen
5. ⚙️ Einstellungen   [Admin] - Kategorien, Lagerorte, Benutzer
```

### 2.2 Navigation-Pattern
**Bottom Navigation Bar** (immer sichtbar):
- Icon + Label für Hauptbereiche
- 4 Hauptitems (Übersicht, Erfassen, Vorrat, Mehr)
- Sticky am unteren Bildschirmrand
- Active State deutlich sichtbar

**Vorteil gegenüber Sidebar:**
- Einhändige Bedienung (Daumen-Reichweite)
- Standard-Pattern für Mobile Apps
- Schneller Zugriff auf Hauptfunktionen
- Mehr vertikaler Platz

---

## 3. Screen-Designs (Wireframes)

### 3.1 Login-Seite (Mobile)
```
┌─────────────────────────┐
│                         │
│    [📦 Platzhalter]     │ ← Logo kommt später
│      Füllhorn           │
│  Vorratsverwaltung      │
│                         │
│  ┌───────────────────┐  │
│  │ Benutzername      │  │
│  │ [____________]    │  │
│  │                   │  │
│  │ Passwort          │  │
│  │ [____________] 👁  │  │
│  │                   │  │
│  │ □ Angemeldet      │  │
│  │   bleiben         │  │
│  │                   │  │
│  │   [Anmelden]      │  │
│  └───────────────────┘  │
│                         │
└─────────────────────────┘
```

**Logo:**
- **MVP**: Platzhalter (📦 Icon + "Füllhorn" Text)
- **Post-MVP**: Richtiges Logo (kommt im Laufe des Projekts)

**Session-Management:**
- **"Angemeldet bleiben"** Checkbox (standardmäßig AN)
- Session-Länge:
  - **MIT** "Angemeldet bleiben": 30 Tage (konfigurierbar)
  - **OHNE** "Angemeldet bleiben": 24 Stunden
- Wichtig: Benutzer sollen sich **nicht ständig neu anmelden** müssen
- Remember-Me Token sicher in DB gespeichert

**UX-Details:**
- Passwort mit Show/Hide Toggle
- Enter-Taste auf Tastatur sendet Form
- Autofocus auf Username-Feld
- Keine "Passwort vergessen" (Admin reset)
- Session bleibt lange aktiv (30 Tage default)

---

### 3.2 Übersicht / Dashboard (Mobile)
```
┌─────────────────────────────────┐
│ Füllhorn           [@User] ⚙️   │
├─────────────────────────────────┤
│                                 │
│ 🔴 Bald abgelaufen (3)          │
│ ┌─────────────────────────────┐ │
│ │ 🔴 Milch                    │ │
│ │    Läuft ab: Heute          │ │
│ │    Kühlschrank              │ │
│ │                    [Entn.] │ │
│ ├─────────────────────────────┤ │
│ │ 🔴 Joghurt                  │ │
│ │    Läuft ab: Morgen         │ │
│ │    Kühlschrank    [Entn.] │ │
│ ├─────────────────────────────┤ │
│ │ 🟡 Käse                     │ │
│ │    Läuft ab: in 4 Tagen     │ │
│ │    Kühlschrank    [Entn.] │ │
│ └─────────────────────────────┘ │
│                                 │
│ 📊 Vorrats-Statistik            │
│ ┌──────────┬──────────┬────────┐│
│ │  Artikel │  Ablauf  │ Entn.  ││
│ │    45    │    3     │  12    ││
│ └──────────┴──────────┴────────┘│
│                                 │
│ 🏷️ Schnellfilter                │
│ [Kühlschrank] [Tiefkühler]     │
│ [Keller] [Vorratsschrank]      │
│                                 │
├─────────────────────────────────┤
│ [🏠] [➕] [📦] [⋯]  ← Bottom Nav│
└─────────────────────────────────┘
```

**UX-Details:**
- Kritische Artikel sofort sichtbar (rot/gelb)
- Swipe-to-entnehmen (wie E-Mail-Apps)
- Quick-Filter als Chips
- Bottom Navigation immer sichtbar
- Pull-to-Refresh

---

### 3.3 Artikel Erfassen (Wizard - Mobile)
```
┌─────────────────────────────────┐
│ ← Artikel erfassen     [X]      │
├─────────────────────────────────┤
│                                 │
│ Schritt 1 von 3                 │
│ ▓▓▓▓▓░░░░░░░░░░░░░░░░           │
│                                 │
│ Produktname *                   │
│ ┌─────────────────────────────┐ │
│ │ [___________________]       │ │
│ └─────────────────────────────┘ │
│                                 │
│ Artikel-Typ *                   │
│ ┌─────────────────────────────┐ │
│ │ ● Gekauft (nicht gefroren)  │ │ ← Default (oder letzter)
│ │ ○ Gekauft (gefroren)        │ │
│ │ ○ Gekauft & eingefroren     │ │
│ │ ○ Selbst hergestellt (TK)   │ │
│ │ ○ Selbst hergestellt (eingem│ │
│ └─────────────────────────────┘ │
│                                 │
│ Menge *          Einheit *      │
│ ┌──────┐         ┌───────────┐  │
│ │ [__] │         │ [g     ▼] │  │
│ └──────┘         └───────────┘  │
│                                 │
│                                 │
│         [Weiter →]              │
│                                 │
└─────────────────────────────────┘
```

**Smart Defaults (Schritt 1):**
- **Artikel-Typ**:
  - Default: "Gekauft (nicht gefroren)" (>90% der Fälle)
  - ABER: Wenn innerhalb der letzten 30 Min ein Artikel erfasst wurde → letzten Typ vorauswählen
  - Zeitfenster konfigurierbar in Settings (z.B. 15-60 Min)
- **Produktname**: Autofokus, leeres Feld
- **Menge**: Leeres Feld
- **Einheit**: Letzte verwendete Einheit (oder "g" als Fallback)

**Schritt 2: Datum erfassen**
```
┌─────────────────────────────────┐
│ ← Artikel erfassen     [X]      │
├─────────────────────────────────┤
│                                 │
│ Schritt 2 von 3                 │
│ ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░            │
│                                 │
│ Tomaten aus Garten              │
│ 500g                            │
│ Typ: Selbst hergestellt (TK)    │
│                                 │
│ Produktionsdatum (Erntedatum) * │
│ ┌─────────────────────────────┐ │
│ │ [23.11.2025]         📅     │ │
│ └─────────────────────────────┘ │
│                                 │
│ ℹ️ Haltbarkeit wird automatisch │
│    berechnet: Erntedatum +      │
│    12 Monate (Gemüse)           │
│                                 │
│ Notizen (optional)              │
│ ┌─────────────────────────────┐ │
│ │ [blanchiert]                │ │
│ └─────────────────────────────┘ │
│                                 │
│  [← Zurück]      [Weiter →]    │
│                                 │
└─────────────────────────────────┘
```

**Schritt 3: Lagerort & Kategorien**
```
┌─────────────────────────────────┐
│ ← Artikel erfassen     [X]      │
├─────────────────────────────────┤
│                                 │
│ Schritt 3 von 3                 │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓            │
│                                 │
│ Tomaten aus Garten              │
│ 500g, Erntedatum: 23.11.2025    │
│                                 │
│ Lagerort *                      │
│ ┌─────────────────────────────┐ │
│ │ [Tiefkühltruhe          ▼]  │ │ ← Letzter Lagerort
│ └─────────────────────────────┘ │
│                                 │
│ Kategorien (optional)           │
│ [+ Kategorie hinzufügen]        │
│                                 │
│ Ausgewählt:                     │
│ [Gemüse ×] [Garten ×]          │ ← Letzte Kategorien
│                                 │
│                                 │
│                                 │
│  [← Zurück]  [💾 Speichern]    │
│                                 │
│  [💾 Speichern & Nächster]     │
│                                 │
└─────────────────────────────────┘
```

**Smart Defaults (Schritt 2 - Datum):**
- **Produktionsdatum / Einfrierdatum**:
  - Default: Heutiges Datum
  - Wenn innerhalb 30 Min ein Artikel erfasst wurde → Letztes Datum vorauswählen
  - Zeitfenster: 30 Min (konfigurierbar)
  - Sinnvoll für: Mehrere Artikel am selben Tag einfrieren

**Smart Defaults (Schritt 3):**
- **Lagerort**:
  - Letzten Lagerort vorauswählen (wenn man an der Truhe steht → mehrere TK-Artikel nacheinander)
  - **Zeitfenster: 60 Min** (konfigurierbar) - danach erster Lagerort in Liste
- **Kategorien**:
  - Letzte Kategorie(n) vorauswählen (z.B. wenn 5x "Gemüse" erfasst wird)
  - Benutzer kann einfach ändern/löschen
  - Zeitfenster: 30 Min (konfigurierbar) - danach leere Auswahl

**UX-Details:**
- 3 Schritte klar strukturiert
- Fortschrittsbalken oben
- Zusammenfassung in jedem Schritt
- **"Speichern & Nächster"** für Bulk-Erfassung (wichtigster Button!)
- Große Touch-Targets (min. 48px)
- Zurück-Button im Header + als Button
- Autofokus auf nächstes Feld
- **Intelligente Vorauswahl** spart 80% der Taps bei Bulk-Erfassung

---

### 3.4 Vorratsliste (Mobile)
```
┌─────────────────────────────────┐
│ 📦 Vorrat          🔍  ⚙️       │
├─────────────────────────────────┤
│                                 │
│ Suchen...                       │
│ ┌─────────────────────────────┐ │
│ │ [___________________]    🔍 │ │
│ └─────────────────────────────┘ │
│                                 │
│ Filter: [Alle ▼] [Lagerort ▼] │
│ Sort: [Ablaufdatum ▼]          │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 🔴 Milch              1L    │ │
│ │    Läuft ab: Heute          │ │
│ │    📍 Kühlschrank           │ │
│ │    [Details] [Entnehmen]   │ │
│ ├─────────────────────────────┤ │
│ │ 🟢 Nudeln             500g  │ │
│ │    MHD: 12.05.2026          │ │
│ │    📍 Vorratsschrank        │ │
│ │    [Details] [Entnehmen]   │ │
│ ├─────────────────────────────┤ │
│ │ 🟢 Tomaten (TK)       500g  │ │
│ │    Haltbar bis: 23.11.2026  │ │
│ │    📍 Tiefkühltruhe         │ │
│ │    [Details] [Entnehmen]   │ │
│ └─────────────────────────────┘ │
│                                 │
│              ↓                  │
│        [Mehr laden]             │
│                                 │
├─────────────────────────────────┤
│ [🏠] [➕] [📦] [⋯]              │
└─────────────────────────────────┘
```

**UX-Details:**
- Infinite Scroll / "Mehr laden"
- Swipe-to-entnehmen (links wischen)
- Farbcodierung pro Artikel (rot/gelb/grün)
- Schnellzugriff auf Details & Entnehmen
- Live-Suche (debounced)
- Pull-to-Refresh

**Alternative: Card-Layout (größer, Touch-freundlicher)**
```
┌─────────────────────────────────┐
│ ┌───────────────────────────┐   │
│ │ 🔴 Milch                  │   │
│ │ ─────────────────────────  │   │
│ │ Menge: 1L                 │   │
│ │ Läuft ab: Heute           │   │
│ │ 📍 Kühlschrank            │   │
│ │                           │   │
│ │ [Details]    [Entnehmen]  │   │
│ └───────────────────────────┘   │
│                                 │
│ ┌───────────────────────────┐   │
│ │ 🟢 Nudeln                 │   │
│ │ ─────────────────────────  │   │
│ │ ...                       │   │
│ └───────────────────────────┘   │
└─────────────────────────────────┘
```

---

### 3.5 Artikel Entnehmen (Bottom Sheet)
```
┌─────────────────────────────────┐
│                                 │
│        (Hintergrund gedimmt)    │
│                                 │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ ──────                      │ │ ← Swipe-Handle
│ │                             │ │
│ │ Milch entnehmen             │ │
│ │                             │ │
│ │ Verfügbar: 1L               │ │
│ │                             │ │
│ │ Entnehmen:                  │ │
│ │ ┌──────┐  ┌───────────┐    │ │
│ │ │ [1 ] │  │ [L     ▼] │    │ │
│ │ └──────┘  └───────────┘    │ │
│ │                             │ │
│ │ ○ Teilmenge                 │ │
│ │ ● Vollständig entnehmen     │ │
│ │                             │ │
│ │ [Abbrechen] [✓ Entnehmen]  │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**UX-Details:**
- Bottom Sheet (swipe-down to close)
- Große Buttons
- Smart Default: Vollständig entnehmen vorausgewählt
- Einheit aus Artikel übernehmen
- Bestätigung mit Haptic Feedback
- Toast-Notification nach Erfolg

---

### 3.6 Einstellungen (Mobile - Admin)
```
┌─────────────────────────────────┐
│ ← Einstellungen                 │
├─────────────────────────────────┤
│                                 │
│ 👤 Benutzer                     │
│ ┌─────────────────────────────┐ │
│ │ Benutzer verwalten        > │ │
│ └─────────────────────────────┘ │
│                                 │
│ 🏷️ Kategorien                   │
│ ┌─────────────────────────────┐ │
│ │ Kategorien verwalten      > │ │
│ └─────────────────────────────┘ │
│                                 │
│ 📍 Lagerorte                    │
│ ┌─────────────────────────────┐ │
│ │ Lagerorte verwalten       > │ │
│ └─────────────────────────────┘ │
│                                 │
│ ❄️ Gefrierzeiten                │
│ ┌─────────────────────────────┐ │
│ │ Gefrierzeiten konfigurieren>│ │
│ └─────────────────────────────┘ │
│                                 │
│ 🔒 Profil                       │
│ ┌─────────────────────────────┐ │
│ │ Passwort ändern           > │ │
│ │ Abmelden                  > │ │
│ └─────────────────────────────┘ │
│                                 │
├─────────────────────────────────┤
│ [🏠] [➕] [📦] [⋯]              │
└─────────────────────────────────┘
```

**UX-Details:**
- Gruppierte Settings
- Icons für schnelle Erkennung
- Chevron (>) zeigt weitere Screens an
- Nur für Admins sichtbar
- Normale User sehen nur Profil

---

## 4. Bottom Navigation (Mobile)

```
┌─────────────────────────────────┐
│ [🏠]    [➕]    [📦]    [⋯]     │
│ Über-   Erfas- Vorrat  Mehr     │
│ sicht   sen                     │
└─────────────────────────────────┘
```

**Items:**
1. **🏠 Übersicht** - Dashboard mit ablaufenden Artikeln
2. **➕ Erfassen** - Artikel schnell erfassen (Wizard)
3. **📦 Vorrat** - Vorratsliste durchsuchen
4. **⋯ Mehr** - Einstellungen, Profil, Hilfe

**Active State:**
- Icon + Label farbig (Primary Color)
- Leichter Glow-Effekt

---

## 5. UI-Komponenten-Bibliothek

### 5.1 Standard-Komponenten (NiceGUI + Custom)

**Buttons:**
- **Primary Button** (CTA): Groß (48px Höhe), Primary Color
- **Secondary Button**: Outlined, 48px Höhe
- **Icon Button**: 48x48px (Touch-Target)
- **FAB** (Floating Action Button): Primäre Aktion pro Screen

**Cards:**
- Artikel-Card: Mit Farbcodierung (Border-Left: rot/gelb/grün)
- Dashboard-Card: Statistiken, Quick-Actions
- Shadow: Elevation-2 (leicht erhaben)

**Inputs:**
- Text Input: 48px Höhe, großer Font (16px)
- Number Input: Mit +/- Buttons (touch-freundlich)
- Select/Dropdown: Native Mobile Picker nutzen
- Date Picker: Native Mobile Date Picker
- Radio Buttons: 44x44px Touch-Target

**Bottom Sheet:**
- Swipe-Handle oben
- Backdrop Overlay (dimmed)
- Swipe-to-close

**Navigation:**
- Bottom Nav: 56px Höhe
- Top Bar: 56px Höhe

### 5.2 Farbschema (Mobile-optimiert)

```
Primary:     #10b981 (Grün - Frisch, Lebensmittel)
Secondary:   #3b82f6 (Blau - Vertrauenswürdig)
Success:     #22c55e (Grün - Positiv)
Warning:     #f59e0b (Orange - Achtung, bald ablaufend)
Danger:      #ef4444 (Rot - Kritisch, abgelaufen)
Neutral:     #6b7280 (Grau - Text/Borders)
Background:  #ffffff (Weiß)
Surface:     #f9fafb (Hell-Grau - Cards)
```

**Dark Mode:**
- Background: #1f2937
- Surface: #374151
- Text: #f9fafb

### 5.3 Typography (Mobile)

```
Display:   32px / 2rem (Semibold) - Page Titles
Headline:  24px / 1.5rem (Semibold) - Section Headers
Body:      16px / 1rem (Regular) - Main Text
Caption:   14px / 0.875rem (Regular) - Meta Info
Small:     12px / 0.75rem (Regular) - Hints
```

**Wichtig:**
- Mindestens 16px für Body Text (Lesbarkeit)
- Line-Height: 1.5 (gute Lesbarkeit)
- Font: System-Font (San Francisco iOS, Roboto Android)

---

## 6. Interaktions-Patterns (Mobile)

### 6.1 Gesten
- **Swipe Left** (auf Artikel): Entnehmen-Aktion
- **Swipe Right** (auf Artikel): Details anzeigen (optional)
- **Pull-to-Refresh**: Listen aktualisieren
- **Long-Press**: Context-Menu (Bearbeiten, Löschen)
- **Swipe-down**: Bottom Sheet schließen

### 6.2 Haptic Feedback
- Button Press: Light Haptic
- Swipe-Aktion: Medium Haptic
- Erfolg: Success Haptic (2x kurz)
- Fehler: Error Haptic (lang)

### 6.3 CRUD-Operations (Mobile)

**Create:**
- FAB oder "+" in Bottom Nav
- Wizard (3 Schritte)
- "Speichern & Nächster" für Bulk

**Read/List:**
- Infinite Scroll oder "Mehr laden"
- Pull-to-Refresh
- Search-Bar am Top (sticky)

**Update:**
- Long-Press → Context Menu → Bearbeiten
- Gleicher Wizard wie Create

**Delete/Entnehmen:**
- Swipe Left → Entnehmen-Button
- Confirmation Bottom Sheet
- Toast nach Erfolg

### 6.4 Error-Handling (Mobile)

**Validation Errors:**
- Inline unter Feld (rot)
- Shake-Animation
- Haptic Feedback (Error)

**Server Errors:**
- Toast oben (nicht Bottom, wegen Bottom Nav)
- Retry-Button in Toast

**Network Errors:**
- Offline-Indicator oben
- Queued Actions (Post-MVP)

### 6.5 Loading States

**Initial Load:**
- Skeleton Cards (shimmer effect)
- Loading Spinner für < 2 Sekunden

**Button Actions:**
- Spinner in Button
- Button disabled + "Lädt..."

**Pull-to-Refresh:**
- Native Pull-Spinner

---

## 7. Responsive Verhalten

### 7.1 Mobile-First (< 640px)
- Bottom Navigation
- Single Column Layout
- Cards Full-Width
- FAB für Hauptaktion

### 7.2 Tablet (640px - 1024px)
- Bottom Nav ODER Sidebar (optional)
- Two-Column Layout (Liste + Details)
- Cards in Grid (2 Spalten)

### 7.3 Desktop (> 1024px)
- Left Sidebar Navigation (wie VellenBase)
- Multi-Column Layout
- Tabelle statt Cards (mehr Spalten)
- Hover-States

**Breakpoints:**
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

---

## 8. Accessibility (Mobile)

### 8.1 Touch-Targets
- Minimum: 44x44px (Apple HIG)
- Empfohlen: 48x48px (Material Design)
- Abstand zwischen Targets: min. 8px

### 8.2 Kontrast
- WCAG AA: 4.5:1 (Normal Text)
- WCAG AAA: 7:1 (bevorzugt)
- Status-Colors immer mit Icon (nicht nur Farbe)

### 8.3 Screen-Reader
- Labels für alle Inputs
- ARIA-Labels für Icons
- Live-Regions für Notifications

### 8.4 Keyboard-Navigation (Desktop)
- Tab-Order logisch
- Enter/Space für Buttons
- ESC für Modals/Bottom Sheets

---

## 9. Performance (Mobile)

### 9.1 Optimierungen
- Lazy Loading (Listen)
- Image Optimization (falls Fotos Post-MVP)
- Code Splitting (NiceGUI)
- Debounce Search (300ms)

### 9.2 Feedback
- Optimistic UI Updates
- Instant Feedback (< 100ms)
- Skeleton Screens (< 1s)
- Loading Spinner (> 1s)

---

## 10. Implementierungs-Reihenfolge

### Phase 1: Mobile Core (Tag 1-4)
1. Login (Mobile)
2. Bottom Navigation
3. Dashboard (Übersicht)
4. Vorratsliste (Cards)

### Phase 2: Kern-Features (Tag 5-8)
1. Artikel erfassen (Wizard)
2. Entnehmen (Bottom Sheet)
3. Suche & Filter
4. Swipe-to-entnehmen

### Phase 3: Admin (Tag 9-10)
1. Einstellungen (Kategorien, Lagerorte)
2. Benutzer-Verwaltung
3. Gefrierzeit-Konfiguration

### Phase 4: Responsive (Tag 11-12)
1. Tablet-Layout
2. Desktop-Layout (Sidebar)
3. Touch-Gesten & Haptics
4. Dark Mode

---

## 11. Technische Prinzipien

### 11.1 NiceGUI Mobile-First
- **ui.page()** mit `viewport` meta tag
- **Responsive Grids**: ui.row(), ui.column() mit Breakpoints
- **Bottom Nav**: Custom Component (NiceGUI)
- **Bottom Sheet**: Custom Component oder Plugin
- **Native Mobile Picker**: HTML5 Input Types nutzen

### 11.2 Smart Defaults (Session-Storage)

**Implementierung:**
- NiceGUI Browser Storage (`app.storage.browser`)
- Persistiert zwischen Sessions
- Separate Namespaces pro Benutzer

**Gespeicherte Werte:**
```python
{
  "last_item_entry": {
    "timestamp": "2025-11-24T15:30:00",  # Für Zeitfenster-Check
    "item_type": "purchased_then_frozen",
    "location_id": 3,  # Tiefkühltruhe
    "category_ids": [1, 5],  # Gemüse, Garten
    "unit": "g"
  },
  "preferences": {
    "item_type_time_window": 30,  # Minuten (konfigurierbar)
    "category_time_window": 30     # Minuten (konfigurierbar)
  }
}
```

**Logik:**
1. **Artikel-Typ**:
   - Wenn `last_item_entry.timestamp` < 30 Min → `last_item_entry.item_type` vorauswählen
   - Sonst → "purchased_fresh" (Default)

2. **Lagerort**:
   - Immer `last_item_entry.location_id` vorauswählen (kein Zeitfenster)
   - Erst-Nutzung: Erster Lagerort in Liste

3. **Kategorien**:
   - Wenn `last_item_entry.timestamp` < 30 Min → `last_item_entry.category_ids` vorauswählen
   - Sonst → Leere Auswahl

4. **Einheit**:
   - Immer `last_item_entry.unit` vorauswählen
   - Default: "g"

**Nach "Speichern & Nächster":**
- `last_item_entry` wird aktualisiert
- Timestamp = jetzt
- Wizard wird geleert, aber Smart Defaults greifen sofort

### 11.3 Session-Management (Langlebige Sessions)

**Implementierung:**
- **Session Cookie**: HTTPOnly, Secure, SameSite=Lax
- **Session-Länge**:
  - Standard (ohne "Angemeldet bleiben"): 24h
  - Mit "Angemeldet bleiben": 30 Tage (konfigurierbar)
- **Remember-Me Token**:
  - Separater Token in DB (User-Tabelle)
  - Kryptografisch sicher generiert
  - Bei jedem Login erneuert
  - Kann vom Admin zurückgesetzt werden

**Session-Refresh:**
- Automatisch bei jeder Anfrage
- Sliding Expiration (Session verlängert sich bei Aktivität)

### 11.4 Progressive Web App (PWA) - Post-MVP
- Service Worker für Offline
- Add to Home Screen
- Push Notifications
- Background Sync

---

## 12. Unterschiede zu VellenBase

| Feature | VellenBase | Fuellhorn |
|---------|-----------|-----------|
| Navigation | Left Sidebar | Bottom Nav (Mobile) |
| Layout | Desktop-First | Mobile-First |
| Cards | Medium | Large (Touch) |
| Buttons | 36px | 48px (Touch) |
| Forms | Multi-Column | Single Column |
| Modals | Center Modal | Bottom Sheet |
| Actions | Click | Swipe + Tap |
| Lists | Table (10-20 rows) | Infinite Scroll |

---

## Nächste Schritte

1. ✅ UI-Konzept erstellt (Mobile-First)
2. 🔄 Mockups/Wireframes in Figma/Sketch? (optional)
3. 🔜 Prototyp mit NiceGUI (Bottom Nav + Dashboard)
4. 🔜 User Testing mit Familie
