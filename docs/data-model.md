# Fuellhorn - Datenmodell

## Übersicht

Dieses Dokument beschreibt das Datenmodell für die Fuellhorn-Anwendung (MVP Version 1.0).

## Entitäten & Beziehungen

### Hauptentitäten

1. **User** - Benutzer des Systems
2. **Item** - Vorratsartikel
3. **Category** - Kategorien/Tags für Artikel
4. **Location** - Lagerorte
5. **FreezeTimeConfig** - Konfiguration von Gefrierzeiten pro Kategorie
6. **AuditLog** - Audit-Protokoll für alle Aktionen
7. **ItemCategory** - Zuordnung Item ↔ Category (Many-to-Many)

---

## Detaillierte Entitätsbeschreibung

### 1. User (Benutzer)

Speichert Benutzerkonten und deren Rollen.

**Attribute:**
- `id` (UUID/Integer, PK): Eindeutige Benutzer-ID
- `username` (String, unique, required): Benutzername (für Login)
- `email` (String, unique, required): E-Mail-Adresse
- `password_hash` (String, required): Gehashtes Passwort (bcrypt/Argon2)
- `role` (Enum: 'admin', 'user', required): Rolle des Benutzers
- `is_active` (Boolean, default: true): Ist der Benutzer aktiv?
- `failed_login_attempts` (Integer, default: 0): Anzahl fehlgeschlagener Login-Versuche
- `locked_until` (Timestamp, nullable): Account gesperrt bis (nach zu vielen fehlgeschlagenen Logins)
- `created_at` (Timestamp): Erstellungszeitpunkt
- `updated_at` (Timestamp): Letzte Änderung

**Geschäftsregeln:**
- Username muss eindeutig sein (Case-insensitive)
- Email muss eindeutig sein
- Passwort wird niemals im Klartext gespeichert
- Nach X fehlgeschlagenen Login-Versuchen wird Account für Y Minuten gesperrt (konfigurierbar)

**Beziehungen:**
- 1 User → N Items (erfasst)
- 1 User → N AuditLogs (verursacht)

---

### 2. Item (Vorratsartikel)

Speichert alle Vorratsartikel mit ihren Details.

**Attribute:**
- `id` (UUID/Integer, PK): Eindeutige Artikel-ID
- `product_name` (String, required): Produktname
- `item_type` (Enum, required): Artikel-Typ
  - `purchased_fresh` - Gekauft (nicht gefroren)
  - `purchased_frozen` - Gekauft (bereits gefroren)
  - `purchased_then_frozen` - Gekauft und eingefroren
  - `homemade_frozen` - Selbst hergestellt (gefroren)
  - `homemade_preserved` - Selbst hergestellt (eingemacht)
- `quantity` (Decimal, required): Menge (> 0)
- `unit` (String, required): Einheit (z.B. "g", "ml", "Stück")
- `location_id` (Integer, FK → Location, required): Lagerort
- `best_before_date` (Date, nullable): MHD (nur bei gekauften Artikeln)
- `production_date` (Date, nullable): Produktions-/Erntedatum (bei selbst hergestellten)
- `freeze_date` (Date, nullable): Einfrierdatum (bei nachträglich eingefrorenen)
- `barcode` (String, nullable): Barcode (Post-MVP)
- `notes` (Text, nullable): Notizen (z.B. "blanchiert")
- `is_withdrawn` (Boolean, default: false): Wurde vollständig entnommen? (Soft-Delete)
- `withdrawn_at` (Timestamp, nullable): Wann wurde entnommen?
- `withdrawn_by` (Integer, FK → User, nullable): Wer hat entnommen?
- `created_at` (Timestamp): Erfassungszeitpunkt
- `created_by` (Integer, FK → User): Wer hat erfasst?
- `updated_at` (Timestamp): Letzte Änderung
- `updated_by` (Integer, FK → User, nullable): Wer hat zuletzt geändert?

**Berechnete Felder (nicht in DB gespeichert):**
- `expiry_date` (Date): Berechnetes Ablaufdatum basierend auf item_type
- `days_until_expiry` (Integer): Tage bis zum Ablauf
- `expiry_status` (Enum): 'critical' (< 3 Tage), 'warning' (< 7 Tage), 'ok'

**Geschäftsregeln:**
- `product_name` min. 2 Zeichen
- `quantity` muss > 0 sein
- Abhängig von `item_type` sind verschiedene Datumsfelder relevant:
  - `purchased_fresh`: `best_before_date` erforderlich
  - `purchased_frozen`: `best_before_date` erforderlich
  - `purchased_then_frozen`: `freeze_date` erforderlich, `best_before_date` optional
  - `homemade_frozen`: `production_date` erforderlich
  - `homemade_preserved`: `production_date` erforderlich

