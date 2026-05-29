# OSINT Industries CSV Data Importer

[OSINT Industries](https://app.osint.industries/) CSV Data Importer imports OSINT Industries
exports into SQLite databases. It supports both the legacy flat-CSV format and the current
ZIP-based export format, and accepts multiple files and directories in one call.

## Key Features

- **Dual-format support**: handles both the legacy `.csv` format and the new `.zip` format.
- **Per-type tables for ZIP exports**: each CSV inside the ZIP (`rich_data`, `timeline_events`,
  `geo_data`, `breached_data`, `checker_registered_data`) is stored in its own SQLite table,
  preserving every field without forcing incompatible schemas together.
- **Multi-input CLI**: accepts one or more `.csv`/`.zip` files and/or directories in one run.
- **Correct deduplication**: the uniqueness key is `(all data columns + entity)`, so the same
  module result found for two different query targets is kept as two distinct rows -- one per
  entity -- while re-importing the same file still produces zero duplicates.
- **Streaming CSV processing**: rows are processed one at a time; CSV files and ZIP entries are
  never fully loaded into memory.
- **Dynamic schema evolution**: tables are created on first use; new columns added by later
  imports are appended via `ALTER TABLE ADD COLUMN` without data loss.
- **Empty-file tolerance**: CSV files inside ZIPs that contain no data rows are silently skipped.
- **Automatic entity identification**: the queried target (email, phone, username...) is extracted
  from the export filename and stored in an `entity` column on every row.
- **Safe SQL identifiers**: column and table names with embedded double-quotes are escaped
  correctly.
- **UTF-8 / BOM support**: files with or without a UTF-8 BOM are handled transparently.
- **No external dependencies**: standard library only -- `csv`, `sqlite3`, `zipfile`.

## Installation

```bash
git clone https://github.com/N4rr34n6/OSINT-Industries-CSV-Data-Importer.git
cd OSINT-Industries-CSV-Data-Importer
```

## Prerequisites

- **Python 3.x**
- **SQLite3** (pre-installed on most operating systems)

## Usage

```text
python import_csv.py <path [path ...]> [--db DATABASE]
```

Each `path` can be:
- a `.csv` export file (legacy format)
- a `.zip` export file (current format)
- a directory -- all `.csv` and `.zip` files inside it are processed in sorted order

`--db` is optional and defaults to `output.db`.

### Import a single legacy CSV

```bash
python import_csv.py export_user@example.com.csv --db osint.db
```

```
[export_user@example.com.csv]
  Rows processed:     42
  Rows inserted:      40
  Duplicates skipped: 2
```

All rows land in the `data` table with an `entity` column set to `user@example.com`.

### Import a single ZIP export

```bash
python import_csv.py export_user_example_com.zip --db osint.db
```

```
[export_user_example_com.zip]
  [breached_data.csv] empty
  [checker_registered_data.csv] processed=4, inserted=4, skipped=0
  [geo_data.csv] empty
  [rich_data.csv] processed=31, inserted=31, skipped=0
  [timeline_events.csv] processed=5, inserted=5, skipped=0
  Total: processed=40, inserted=40, skipped=0
```

Each CSV inside the ZIP is stored in a separate SQLite table.
All rows carry an `entity` column derived from the ZIP filename.

### Import whole directories (all formats at once)

```bash
python import_csv.py folder1/new_format folder2/old_format --db osint.db
```

Files in each directory are processed in alphabetical order.
Deduplication works across all imports: re-running the same command
a second time inserts 0 rows.

### Mix files and directories

```bash
python import_csv.py folder1/new_format extra_export.zip dir/ --db osint.db
```

## Database schema

| Table | Source | Notable columns |
|---|---|---|
| `data` | Legacy `.csv` | dynamic (matches CSV headers) + `entity` |
| `rich_data` | `rich_data.csv` inside ZIP | `module`, profile fields... + `entity` |
| `timeline_events` | `timeline_events.csv` | `module`, `event_group`, `event_start`, `event_content` + `entity` |
| `geo_data` | `geo_data.csv` | dynamic + `entity` |
| `breached_data` | `breached_data.csv` | dynamic + `entity` |
| `checker_registered_data` | `checker_registered_data.csv` | `module`, `category_name`, `category_description` + `entity` |

## Technical details

- **Deduplication key**: `(all data columns, entity)`. Two entities that share the same raw
  module result each get their own row -- cross-entity relationships are never lost. Re-importing
  the same file is still idempotent.
- **Schema evolution**: when a later import introduces columns not present in the table, those
  columns are added with `ALTER TABLE ... ADD COLUMN`. Existing rows receive `NULL` for the new
  fields.
- **Row normalisation**: rows shorter than the header are right-padded with empty strings; rows
  longer than the header are trimmed.
- **SQL safety**: all table and column names are quoted with doubled internal double-quotes,
  following the SQLite identifier quoting rules.

## Legal Disclaimer

This software is designed to assist in data analysis for legitimate and ethical purposes, such as
open-source intelligence research and data process automation. Misuse of this tool may violate
local or international laws related to privacy and data protection. The author assumes no
responsibility for any inappropriate use of this software.

## License

This project is provided under the GNU Affero General Public License v3.0. You can find the full
license text in the [LICENSE](LICENSE) file.
