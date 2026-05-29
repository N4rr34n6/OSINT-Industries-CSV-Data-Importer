import argparse
import csv
import sqlite3
import os
import re
import sys
import zipfile
import io

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def extract_entity_name(filename):
    return re.sub(r'^export_|\.(?:csv|zip)$', '', filename)


def quote_id(name):
    """Return a safely double-quoted SQLite identifier."""
    return '"' + name.replace('"', '""') + '"'


def ensure_table(cursor, table_name, headers):
    """Create the table if it does not exist, then add any new columns."""
    qt = quote_id(table_name)
    col_defs = ', '.join(
        [quote_id(h) + ' TEXT' for h in headers] + ['"entity" TEXT']
    )
    cursor.execute(f'CREATE TABLE IF NOT EXISTS {qt} ({col_defs})')
    cursor.execute(f'PRAGMA table_info({qt})')
    existing = {row[1] for row in cursor.fetchall()}
    for h in headers:
        if h not in existing:
            cursor.execute(f'ALTER TABLE {qt} ADD COLUMN {quote_id(h)} TEXT')


def row_exists(cursor, table_name, row_values, headers, entity_name):
    """Return True if an identical (data columns + entity) row already exists.

    Including entity in the key means the same module result found for two
    different query targets is stored twice -- once per entity -- which is
    the correct OSINT behaviour.  Re-importing the same file still produces
    zero duplicates.
    """
    qt = quote_id(table_name)
    conditions = ' AND '.join(
        [f'{quote_id(h)} = ?' for h in headers] + ['"entity" = ?']
    )
    cursor.execute(
        f'SELECT COUNT(*) FROM {qt} WHERE {conditions}',
        list(row_values) + [entity_name],
    )
    return cursor.fetchone()[0] > 0


def process_csv_reader(cursor, table_name, reader, entity_name):
    """Stream rows from a csv.reader into table_name, skipping duplicates."""
    try:
        headers = next(reader)
    except StopIteration:
        return 0, 0

    if not headers:
        return 0, 0

    ensure_table(cursor, table_name, headers)

    qt = quote_id(table_name)
    col_names = ', '.join([quote_id(h) for h in headers] + ['"entity"'])
    placeholders = ', '.join(['?'] * (len(headers) + 1))
    insert_query = f'INSERT INTO {qt} ({col_names}) VALUES ({placeholders})'

    processed = inserted = 0
    for row in reader:
        processed += 1
        # Pad short rows; trim rows longer than the header
        row = (list(row) + [''] * len(headers))[:len(headers)]
        if not row_exists(cursor, table_name, row, headers, entity_name):
            cursor.execute(insert_query, row + [entity_name])
            inserted += 1

    return processed, inserted


# ---------------------------------------------------------------------------
# Per-format importers
# ---------------------------------------------------------------------------

def import_one_csv(file_path, db_path):
    """Import a legacy flat CSV into the 'data' table."""
    entity_name = extract_entity_name(os.path.basename(file_path))
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
            processed, inserted = process_csv_reader(
                cursor, 'data', csv.reader(f), entity_name
            )
        conn.commit()
    return {'data': (processed, inserted)}


def import_one_zip(file_path, db_path):
    """Import every CSV inside a ZIP into a dedicated per-type table."""
    entity_name = extract_entity_name(os.path.basename(file_path))
    stats = {}
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        with zipfile.ZipFile(file_path, 'r') as zf:
            for name in sorted(zf.namelist()):
                basename = os.path.basename(name)
                if not basename.lower().endswith('.csv'):
                    continue
                table_name = re.sub(r'\.csv$', '', basename, flags=re.IGNORECASE)
                with zf.open(name) as raw_f:
                    text_f = io.TextIOWrapper(
                        raw_f, encoding='utf-8-sig', newline=''
                    )
                    processed, inserted = process_csv_reader(
                        cursor, table_name, csv.reader(text_f), entity_name
                    )
                stats[basename] = (processed, inserted)
        conn.commit()
    return stats


# ---------------------------------------------------------------------------
# Input collection
# ---------------------------------------------------------------------------

def collect_input_files(paths):
    """Expand a mixed list of files and directories into a sorted file list."""
    result = []
    for path in paths:
        if os.path.isdir(path):
            for entry in sorted(os.listdir(path)):
                if entry.lower().endswith(('.csv', '.zip')):
                    result.append(os.path.join(path, entry))
        elif os.path.isfile(path):
            result.append(path)
        else:
            print(f"Warning: '{path}' not found -- skipping.", file=sys.stderr)
    return result


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_csv_stats(file_path, stats):
    processed, inserted = stats['data']
    print(f"[{file_path}]")
    print(f"  Rows processed:     {processed}")
    print(f"  Rows inserted:      {inserted}")
    print(f"  Duplicates skipped: {processed - inserted}")


def print_zip_stats(file_path, stats):
    print(f"[{file_path}]")
    total_p = total_i = 0
    for csv_name, (processed, inserted) in stats.items():
        status = (
            'empty'
            if processed == 0
            else f'processed={processed}, inserted={inserted}, skipped={processed - inserted}'
        )
        print(f"  [{csv_name}] {status}")
        total_p += processed
        total_i += inserted
    print(
        f"  Total: processed={total_p}, inserted={total_i},"
        f" skipped={total_p - total_i}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Import OSINT Industries exports (.csv or .zip) into SQLite.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'examples:\n'
            '  python import_csv.py export.zip\n'
            '  python import_csv.py examples/folder1 examples/folder2 --db osint.db\n'
            '  python import_csv.py file1.csv file2.zip exports_folder/ --db osint.db'
        ),
    )
    parser.add_argument(
        'files',
        nargs='+',
        metavar='path',
        help='.csv/.zip export file(s), or directory/ies containing them',
    )
    parser.add_argument(
        '--db',
        default='output.db',
        help='SQLite database path (default: output.db)',
    )
    args = parser.parse_args()

    input_files = collect_input_files(args.files)
    if not input_files:
        print('No .csv or .zip files found.', file=sys.stderr)
        sys.exit(1)

    had_errors = False
    for file_path in input_files:
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.csv':
                print_csv_stats(file_path, import_one_csv(file_path, args.db))
            elif ext == '.zip':
                print_zip_stats(file_path, import_one_zip(file_path, args.db))
            else:
                print(
                    f"Warning: skipping '{file_path}' (unsupported type '{ext}').",
                    file=sys.stderr,
                )
        except Exception as exc:
            print(f"Error importing '{file_path}': {exc}", file=sys.stderr)
            had_errors = True

    if had_errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
