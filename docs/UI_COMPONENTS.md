# Fuellhorn UI-Komponenten

Diese Übersicht listet alle UI-Komponenten für Designer zum Stylen.

---

## Custom Components (eigene Widgets)

| Komponente | Datei | Beschreibung |
|------------|-------|--------------|
| **Bottom Navigation** | `app/ui/components/bottom_nav.py` | Mobile Navigation, 3 Items (Übersicht, Erfassen, Vorrat), sticky am unteren Rand |
| **Bottom Sheet** | `app/ui/components/bottom_sheet.py` | Modal-Dialog für Artikel-Details, von unten einblendend |
| **Item Card** | `app/ui/components/item_card.py` | Artikel-Karte mit farbiger Status-Border links |
| **Expiry Badge** | `app/ui/components/expiry_badge.py` | Farbcodiertes Haltbarkeits-Badge (Tage bis Ablauf) |
| **Unit Chips** | `app/ui/components/unit_chips.py` | Einheiten-Auswahl (g, kg, ml, l, Stück, Packung) |
| **Category Chips** | `app/ui/components/category_chips.py` | Kategorie-Auswahl mit dynamischen Farben |
| **Location Chips** | `app/ui/components/location_chips.py` | Lagerort-Auswahl mit dynamischen Farben |
| **Item Type Chips** | `app/ui/components/item_type_chips.py` | Artikel-Typ Auswahl (5 Typen) |
| **User Dropdown** | `app/ui/components/user_dropdown.py` | Benutzer-Menü im Header |
| **Mobile Page Container** | `app/ui/components/bottom_nav.py` | Standard-Wrapper mit max-width und Padding |

---

## NiceGUI Standard-Komponenten

### Layout

| Komponente | Verwendung | Häufige Klassen |
|------------|------------|-----------------|
| `ui.row()` | Horizontales Flex-Layout | `w-full items-center justify-between gap-2` |
| `ui.column()` | Vertikales Flex-Layout | `flex-1 gap-2 p-4` |
| `ui.card()` | Container mit Schatten | `w-full mb-2` |
| `ui.separator()` | Horizontale Trennlinie | `my-4` |
| `ui.element("div")` | Custom DIV (z.B. Farb-Dots) | Inline-Styles für Farben |

### Formulare

| Komponente | Props | Verwendung |
|------------|-------|------------|
| `ui.input()` | `outlined`, `autofocus`, `placeholder` | Textfelder, Suche |
| `ui.number()` | `min`, `max`, `step`, `outlined` | Mengen, Zahlen |
| `ui.checkbox()` | - | "Angemeldet bleiben" |
| `ui.switch()` | - | "Entnommene anzeigen" |
| `ui.select()` | `outlined` | Sortierung, Filter |
| `ui.date()` | - | Datumseingabe |
| `ui.color_input()` | - | Farb-Picker für Kategorien/Orte |

### Buttons & Navigation

| Komponente | Props | Verwendung |
|------------|-------|------------|
| `ui.button()` | `flat`, `round`, `outlined`, `no-caps`, `dense`, `disabled` | Alle Aktionen |
| `ui.dialog()` | `position=bottom`, `persistent`, `full-width` | Bottom Sheets, Modals |
| `ui.menu()` | - | Dropdown-Menüs |
| `ui.menu_item()` | `icon`, `on_click` | Menü-Einträge |

**Button-Farben:** `primary`, `secondary`, `positive`, `negative`, `gray-7`

### Anzeige

| Komponente | Props | Verwendung |
|------------|-------|------------|
| `ui.label()` | - | Text-Anzeige (mit Tailwind-Klassen) |
| `ui.icon()` | `size` (24px, 48px, 64px) | Material Design Icons |
| `ui.badge()` | `color`, `outline` | Kategorie-Tags, Status |
| `ui.notify()` | `type` (warning, positive, negative) | Toast-Benachrichtigungen |

---

## Farb-System

### Status-Farben

| Status | Tailwind | Hex | Verwendung |
|--------|----------|-----|------------|
| Kritisch | `red-500` | #EF4444 | Ablauf < 3 Tage |
| Warnung | `orange-500` | #F97316 | Ablauf 3-7 Tage |
| Warnung (alt) | `yellow-500` | #EAB308 | Badge-Hintergrund |
| OK | `green-500` | #22C55E | Ablauf > 7 Tage |
| Primary | - | Theme | Hauptaktionen, aktive Nav |

### Graustufen

| Verwendung | Klasse |
|------------|--------|
| Hintergrund | `bg-white`, `bg-gray-100`, `bg-gray-200` |
| Text primär | `text-gray-900` |
| Text sekundär | `text-gray-600`, `text-gray-500` |
| Borders | `border-gray-200` |
| Hover | `hover:bg-gray-50`, `hover:bg-gray-300` |

### Dynamische Farben

Kategorien und Lagerorte haben benutzerdefinierte Hex-Farben mit automatischer WCAG-Kontrastberechnung für Text (weiß oder dunkel).

---

## Typography

### Überschriften

