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

| Typ | Haltbarkeit |
|-----|-------------|
| `purchased_fresh` | MHD |
| `purchased_frozen` | MHD |
| `purchased_then_frozen` | Einfrierdatum + Gefrierzeit |
| `homemade_frozen` | Produktionsdatum + Gefrierzeit |
| `homemade_preserved` | Produktionsdatum + Haltbarkeit |


### Rollen (2 Stück)

- **admin** - Voller Zugriff (Benutzer, Kategorien, Lagerorte)
- **user** - Items lesen/schreiben

---