**Beziehungen:**
- N Items → 1 Location
- N Items → 1 User (created_by)
- N Items → 1 User (updated_by, nullable)
- N Items → 1 User (withdrawn_by, nullable)
- N Items ↔ M Categories (via ItemCategory)

---

### 3. Category (Kategorie/Tag)

Speichert Kategorien/Tags für die Klassifizierung von Artikeln.

**Attribute:**
- `id` (Integer, PK): Eindeutige Kategorie-ID
- `name` (String, unique, required): Kategoriename (z.B. "Getränke", "Fleisch")
- `color` (String, nullable): Farbcode für UI (z.B. "#FF5733")
- `freeze_time_months` (Integer, nullable): Standard-Gefrierzeit in Monaten für diese Kategorie
- `created_at` (Timestamp): Erstellungszeitpunkt
- `created_by` (Integer, FK → User): Wer hat erstellt?

**Geschäftsregeln:**
- Name muss eindeutig sein (Case-insensitive)
- Flache Struktur (keine Hierarchie im MVP)
- Nur Admins können Kategorien erstellen/ändern/löschen

**Beziehungen:**
- N Categories ↔ M Items (via ItemCategory)
- 1 Category → N FreezeTimeConfigs (Post-MVP: feinere Granularität)

---

### 4. Location (Lagerort)

Speichert verfügbare Lagerorte.

**Attribute:**
- `id` (Integer, PK): Eindeutige Lagerort-ID
- `name` (String, unique, required): Name des Lagerorts (z.B. "Tiefkühltruhe")
- `location_type` (Enum, required): Typ des Lagerorts
  - `frozen` - Gefroren
  - `chilled` - Gekühlt
  - `ambient` - Normal (Raumtemperatur)
- `description` (Text, nullable): Beschreibung
- `is_active` (Boolean, default: true): Ist der Lagerort aktiv?
- `created_at` (Timestamp): Erstellungszeitpunkt
- `created_by` (Integer, FK → User): Wer hat erstellt?

**Geschäftsregeln:**
- Name muss eindeutig sein
- `location_type` beeinflusst Haltbarkeitsberechnung
- Nur Admins können Lagerorte erstellen/ändern
- Lagerorte können nicht gelöscht werden, wenn noch Artikel zugeordnet sind (oder nur deaktiviert via `is_active`)

**Beziehungen:**
- 1 Location → N Items

---

### 5. FreezeTimeConfig (Gefrierzeit-Konfiguration)

Speichert konfigurierbare Gefrierzeiten pro Kategorie und Typ.

**Attribute:**
- `id` (Integer, PK): Eindeutige ID
- `category_id` (Integer, FK → Category, nullable): Kategorie (wenn null = Standardwert)
- `item_type` (Enum): Artikel-Typ (siehe Item.item_type)
- `freeze_time_months` (Integer, required): Gefrierzeit in Monaten
- `description` (Text, nullable): Beschreibung/Hinweise
- `created_at` (Timestamp): Erstellungszeitpunkt
- `created_by` (Integer, FK → User): Wer hat erstellt?
- `updated_at` (Timestamp): Letzte Änderung

**Geschäftsregeln:**
- Kombination aus `category_id` und `item_type` muss eindeutig sein
- Wenn `category_id` null: Standardwert für alle Artikel dieses Typs ohne spezifische Kategorie
- Nur Admins können konfigurieren

**Beispieldaten:**
```
category_id | item_type              | freeze_time_months | description
------------|------------------------|--------------------|--------------
1 (Fleisch) | purchased_then_frozen  | 6                  | Rohes Fleisch
1 (Fleisch) | homemade_frozen        | 3                  | Gekochtes Fleisch
2 (Gemüse)  | purchased_then_frozen  | 12                 | Gemüse blanchiert
2 (Gemüse)  | homemade_frozen        | 12                 | Gartengemüse
NULL        | purchased_then_frozen  | 3                  | Standard-Gefrierzeit
NULL        | homemade_frozen        | 3                  | Standard-Gefrierzeit
NULL        | homemade_preserved     | 12                 | Standard eingemacht
```

**Beziehungen:**
- N FreezeTimeConfigs → 1 Category (nullable)

---

### 6. ItemCategory (Zuordnung Item ↔ Category)

Many-to-Many Zuordnungstabelle zwischen Items und Categories.

**Attribute:**
- `id` (Integer, PK): Eindeutige ID
- `item_id` (Integer, FK → Item, required): Artikel
- `category_id` (Integer, FK → Category, required): Kategorie
- `created_at` (Timestamp): Zuordnungszeitpunkt

**Geschäftsregeln:**
- Kombination aus `item_id` und `category_id` muss eindeutig sein
- Ein Artikel kann mehrere Kategorien haben
- Eine Kategorie kann mehreren Artikeln zugeordnet sein

**Beziehungen:**
- N ItemCategory → 1 Item
- N ItemCategory → 1 Category

