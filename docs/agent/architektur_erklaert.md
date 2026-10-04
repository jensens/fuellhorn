## Architektur

## Mobile-First Entwicklung

**WICHTIG**: Fuellhorn ist für Smartphone-Nutzung optimiert!

- **Touch-optimierte Buttons**: min. 48x48px
- **Bottom Navigation** statt Sidebar
- **Card Layout** statt Tabellen
- **Bottom Sheets** statt Center-Modals

**Details:** [ui_und_design.md](ui_und_design.md)


### 3-Schichten-Modell

1. **Models** (`app/models/`) - SQLModel Entitäten - code gilt als referenz
2. **Services** (`app/services/`) - Business Logic
3. **UI** (`app/ui/`) - NiceGUI Presentation

**Regeln:**
- Keine Business-Logic in UI-Code
- Keine UI-Code in Services
- Relative Imports innerhalb von `app/`

**Details:** [tech_stack.md](tech_stack.md)

### 5 Artikel-Typen

| Typ | Erfasste Daten (Label) | Bedeutung von `best_before_date` | Haltbarkeit |
|-----|------------------------|----------------------------------|-------------|
| `purchased_fresh` | MHD | MHD der Packung | MHD |
| `purchased_frozen` | MHD | MHD der Packung | MHD |
| `purchased_then_frozen` | Eingefroren am | = `freeze_date` (Service spiegelt, kein eigenes Datum) | Einfrierdatum + Gefrierzeit (FROZEN) |
| `homemade_frozen` | Hergestellt am, Eingefroren am | Herstellungsdatum | Einfrierdatum + Gefrierzeit (FROZEN) |
| `homemade_preserved` | Hergestellt am | Herstellungsdatum | Herstellungsdatum + Haltbarkeit (AMBIENT) |

`best_before_date` ist überladen (MHD bzw. Herstellungsdatum). Beschriftungen überall gleich: "MHD", "Hergestellt am", "Eingefroren am" (Wizard, Edit-View, Bottom-Sheet; Issue #387). `freeze_date` ist Pflicht für `purchased_then_frozen` und `homemade_frozen`; die Reihenfolge Herstellung ≤ Einfrieren wird nur bei `homemade_frozen` geprüft (`app/ui/validation/wizard_validation.py`, `item_service.validate_item_data`).


### Rollen (2 Stück)

- **admin** - Voller Zugriff (Benutzer, Kategorien, Lagerorte)
- **user** - Items lesen/schreiben

---