| Klasse | Verwendung |
|--------|------------|
| `text-h4` | Seitentitel |
| `text-h5` | Abschnittstitel |
| `text-h6` | Card-Titel |

### Fließtext

| Klasse | Verwendung |
|--------|------------|
| `text-base` | Normaler Text |
| `text-subtitle1` | Untertitel |
| `text-body2` | Sekundärer Text |
| `text-sm` | Klein |
| `text-xs` | Sehr klein (Labels, Badges) |

### Font-Weights

| Klasse | Wert |
|--------|------|
| `font-bold` | 700 |
| `font-semibold` | 600 |
| `font-medium` | 500 |

---

## Material Icons

### Navigation
`home`, `add_circle`, `inventory_2`, `dashboard`, `arrow_back`

### Admin/Settings
`category`, `place`, `people`, `settings`, `person`

### Aktionen
`add`, `edit`, `delete`, `close`, `save`, `logout`
`check_circle`, `remove_circle_outline`
`arrow_upward`, `arrow_downward`

### Anzeige
`scale`, `event`, `notes`, `chevron_right`, `search_off`, `kitchen`

---

## Design-Richtlinien

### Mobile-First

- **Max-Width:** 800px für Seiteninhalte
- **Touch-Targets:** mindestens 48×48px
- **Bottom Navigation:** 56px Höhe, fixiert unten
- **Padding unten:** 72px (56px Nav + 16px Abstand)

### Komponenten-Größen

| Element | Größe |
|---------|-------|
| Bottom Nav | 56px Höhe |
| Touch Button | min. 48×48px |
| Icons (normal) | 24px |
| Icons (leer-Status) | 48px |
| Icons (Titel) | 64px |
| Chip min-height | 44px |

### Abstände (Spacing)

| Verwendung | Klasse |
|------------|--------|
| Card-Padding | `p-4` |
| Element-Abstand | `gap-2`, `gap-3` |
| Section-Abstand | `mb-4`, `my-4` |
| Inline-Abstand | `px-2`, `py-1` |

---

## Seiten-Übersicht

| Seite | Route | Hauptkomponenten |
|-------|-------|------------------|
| Login | `/login` | Input, Checkbox, Button, Card |
| Dashboard | `/dashboard` | Bottom Nav, Cards, Icons, Labels |
| Vorrat | `/items` | Item Cards, Search, Filter, Chips |
| Erfassen | `/items/add` | 3-Step Wizard, alle Chip-Gruppen |
| Artikel bearbeiten | `/items/{id}/edit` | Formular wie Erfassen |
| Kategorien | `/admin/categories` | Dialog, Color Picker, Liste |
| Lagerorte | `/admin/locations` | Dialog, Color Picker, Liste |
| Benutzer | `/admin/users` | Cards, Badges, Icons |

---

## Chip-Komponenten Detail

### Gemeinsames Styling

Alle Chips verwenden:
- Min-Height: 44px
- Rounded corners
- Cursor pointer
- Transition für Hover/Active

### Unit Chips

Einfache Farbwechsel ohne Indikatoren:
- **Selected:** `bg-primary text-white`
- **Default:** `bg-gray-200 text-gray-800 hover:bg-gray-300`

### Category/Location/ItemType Chips

Mit Ring-Dot Indikator (Radio-Button-ähnlich):
- **Selected:** Volle Hintergrundfarbe, gefüllter Ring-Dot
- **Default:** Grauer Hintergrund (`#F3F4F6`), farbiger Border, leerer Ring

Ring-Dot Styling:
```css
/* Gefüllt */
background: radial-gradient(circle, <color> 35%, white 35%);

/* Leer */
background: white;
border: 2px solid <color>;
```

---

## Bottom Sheet Detail

### Struktur

```
┌─────────────────────────────┐
│  ══════════════  (Handle)   │  ← Zieh-Indikator
├─────────────────────────────┤
│  Produktname           [X]  │  ← Header mit Close
├─────────────────────────────┤
│  🏷️ Menge: 500g             │
│  📍 Lagerort: Kühlschrank   │  ← Info-Zeilen
│  📅 Haltbar bis: 15.12.     │
│  📝 Notizen: ...            │
├─────────────────────────────┤
│  [Entnehmen] [Entnommen]    │  ← Action Buttons
│  [Bearbeiten]               │
└─────────────────────────────┘
```

### Styling

- `rounded-t-2xl` für obere Ecken
- Separator zwischen Sections
- Buttons: 48px min-height
- Position: `bottom` im Dialog

---

## Item Card Detail

### Struktur

```
┌────┬──────────────────────────┐
│ 🟢 │  Produktname             │
│    │  500g · Kühlschrank      │
│    │  [Gemüse] [Bio]          │
└────┴──────────────────────────┘
  ↑
  Status-Border (4px, farbig)
```

### Status-Border Farben

| Status | Border-Farbe | Emoji |
|--------|--------------|-------|
| Kritisch (< 3 Tage) | `red-500` | 🔴 |
| Warnung (3-7 Tage) | `orange-500` | 🟡 |
| OK (> 7 Tage) | `green-500` | 🟢 |