---

### 7. AuditLog (Audit-Protokoll)

Speichert alle wichtigen Aktionen für Nachvollziehbarkeit und Sicherheit.

**Attribute:**
- `id` (Integer, PK): Eindeutige Log-ID
- `timestamp` (Timestamp, required): Zeitpunkt der Aktion
- `user_id` (Integer, FK → User, nullable): Wer hat die Aktion durchgeführt? (nullable für System-Aktionen)
- `action` (String, required): Art der Aktion (z.B. "login", "logout", "item_created", "item_withdrawn")
- `entity_type` (String, nullable): Typ der betroffenen Entität (z.B. "Item", "User", "Category")
- `entity_id` (Integer, nullable): ID der betroffenen Entität
- `details` (JSON/Text, nullable): Zusätzliche Details (z.B. geänderte Felder)
- `ip_address` (String, nullable): IP-Adresse des Benutzers
- `user_agent` (String, nullable): Browser/Client-Information

**Geschäftsregeln:**
- Logs können nicht geändert oder gelöscht werden (Append-Only)
- Niemals Passwörter oder Session-Tokens in Logs speichern
- Logs sollten regelmäßig archiviert werden (Post-MVP)

**Beispiel-Actions:**
- `login`, `logout`, `login_failed`
- `item_created`, `item_updated`, `item_withdrawn`
- `user_created`, `user_updated`, `user_deleted`
- `category_created`, `category_updated`, `category_deleted`
- `location_created`, `location_updated`
- `config_updated`

**Beziehungen:**
- N AuditLogs → 1 User (nullable)

---

## Haltbarkeitsberechnung (Business Logic)

Die Haltbarkeit wird zur Laufzeit berechnet, basierend auf `item_type`:

### 1. Gekauft (nicht gefroren) - `purchased_fresh`
```
expiry_date = best_before_date
```

### 2. Gekauft (bereits gefroren) - `purchased_frozen`
```
expiry_date = best_before_date
```

### 3. Gekauft und eingefroren - `purchased_then_frozen`
```
freeze_time = FreezeTimeConfig.get(category_id, 'purchased_then_frozen') oder Standardwert
expiry_date = freeze_date + freeze_time Monate
```

### 4. Selbst hergestellt (gefroren) - `homemade_frozen`
```
freeze_time = FreezeTimeConfig.get(category_id, 'homemade_frozen') oder Standardwert
expiry_date = production_date + freeze_time Monate
```

### 5. Selbst hergestellt (eingemacht) - `homemade_preserved`
```
shelf_life = FreezeTimeConfig.get(category_id, 'homemade_preserved') oder Standardwert
expiry_date = production_date + shelf_life Monate
```

### Expiry Status
```
days_until_expiry = expiry_date - today

if days_until_expiry < 3:
    status = 'critical' (rot)
elif days_until_expiry < 7:
    status = 'warning' (gelb)
else:
    status = 'ok' (grün/normal)
```

---

## Indizes & Performance

Empfohlene Indizes für bessere Performance:

### User
- `username` (unique)
- `email` (unique)

### Item
- `location_id` (FK)
- `created_by` (FK)
- `is_withdrawn` (für Filterung aktiver Artikel)
- Composite: `(is_withdrawn, location_id)` (häufige Kombination)

### Category
- `name` (unique)

### Location
- `name` (unique)
- `is_active`

### ItemCategory
- `item_id` (FK)
- `category_id` (FK)
- Composite unique: `(item_id, category_id)`

### FreezeTimeConfig
- Composite unique: `(category_id, item_type)`

### AuditLog
- `user_id` (FK)
- `timestamp` (für zeitbasierte Abfragen)
- `action` (für Filterung nach Aktionstyp)
- Composite: `(entity_type, entity_id)` (für Entity-spezifische Logs)

---

## Datenbankwahl (Empfehlung)

### MVP:
- **PostgreSQL** (empfohlen)
  - Robust, Open-Source
  - Gute JSON-Unterstützung (für AuditLog.details)
  - Enum-Typen
  - Self-hostbar

- **SQLite** (Alternative für sehr kleine Installationen)
  - Einfach zu deployen
  - Keine separate DB-Server nötig
  - Limitierungen bei Concurrent Writes

### Post-MVP:
- Bei Cloud/SaaS: PostgreSQL (managed)

---

## Migrations-Strategie

- Verwendung eines Schema-Migration-Tools (z.B. Alembic für Python, TypeORM für Node.js)
- Alle Schema-Änderungen via Migrations
- Rollback-Fähigkeit
- Seeding für Default-Daten (Standard-Kategorien, Lagerorte, Gefrierzeiten)

---

## Nächste Schritte

1. ER-Diagramm visualisieren
2. SQL-Schema generieren
3. ORM-Models implementieren
4. Sample-Data erstellen
5. Migrations aufsetzen
