# UI und visuelles Design

Dieses Dokument beschreibt das visuelle Design-System für Füllhorn (Solarpunk Theme).

**Wichtig:** Die maßgebliche Quelle ist `ci-guidelines/fuellhorn-ci-guidelines.pdf`.

---

## 1. Design-Philosophie (Solarpunk)

Füllhorn folgt einer **Solarpunk-Ästhetik** – einer hoffnungsvollen Zukunftsvision, die Harmonie zwischen Technologie und Natur verkörpert.

### Kernwerte

| Wert | Bedeutung |
|------|-----------|
| **Organisch** | Geschwungene Linien, weiche Formen, natürliche Kurven |
| **Warm** | Erdige Grüntöne, sonniges Gold, einladende Farbwelt |
| **Zyklisch** | Der Kreislauf-Gedanke durchzieht das gesamte Design |
| **Hoffnungsvoll** | Optimistisch, zukunftsweisend, lebensbejahend |

### UI-Grundsätze

- **Warme Hintergründe:** Cream (#FAF7F0) statt kaltem Weiß
- **Weiche Schatten:** Sanfte Schatten mit geringer Opazität
- **Abgerundete Ecken:** 12–16px für Karten, 20px für Chips
- **Status über Farbe:** Border-Akzente statt greller Badges
- **Organische Akzente:** Dezente botanische Elemente wo passend

---

## 2. Farbpalette

### Primärfarben – Grün

| Name | Hex | CSS-Variable | Verwendung |
|------|-----|--------------|------------|
| Fern Green | `#4A7C59` | `--sp-fern` | Hauptfarbe, Logo, Headlines |
| Fern Dark | `#3D6A4A` | `--sp-fern-dark` | Hover-States |
| Fern Light | `#5A8C69` | `--sp-fern-light` | Highlights |
| Moss | `#5C7F5C` | `--sp-moss` | Sekundär, Subheadlines |
| Leaf | `#7CB342` | `--sp-leaf` | Akzent, Status "OK" |
| Sage | `#9CAF88` | `--sp-sage` | Borders, dezente Elemente |
| Sage Light | `#B8C9A8` | `--sp-sage-light` | Helle Borders |

### Sekundärfarben – Erde & Gold

| Name | Hex | CSS-Variable | Verwendung |
|------|-----|--------------|------------|
| Amber | `#E6A832` | `--sp-amber` | Füllhorn, Akzente, CTA |
| Amber Dark | `#D49A28` | `--sp-amber-dark` | Hover für Amber |
| Honey | `#DAA520` | `--sp-honey` | Gold, Premium-Elemente |
| Terracotta | `#C17F59` | `--sp-terracotta` | Warme Akzente, Lagerort-Icon |

### Neutrale Farben

| Name | Hex | CSS-Variable | Verwendung |
|------|-----|--------------|------------|
| Cream | `#FAF7F0` | `--sp-cream` | Haupthintergrund |
| Oat | `#F5F0E6` | `--sp-oat` | Karten-Hintergrund |
| Parchment | `#EDE8DB` | `--sp-parchment` | Sekundärer Hintergrund |
| Stone | `#A39E93` | `--sp-stone` | Muted Text, Platzhalter |
| Stone Dark | `#7D796F` | `--sp-stone-dark` | Dunklerer Text |
| Charcoal | `#3D3D3D` | `--sp-charcoal` | Haupttext |

### Status-Farben

| Status | Name | Hex | CSS-Variable |
|--------|------|-----|--------------|
| OK | Leaf | `#7CB342` | `--sp-status-ok` |
| Warning | Amber | `#E6A832` | `--sp-status-warning` |
| Critical | Coral | `#E07A5F` | `--sp-status-critical` |
| Info | Water | `#5BA3C6` | `--sp-status-info` |

---

## 3. Typografie

### Schriftarten

| Typ | Font | Fallback | Verwendung |
|-----|------|----------|------------|
| Headlines | Cormorant Garamond | Georgia, serif | Überschriften, Logo-Wortmarke |
| Body | Nunito | system-ui, sans-serif | Fließtext, UI-Elemente |

**CSS-Variablen:**
```css
--sp-font-display: 'Cormorant Garamond', Georgia, serif;
--sp-font-body: 'Nunito', system-ui, sans-serif;
```

### Schriftgrößen

| Element | Größe | Font | Farbe |
|---------|-------|------|-------|
| H1 – Seitentitel | 28–36px | Cormorant Garamond, Bold | Fern Green |
| H2 – Abschnitt | 22–28px | Cormorant Garamond, Bold | Moss |
| H3 – Unterabschnitt | 18–22px | Nunito, Semibold | Fern Green |
| Body | 14–16px | Nunito, Regular | Charcoal |
| Small / Caption | 12–14px | Nunito, Regular | Stone |

### Tailwind/Quasar Klassen

| Klasse | Verwendung |
|--------|------------|
| `text-h4`, `text-h5`, `text-h6` | Überschriften |
| `text-base` | Normaler Text |
| `text-subtitle1` | Untertitel |
| `text-body2` | Sekundärer Text |
| `text-sm`, `text-xs` | Klein, Labels |
| `font-bold`, `font-semibold`, `font-medium` | Gewichte |

---

## 4. Logo-Verwendung

### Symbolik

- **Kreisbogen (Grün):** Der Kreislauf – Wachstum, Ernte, Vorrat, Verbrauch
- **Füllhorn (Gold):** Überfluss, Ernte, Nahrung
- **Früchte:** Vielfalt der Lebensmittel
- **Blatt:** Leben, Wachstum, Frische

### Logo-Varianten

| Variante | Verwendung | Datei |
|----------|------------|-------|
| Vollfarbe | Helle Hintergründe | `fuellhorn-logo-color.svg` |
| Dark Mode | Dunkle Hintergründe | `fuellhorn-logo-dark.svg` |
| Monochrom Grün | Einfarb-Druck | `fuellhorn-logo-mono-green.svg` |
| Monochrom Weiß | Dunkle Einfarb | `fuellhorn-logo-mono-white.svg` |
| Icon | App, Favicon | `fuellhorn-icon-simple.svg` |

**Pfad:** `ci-guidelines/fuellhorn-logo-export/`

### Regeln

- **Mindestgröße:** 32px (< 48px: Icon-Variante verwenden)
- **Schutzzone:** Breite eines Früchte-Elements

**Nicht erlaubt:**
- Logo rotieren, spiegeln oder verzerren
- Andere als definierte Farben verwenden
- Horn in Grün darstellen
- Elemente hinzufügen oder entfernen

---

## 5. UI-Komponenten

### Custom Components

| Komponente | Datei | Beschreibung |
|------------|-------|--------------|
| Bottom Navigation | `app/ui/components/bottom_nav.py` | Mobile Navigation, 3 Items, sticky unten |
| Bottom Sheet | `app/ui/components/bottom_sheet.py` | Modal-Dialog von unten |
| Item Card | `app/ui/components/item_card.py` | Artikel-Karte mit Status-Border |
| Expiry Badge | `app/ui/components/expiry_badge.py` | Haltbarkeits-Badge |
| Unit Chips | `app/ui/components/unit_chips.py` | Einheiten-Auswahl |
| Category Chips | `app/ui/components/category_chips.py` | Kategorie-Auswahl |
| Location Chips | `app/ui/components/location_chips.py` | Lagerort-Auswahl |
| Item Type Chips | `app/ui/components/item_type_chips.py` | Artikel-Typ Auswahl |
| User Dropdown | `app/ui/components/user_dropdown.py` | Benutzer-Menü im Header |

### NiceGUI Standard-Komponenten

**Layout:**
- `ui.row()` – Horizontales Flex-Layout
- `ui.column()` – Vertikales Flex-Layout
- `ui.card()` – Container mit Schatten
- `ui.separator()` – Trennlinie

**Formulare:**
- `ui.input()` – Textfelder (props: `outlined`, `autofocus`)
- `ui.number()` – Zahlen (props: `min`, `max`, `step`)
- `ui.select()` – Dropdown
- `ui.date()` – Datumseingabe
- `ui.checkbox()`, `ui.switch()` – Toggles

**Buttons:**
- `ui.button()` – Props: `flat`, `round`, `outlined`, `no-caps`, `dense`
- Farben: `primary`, `secondary`, `positive`, `negative`

### Button-Stile

| Typ | CSS-Klasse | Beschreibung |
|-----|------------|--------------|
| Primär | `sp-btn-primary` | Fern Green Hintergrund, weiß |
| Sekundär | `sp-btn-secondary` | Transparent, Fern Green Border |
| Akzent/CTA | `sp-btn-accent` | Amber Hintergrund |
| Danger | `sp-btn-danger` | Coral Hintergrund |
| Ghost | `sp-btn-ghost` | Transparent, Fern Green Text |

### Chip-Stile

**Unit Chips (einfach):**
- Inaktiv: `bg-gray-200 text-gray-800`
- Aktiv: `bg-primary text-white`

**Category/Location/ItemType Chips (mit Ring-Dot):**
- Inaktiv: Grauer Hintergrund, farbiger Border, leerer Ring
- Aktiv: Volle Hintergrundfarbe, gefüllter Ring

---

## 6. CSS-Theme Referenz

**Datei:** `ci-guidelines/solarpunk-theme.css`

### Einbindung

```html
<link href="/static/solarpunk-theme.css" rel="stylesheet">
```

### CSS-Variablen (Auswahl)

```css
/* Farben */
--sp-fern: #4A7C59;
--sp-amber: #E6A832;
--sp-cream: #FAF7F0;

/* Schatten */
--sp-shadow-sm: 0 1px 3px rgba(74, 124, 89, 0.08);
--sp-shadow-md: 0 4px 12px rgba(74, 124, 89, 0.12);
--sp-shadow-lg: 0 8px 24px rgba(74, 124, 89, 0.16);

/* Border Radius */
--sp-radius-sm: 8px;
--sp-radius-md: 12px;
--sp-radius-lg: 16px;
--sp-radius-xl: 20px;
--sp-radius-full: 9999px;

/* Quasar Overrides */
--q-primary: #4A7C59;
--q-secondary: #9CAF88;
--q-accent: #E6A832;
--q-positive: #7CB342;
--q-negative: #E07A5F;
```

### Utility-Klassen

**Hintergrund:**
`bg-cream`, `bg-oat`, `bg-parchment`, `bg-fern`, `bg-amber`

**Text:**
`text-fern`, `text-fern-dark`, `text-amber`, `text-stone`, `text-charcoal`

**Border:**
`border-sage`, `border-sage-light`, `border-fern`

**Radius:**
`rounded-sp-sm`, `rounded-sp-md`, `rounded-sp-lg`, `rounded-sp-xl`, `rounded-sp-full`

**Schatten:**
`shadow-sp-sm`, `shadow-sp-md`, `shadow-sp-lg`

**Font:**
`font-display`, `font-body`

---

## 7. Material Icons

### Navigation
`home`, `add_circle`, `inventory_2`, `dashboard`, `arrow_back`

### Admin/Settings
`category`, `place`, `people`, `settings`, `person`

### Aktionen
`add`, `edit`, `delete`, `close`, `save`, `logout`, `check_circle`, `remove_circle_outline`

### Anzeige
`scale`, `event`, `notes`, `chevron_right`, `search_off`, `kitchen`

---

## 8. Mobile-First & Accessibility

### Touch-Targets

| Element | Mindestgröße |
|---------|--------------|
| Buttons | 48×48px |
| Icons (normal) | 24px |
| Icons (leer-Status) | 48px |
| Chip min-height | 44px |
| Bottom Nav | 56px Höhe |

### Abstände

| Verwendung | Klasse |
|------------|--------|
| Card-Padding | `p-4` |
| Element-Abstand | `gap-2`, `gap-3` |
| Section-Abstand | `mb-4`, `my-4` |

### WCAG-Kontrast

- **WCAG AA:** 4.5:1 (Normal Text)
- **WCAG AAA:** 7:1 (bevorzugt)
- Status-Colors immer mit Icon (nicht nur Farbe)

### Responsive Breakpoints

| Gerät | Breite |
|-------|--------|
| Mobile | < 640px |
| Tablet | 640px – 1024px |
| Desktop | > 1024px |

---

## Referenzen

- [ci-guidelines/fuellhorn-ci-guidelines.pdf](../../ci-guidelines/fuellhorn-ci-guidelines.pdf) – Vollständige CI-Guidelines
- [ci-guidelines/solarpunk-theme.css](../../ci-guidelines/solarpunk-theme.css) – CSS-Theme
- [ci-guidelines/fuellhorn-logo-export/](../../ci-guidelines/fuellhorn-logo-export/) – Logo-Dateien
- [ci-guidelines/fuellhorn-icons/](../../ci-guidelines/fuellhorn-icons/) – Icon-Set
