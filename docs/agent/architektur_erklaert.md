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

### Kategorie-Hierarchie (eine Ebene)

`Category.parent_id` bildet genau eine Ebene: Gruppen (z.B. "Fleisch") und ihre Kinder ("Rindfleisch", "Wurst").
Gruppen sind beim Erfassen nicht wählbar; nur Blätter tragen Artikel. Die Regeln setzt
`category_service._validate_parent` durch (Issue #395):

- Eine Kategorie kann nicht sich selbst zugeordnet werden; der Parent muss selbst Top-Level sein.
- Eine Kategorie mit Unterkategorien kann kein Kind werden; eine Kategorie mit Artikeln keine Gruppe.
- Admin-UI: Liste gruppiert (Badge "Gruppe", Kinder eingerückt), Parent-Auswahl im Dialog, Hoch/Runter nur
  innerhalb der Geschwister.

**Haltbarkeit wird vererbt, nicht ausgeblendet:** Ein Kind ohne eigenen `CategoryShelfLife`-Eintrag nutzt den
seiner Gruppe (`shelf_life_service.get_shelf_life_with_fallback`, Index-Pfad in `expiry_service`). Deshalb bleibt
die Haltbarkeits-Eingabe für Gruppen im Admin sichtbar: Sie ist der Default für alle Kinder. Der Wizard bietet
Kinder an, deren Haltbarkeit für die Lagerart aus der Gruppe kommt (`get_categories_for_item_type`). Im
Vorratsfilter steht ein Gruppen-Chip für alle Kinder (`category_service.expand_category_filter`).


### Rollen (2 Stück)

- **admin** - Voller Zugriff (Benutzer, Kategorien, Lagerorte)
- **user** - Items lesen/schreiben

---

### Zeitstempel

Alle Zeitstempel sind naive lokale Zeit (`datetime.now()`): `created_at`, `last_login`,
Smart-Default-Zeitfenster. Entscheidung (Issue #401): keine Migration auf timezone-aware Werte, weil eine
Instanz genau einen Haushalt in einer Zeitzone bedient. Dafür muss der Prozess in der Zeitzone der Nutzer
laufen (`TZ`, siehe docs/deployment/docker.md); Tests, die Zeit vergleichen, nutzen `freezegun` oder
injizieren `now`.

### Datenbankzugriff

Engine und Sessions sind synchron (`app/database.py`, SQLModel `create_engine`/`Session`); Seiten und
Event-Handler rufen die Services mit `with next(get_session()) as session:` auf. NiceGUI führt diese
Aufrufe im Event-Loop aus, jede Abfrage blockiert also kurz alle Clients. Entscheidung (Issue #195): kein
Umbau auf `AsyncEngine`/`AsyncSession` – eine Instanz bedient einen Haushalt, SQLite liegt lokal, die
Seiten laufen seit #393 mit konstant wenigen Abfragen; der Umbau würde alle Services, Seiten und Tests
erfassen. Wird Latenz einmal messbar (PostgreSQL über das Netz, viele gleichzeitige Nutzer), ist der
günstige Schritt `run.io_bound(...)` um die DB-Aufrufe der betroffenen Seite, nicht die Async-Engine.
